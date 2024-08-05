import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketState

from agent_api.messages import UserMessage
from AgentMint import AgentMint

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "mintAgent"


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
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return FileResponse("./utils/chat.html")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        agent = AgentMint()
        agent.visualize_graph()
        while True:
            incoming_message = await websocket.receive_json()
            user_input = UserMessage(incoming_message)
            type = user_input.to_json()["type"]
            match type:
                case "input":
                    await manager.send_message(user_input.content, websocket)
                case "tool_confirm":
                    await manager.send_message("tool_confirm", websocket)
                case "tool_reject":
                    await manager.send_message("tool_reject", websocket)
            async for message in call_agent(agent, user_input):
                await manager.send_message(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@app.websocket("/ws/test/{client_id}")
async def websocket_test_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        agent = AgentMint()
        while True:
            incoming_message = await websocket.receive_json()
            user_input = UserMessage(incoming_message)
            async for message in mock_call_agent(agent, user_input):
                await manager.send_message(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
