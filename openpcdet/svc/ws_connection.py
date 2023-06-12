import gzip
from typing import Dict

import ujson
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


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
            if not self.active_connections[ip]:
                self.active_connections.pop(ip)

    async def send_personal_message(self, message: list, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message, ip: str):
        data = ujson.dumps(message, separators=(",", ":"))
        data = gzip.compress(data.encode(), compresslevel=1)
        for connection in self.active_connections.get(ip, []):
            try:
                await connection.send_text(data)
            except (ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect):
                self.disconnect(connection, ip)
