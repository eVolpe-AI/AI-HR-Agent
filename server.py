from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketState
from loguru import logger

from agent_api.messages import UserMessage
from AgentMint import AgentMint
from utils.logging import configure_logging

configure_logging()

# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
# os.environ["LANGCHAIN_PROJECT"] = "tokenTest"


app = FastAPI()


async def call_agent(agent: AgentMint, message: str):
    async for message in agent.invoke(message):
        yield message


async def mock_call_agent(agent: AgentMint, message: str):
    async for message in agent.mock_invoke(message):
        yield message


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.debug(f"Connected with {websocket.client}")
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


@app.get("/")
async def get():
    return FileResponse("./utils/chat.html")


@app.websocket("/ws/{user_id}/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, chat_id: int):
    await manager.connect(websocket)
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
                    await manager.send_message(user_input.content, websocket)
                case "tool_confirm":
                    logger.debug(
                        f"Received tool confirmation from {websocket.client}, user_id: {user_id}, chat_id: {chat_id}"
                    )
                    await manager.send_message("tool_confirm", websocket)
                case "tool_reject":
                    logger.debug(
                        f"Received tool rejection: {user_input.content}' from {websocket.client}, user_id: {user_id}, chat_id: {chat_id}"
                    )
                    await manager.send_message("tool_reject", websocket)
                case _:
                    logger.error(
                        f"Invalid message type received: {message_type} from {websocket.client}, user_id: {user_id}, chat_id: {chat_id}"
                    )

            async for message in call_agent(agent, user_input):
                await manager.send_message(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(
            f"Error in connection with {websocket.client}, user_id: {user_id}, chat_id: {chat_id}: {e}"
        )
        raise


@app.websocket("/ws/test/{chat_id}/")
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
