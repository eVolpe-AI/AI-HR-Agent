import pickle
from contextlib import AbstractContextManager
from datetime import datetime, timedelta
from types import TracebackType
from typing import AsyncIterator, Optional, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
)
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from typing_extensions import Self


class JsonPlusSerializerCompat(JsonPlusSerializer):
    def loads(self, data: bytes) -> any:
        if data.startswith(b"\x80") and data.endswith(b"."):
            return pickle.loads(data)
        return super().loads(data)


class MongoDBBase:
    client: AsyncIOMotorClient
    db_name: str
    collection_name: str

    def __init__(
        self,
        client: AsyncIOMotorClient,
        db_name: str,
        collection_name: str,
    ) -> None:
        self.client = client
        self.db_name = db_name
        self.collection_name = collection_name
        self.collection = client[db_name][collection_name]


class MongoDBCheckpointSaver(BaseCheckpointSaver, AbstractContextManager, MongoDBBase):
    serde = JsonPlusSerializerCompat()

    client: AsyncIOMotorClient
    db_name: str
    collection_name: str

    def __init__(
        self,
        client: AsyncIOMotorClient,
        db_name: str,
        collection_name: str,
        *,
        serde: Optional[SerializerProtocol] = None,
    ) -> None:
        super().__init__(serde=serde)
        MongoDBBase.__init__(self, client, db_name, collection_name)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        __exc_type: Optional[type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        return True

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        user_id = config["configurable"]["user_id"]
        chat_id = config["configurable"]["chat_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        base_query = {"_id": user_id, "chats.chat_id": chat_id}

        if checkpoint_id:
            base_query["chats.checkpoints.checkpoint_id"] = checkpoint_id

        projection = {"chats": {"$elemMatch": {"chat_id": chat_id}}}

        try:
            result = await self.collection.find_one(base_query, projection)

            if not result or not result.get("chats"):
                return None

            chat = result["chats"][0]

            if not checkpoint_id:
                last_checkpoint = (
                    chat["checkpoints"][-1] if chat.get("checkpoints") else None
                )
            else:
                last_checkpoint = next(
                    (
                        cp
                        for cp in chat["checkpoints"]
                        if cp["checkpoint_id"] == checkpoint_id
                    ),
                    None,
                )

            if not last_checkpoint:
                return None

            return CheckpointTuple(
                {
                    "configurable": {
                        "chat_id": chat_id,
                        "checkpoint_id": last_checkpoint["checkpoint_id"],
                        "user_id": user_id,
                    }
                },
                self.serde.loads(last_checkpoint["checkpoint"]),
                self.serde.loads(last_checkpoint["metadata"]),
                (
                    {
                        "configurable": {
                            "chat_id": chat_id,
                            "checkpoint_id": last_checkpoint["parent_checkpoint_id"],
                        }
                    }
                    if last_checkpoint.get("parent_checkpoint_id")
                    else None
                ),
            )
        except Exception as e:
            logger.error(f"Error in aget_tuple function: {e}")

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filters: Optional[dict[str, any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        query = {}
        if config is not None:
            query["_id"] = config["configurable"]["user_id"]
            query["chats.chat_id"] = config["configurable"]["chat_id"]

        if filters:
            for key, value in filters.items():
                query[f"chats.checkpoints.metadata.{key}"] = value

        if before is not None:
            query["chats.checkpoints.checkpoint_id"] = {
                "$lt": before["configurable"]["checkpoint_id"]
            }

        pipeline = [
            {"$match": query},
            {"$unwind": "$chats"},
            {"$unwind": "$chats.checkpoints"},
            {"$match": query},
            {"$sort": {"chats.checkpoints.checkpoint_id": -1}},
        ]

        if limit is not None:
            pipeline.append({"$limit": limit})

        try:
            async for doc in self.collection.aggregate(pipeline):
                checkpoint = doc["chats"]["checkpoints"]

                parent_config = None
                if "parent_checkpoint_id" in checkpoint:
                    parent_config = {
                        "configurable": {
                            "chat_id": doc["chats"]["chat_id"],
                            "checkpoint_id": checkpoint["parent_checkpoint_id"],
                        }
                    }

                yield CheckpointTuple(
                    {
                        "configurable": {
                            "chat_id": doc["chats"]["chat_id"],
                            "checkpoint_id": checkpoint["checkpoint_id"],
                        }
                    },
                    self.serde.loads(checkpoint["checkpoint"]),
                    self.serde.loads(checkpoint["metadata"]),
                    parent_config,
                )
        except Exception as e:
            logger.error(f"Error in alist function: {e}")

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        user_id = config["configurable"]["user_id"]
        chat_id = config["configurable"]["chat_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        checkpoint_data = {
            "checkpoint_id": checkpoint["id"],
            "checkpoint": self.serde.dumps(checkpoint),
            "metadata": self.serde.dumps(metadata),
        }

        if checkpoint_id:
            checkpoint_data["parent_checkpoint_id"] = checkpoint_id

        try:
            if checkpoint_id:
                while True:
                    parent_check = await self.collection.find_one(
                        {
                            "_id": user_id,
                            "chats.chat_id": chat_id,
                            "chats.checkpoints.checkpoint_id": checkpoint_id,
                        },
                        projection={"_id": 1},
                    )
                    if parent_check:
                        break

            result = await self.collection.update_one(
                {"_id": user_id, "chats.chat_id": chat_id},
                {"$push": {"chats.$.checkpoints": checkpoint_data}},
                upsert=False,
            )

            if result.matched_count == 0:
                await self.collection.update_one(
                    {"_id": user_id},
                    {
                        "$addToSet": {
                            "chats": {
                                "chat_id": chat_id,
                                "checkpoints": [checkpoint_data],
                            }
                        }
                    },
                    upsert=True,
                )

            return {
                "configurable": {
                    "chat_id": chat_id,
                    "checkpoint_id": checkpoint["id"],
                    "user_id": user_id,
                }
            }
        except Exception as e:
            logger.error(f"Error in aput function: {e}")

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, any]],
        task_id: str,
    ) -> None:
        pass
        # TODO: Implement this function if needed, langgraph documentation is not clear on what this function should exactly do
        # user_id = config["configurable"]["user_id"]
        # chat_id = config["configurable"]["chat_id"]
        # checkpoint_id = config["configurable"]["checkpoint_id"]

        # try:
        #     await self.collection.update_one(
        #         {
        #             "_id": user_id,
        #             "chats.chat_id": chat_id,
        #             "chats.checkpoints.checkpoint_id": checkpoint_id,
        #         },
        #         {
        #             "$push": {
        #                 "chats.$.checkpoints.$[checkpoint].writes": [
        #                     {
        #                         "task_id": task_id,
        #                         "idx": idx,
        #                         "channel": channel,
        #                         "value": self.serde.dumps(value),
        #                     }
        #                     for idx, (channel, value) in enumerate(writes)
        #                 ]
        #             }
        #         },
        #         array_filters=[{"checkpoint.checkpoint_id": checkpoint_id}],
        #     )
        # except Exception as e:
        #     logger.error(f"Error in aput_writes function: {e}")


class MongoDBUsageTracker(MongoDBBase):
    def __init__(
        self,
        client: AsyncIOMotorClient,
        db_name: str,
        collection_name: str,
    ) -> None:
        super().__init__(client, db_name, collection_name)

    async def push_token_usage(self, usage_data: dict) -> None:
        try:
            await self.collection.update_one(
                {"_id": self.collection_name},
                {"$push": {"tokens": usage_data}},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Error while pushing token usage: {e}")

    async def get_token_usage(self, user_id: str, hours: int) -> int:
        time_period = datetime.now() - timedelta(hours=hours)

        pipeline = [
            {"$match": {"_id": user_id}},
            {"$unwind": "$tokens"},
            {"$match": {"tokens.time": {"$gte": time_period}}},
            {
                "$group": {
                    "_id": None,
                    "total_input_tokens": {"$sum": "$tokens.tokens.input_tokens"},
                    "total_output_tokens": {"$sum": "$tokens.tokens.output_tokens"},
                    "total_tokens": {"$sum": "$tokens.tokens.total_tokens"},
                }
            },
        ]

        try:
            result = await self.collection.aggregate(pipeline).to_list(1)

            if result:
                doc = result[0]
                return {
                    "total_input_tokens": doc.get("total_input_tokens", 0),
                    "total_output_tokens": doc.get("total_output_tokens", 0),
                    "total_tokens": doc.get("total_tokens", 0),
                }
            else:
                return {
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens": 0,
                }
        except Exception as e:
            logger.error(f"Error while getting token usage: {e}")


class AgentDatabase(MongoDBBase):
    def __init__(
        self,
        client: AsyncIOMotorClient,
        db_name: str,
        collection_name: str,
    ) -> None:
        super().__init__(client, db_name, collection_name)

    async def get(self, field_names: list) -> dict:
        try:
            projection = {field: 1 for field in field_names}
            return await self.collection.find_one({}, projection=projection)
        except Exception as e:
            logger.error(f"Error while getting data from database: {e}")
