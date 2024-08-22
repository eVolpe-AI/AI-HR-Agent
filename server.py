import multiprocessing
import os
import traceback

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketState
from loguru import logger

from agent_api.CredentialManager import CredentialManager
from agent_api.messages import AgentMessage, AgentMessageType, UserMessage
from AgentMint import AgentMint
from utils.AgentLogger import configure_logging
from utils.errors import ServerError

configure_logging()

# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
# os.environ["LANGCHAIN_PROJECT"] = "tokenTest"


app_http = FastAPI()
app_ws = FastAPI()
app_ws2 = FastAPI()
credential_manager = CredentialManager()


async def call_agent(agent: AgentMint, message: str):
    async for message in agent.invoke(message):
        yield message


async def mock_call_agent(agent: AgentMint, message: str):
    async for message in agent.mock_invoke(message):
        yield message


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: str, token: str):
        if not credential_manager.authenticate_user(user_id, token):
            logger.warning(f"Failed to authenticate {websocket.client}")
            await websocket.accept()
            await websocket.send_json(
                AgentMessage(
                    type=AgentMessageType.ERROR, content="Authentication failed"
                ).to_json()
            )
            await websocket.close()
            return False
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.debug(f"Connected with {websocket.client}")
            return True
        except Exception as e:
            logger.error(f"Connection failed with {websocket.client} due to {e}")
            raise

    async def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logger.debug(f"Connection closed with: {websocket.client}")
        except ValueError as e:
            logger.warning(
                f"Attempted to disconnect with {websocket.client} that was not connected: {e}"
            )

    async def send_message(self, message: str, websocket: WebSocket):
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {websocket.client}: {e}")
                raise


manager = ConnectionManager()


@app_http.get("/")
async def get():
    return FileResponse("./utils/chat.html")


@app_ws.websocket("/{user_id}/{chat_id}/{token}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: str, chat_id: int, token: str
):
    connected = await manager.connect(websocket, user_id, token)
    if not connected:
        return
    try:
        agent = AgentMint(
            user_id=user_id, chat_id=chat_id, ip_addr=websocket.client.host
        )
        while True:
            incoming_message = await websocket.receive_json()
            user_input = UserMessage(incoming_message)
            message_type = user_input.to_json()["type"]
            match message_type:
                case "input":
                    logger.debug(
                        f"Received input message: '{user_input.content}' from {websocket.client}, user_id: {user_id}, chat_id: {chat_id}"
                    )
                case "tool_confirm":
                    logger.debug(
                        f"Received tool confirmation from {websocket.client}, user_id: {user_id}, chat_id: {chat_id}"
                    )
                case "tool_reject":
                    logger.debug(
                        f"Received tool rejection: {user_input.content}' from {websocket.client}, user_id: {user_id}, chat_id: {chat_id}"
                    )
                case _:
                    raise ServerError(f"Invalid message type received: {message_type}")

            async for message in call_agent(agent, user_input):
                await manager.send_message(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except ServerError as e:
        logger.error(f"Server error: {websocket.client} {traceback.format_exc()}")
        message = AgentMessage(type=AgentMessageType.ERROR, content=e.message).to_json()
        await manager.send_message(message, websocket)
        await manager.disconnect(websocket)
        raise
    except Exception:
        message = AgentMessage(
            type=AgentMessageType.ERROR, content="Internal error occurred"
        ).to_json()
        await manager.send_message(message, websocket)
        await manager.disconnect(websocket)
        raise


@app_ws2.websocket("/ws/test/{chat_id}/")
async def websocket_test_endpoint(websocket: WebSocket, chat_id: int):
    await manager.connect(websocket)
    try:
        agent = AgentMint(
            user_id="admin", chat_id=chat_id, ip_addr=websocket.client.host
        )
        while True:
            incoming_message = await websocket.receive_json()
            user_input = UserMessage(incoming_message)
            async for message in mock_call_agent(agent, user_input):
                await manager.send_message(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
