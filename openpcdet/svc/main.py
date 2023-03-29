import asyncio
from typing import Tuple

import numpy as np
import uvicorn
from config import cfgs
from fastapi import FastAPI, WebSocket
from inference import Inference
from mqtt_server import connect, get_mqtt_client
from udp_dataset import DataParse
from ws_connection import ConnectionManager

app = FastAPI()
manager = ConnectionManager()
data_parse = DataParse()


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
    points = points[..., :3]
    points = points * (-1000)
    points = points.astype(int)
    points[:, 1] = points[:, 1] * (-1)
    points = np.delete(points, np.where(abs(points[:, 2]) >= 1700), axis=0)
    points = points.flatten().tolist()
    await manager.broadcast(points, addr[0])


class UDPProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        pcd = data_parse.parse(addr, data)
        if pcd:
            points = np.frombuffer(pcd).reshape(-1, 4)
            points = np.delete(points, np.where(points[:, 2] <= -1.7), axis=0)

            asyncio.create_task(send_points(points, addr))
            asyncio.create_task(main(points))


@app.on_event("startup")
async def on_startup() -> None:
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPProtocol(), local_addr=(cfgs.udp.get("host"), cfgs.udp.get("port"))
    )
    app.state.udp_transport = transport
    app.state.udp_protocol = protocol


async def main(points):
    result = await Inference().run(points=points)
    # send result to mqtt
    mqtt_client = get_mqtt_client()
    mqtt_client.publish(cfgs.mqtt.get("topic"), result)


if __name__ == "__main__":
    uvicorn.run(app=app, host=cfgs.websocket.get("host"), port=28300)
