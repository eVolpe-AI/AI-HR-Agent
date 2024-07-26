import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.websockets import WebSocketState

from agent_api.messages import UserMessage, UserMessageType
from AgentMint import AgentMint

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "mintAgent"


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket mintHCM chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/test/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                var message = {
                    type: "input",
                    text: input.value
                }
                ws.send(JSON.stringify(message))
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


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
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        agent = AgentMint()
        while True:
            incoming_message = await websocket.receive_json()
            user_input = UserMessage(incoming_message)
            await manager.send_message(user_input.text, websocket)
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
