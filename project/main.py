from typing import Dict

import numpy as np
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
@repeat_every(seconds=0.1)
async def send():
    try:
        for ip in manager.active_connections.keys():
            data = redis_conn.rpop(ip)
            if not data:
                continue
            points = np.frombuffer(data).reshape(-1, 4)
            points = points[..., :3]
            points = points * (-1000)
            points = points.astype(int)
            points[:, 1] = points[:, 1] * (-1)
            points = np.delete(points, np.where(abs(points[:, 2]) >= 1700), axis=0)
            result = points.flatten().tolist()

            await manager.broadcast(result, ip)
    except Exception as e:
        print(e)
