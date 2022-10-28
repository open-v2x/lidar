import asyncio
import json
from typing import Dict

from fastapi import FastAPI, WebSocket
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
    while True:
        try:
            key = redis_conn.rpop(ip)
            if not key:
                await asyncio.sleep(0.0001)
                continue
            data = redis_conn.get(key)
            while True:
                if data:
                    break
                data = redis_conn.get(key)
                await asyncio.sleep(0.0001)
            redis_conn.delete(key)
            await manager.broadcast(json.loads(data), ip)
            await asyncio.sleep(0.0001)
        except (ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect):
            manager.disconnect(websocket, ip)
            return
