import asyncio
import socket
from typing import Tuple

import numpy as np
import uvicorn
from config import cfgs
from fastapi import FastAPI, WebSocket
from inference import Inference
from mqtt_server import connect, get_mqtt_client
from starlette.websockets import WebSocketDisconnect
from udp_dataset import DataParse
from ws_connection import ConnectionManager

app = FastAPI()
manager = ConnectionManager()
data_parse = DataParse()
inference = Inference()


@app.on_event("startup")
def setup_mqtt() -> None:
    connect()


@app.websocket("/ws/{ip}")
async def websocket_endpoint(websocket: WebSocket, ip: str):
    await manager.connect(websocket, ip)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, ip)


async def send_points(points, addr):
    points = (points[..., :3] * (-1000)).astype(int)
    points[:, 1] = points[:, 1] * (-1)
    await manager.broadcast(points.flatten().tolist(), addr[0])


class UDPProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        asyncio.create_task(self.process_pcd(data, addr))

    async def process_pcd(self, data: bytes, addr: Tuple[str, int]) -> None:
        pcd = data_parse.parse(addr, data)
        if pcd:
            points = np.frombuffer(pcd).reshape(-1, 4)
            points = points[points[:, 2] > -1.7]
            await asyncio.gather(send_points(points, addr), main(points))


@app.on_event("startup")
async def on_startup() -> None:
    transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: UDPProtocol(),
        local_addr=(cfgs.udp.get("host"), cfgs.udp.get("port")),
        family=socket.AF_INET,
    )
    app.state.udp_transport = transport
    app.state.udp_protocol = protocol


async def main(points):
    result = await inference.run(points=points)
    # send result to mqtt
    mqtt_client = get_mqtt_client()
    mqtt_client.publish(cfgs.mqtt.get("topic"), result)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=28300)
