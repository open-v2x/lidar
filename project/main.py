import asyncio
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from redis_connect import redis_conn

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: list, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return {'test': 'test'}


@app.websocket("/ws/{ip}")
async def websocket_endpoint(websocket: WebSocket, ip: str):
    await manager.connect(websocket)
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
            await manager.send_personal_message(json.loads(data), websocket)
            redis_conn.delete(key)
            await asyncio.sleep(0.0001)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
