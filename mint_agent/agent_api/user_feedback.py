import os
from typing import Literal

from dotenv import load_dotenv
from langfuse import Langfuse
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from mint_agent.database.db_utils import AgentDatabase

load_dotenv()


class Feedback(BaseModel):
    user: str
    run_id: str
    type: str = Literal["positive", "negative"]
    comment: str = None


def send_feedback_to_langfuse(feedback: Feedback):
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    try:
        langfuse.score(
            data_type="CATEGORICAL",
            trace_id=feedback.run_id,
            name="user_feedback",
            value="positive" if feedback.type == "positive" else "negative",
            comment=feedback.comment,
        )
    except Exception as e:
        logger.error(f"Error while sending feedback to langfuse: {e}")


def save_feedback(feedback: Feedback):
    try:
        send_feedback_to_langfuse(feedback)

        agent_db = AgentDatabase(
            AsyncIOMotorClient(os.getenv("MONGO_URI")),
            os.getenv("MONGO_DB_NAME"),
            feedback.user,
        )
        agent_db.save_user_feedback(feedback)
    except Exception as e:
        logger.error(f"Error while saving feedback: {e}")
