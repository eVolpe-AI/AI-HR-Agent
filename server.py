import os
import traceback
from typing import AsyncGenerator

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
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
# os.environ["LANGCHAIN_PROJECT"] = "new-llm-interaction"

app_http = FastAPI()
app_ws = FastAPI()
credential_manager = CredentialManager()


async def call_agent(
    agent: AgentMint, message: str
) -> AsyncGenerator[AgentMessage, None]:
    """
    Calls the agent with the given message and yields the response

    Args:
        agent: AgentMint object
        message: UserMessage object

    Yields:
        AgentMessage object
    """
    async for message in agent.invoke(message):
        yield message


class ConnectionManager:
    """
    Manages active connections with the agent.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: str, token: str) -> bool:
        """
        Authenticates the user and establishes a connection with the agent.

        Args:
            websocket: WebSocket object
            user_id: str
            token: str

        Returns:
            bool: True if the connection is established, False otherwise
        """
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
            return False

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnects the user from the agent API.
        """
        try:
            self.active_connections.remove(websocket)
            logger.debug(f"Connection closed with: {websocket.client}")
        except ValueError as e:
            logger.warning(
                f"Attempted to disconnect with {websocket.client} that was not connected: {e}"
            )

    async def send_message(self, message: str, websocket: WebSocket) -> None:
        """
        Sends a message to the connected socket.
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {websocket.client}: {e}")
                raise


manager = ConnectionManager()


@app_http.get("/")
async def get():
    """
    Server endpoint for the test chat page.
    """
    return FileResponse("./utils/chat.html")


@app_ws.websocket("/{user_id}/{chat_id}/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    chat_id: str,
    token: str,
    advanced: bool = Query(False),
):
    """
    Server endpoint for the WebSocket connection.

    Args:
        websocket: WebSocket object
        user_id: str
        chat_id: str
        token: str
        advanced: bool

    Raises:
        ServerError: If an error occurs during the conversation
    """
    connected = await manager.connect(websocket, user_id, token)
    if not connected:
        return
    try:
        agent = AgentMint(
            user_id=user_id,
            chat_id=chat_id,
            ip_addr=websocket.client.host,
            is_advanced=advanced,
        )
        agent.visualize_graph()
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
