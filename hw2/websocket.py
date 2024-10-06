from dataclasses import dataclass, field
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)


@dataclass(slots=True)
class ConnectionManager:
    active_connections: list[WebSocket] = field(init=False, default_factory=list)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(message)


chat_room_managers = {}


@app.websocket("/chat/{room_name}")
async def chat_websocket_endpoint(websocket: WebSocket, room_name: str):
    client_id = uuid4()
    if room_name not in chat_room_managers:
        chat_room_managers[room_name] = ConnectionManager()

    chat_manager = chat_room_managers[room_name]
    await chat_manager.connect(websocket)
    await chat_manager.broadcast(f"Client {client_id} has joined the room.")

    try:
        while True:
            message = await websocket.receive_text()
            await chat_manager.broadcast(f"Client {client_id}: {message}")
    except WebSocketDisconnect:
        await chat_manager.disconnect(websocket)
        await chat_manager.broadcast(f"Client {client_id} has left the room.")
