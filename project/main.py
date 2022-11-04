import json
import time
from typing import Dict

from fastapi import FastAPI, WebSocket
from fastapi_utils.tasks import repeat_every
from redis_connect import redis_conn
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, list] = {}

    async def connect(self, websocket: WebSocket, ip: str):
        await websocket.accept()
        if ip not in self.active_connections:
            self.active_connections[ip] = []

        self.active_connections[ip].append(websocket)

    def disconnect(self, websocket: WebSocket, ip: str):
        if ip in self.active_connections:
            if websocket in self.active_connections[ip]:
                self.active_connections[ip].remove(websocket)

    async def send_personal_message(self, message: list, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message, ip: str):
        for connection in self.active_connections[ip]:
            try:
                await connection.send_json(message)
            except (ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect):
                self.disconnect(connection, ip)


manager = ConnectionManager()


@app.get("/")
async def get():
    return {"test": "test"}


@app.websocket("/ws/{ip}")
async def websocket_endpoint(websocket: WebSocket, ip: str):
    await manager.connect(websocket, ip)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, ip)


@app.on_event("startup")
@repeat_every(seconds=0.01)
async def send():
    try:
        for ip in manager.active_connections.keys():
            key = redis_conn.rpop(ip)
            if not key:
                continue
            data = redis_conn.get(key)
            t = time.time()
            while True:
                if data or (time.time() - t) > 10:
                    break
                data = redis_conn.get(key)
            if not data:
                continue
            redis_conn.delete(key)
            await manager.broadcast(json.loads(data), ip)
    except Exception as e:
        print(e)
