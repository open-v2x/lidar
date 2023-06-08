import asyncio
import socket
from multiprocessing import Process, Queue
from typing import Tuple

import numpy as np
import uvicorn
from config import cfgs
from fastapi import FastAPI, WebSocket
from fastapi_utils.tasks import repeat_every
from inference import Inference
from mqtt_server import connect, get_mqtt_client
from starlette.websockets import WebSocketDisconnect
from udp_dataset import DataParse
from ws_connection import ConnectionManager

app = FastAPI()
manager = ConnectionManager()
data_parse = DataParse()

queue = Queue(maxsize=100)


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
    if not manager.active_connections.get(addr[0]):
        return
    points = points[points[:, 2] < -1]
    points = (points[..., :3] * -10).astype(int)
    points[:, 1] *= -1
    sq = np.sum(points[:, :2] ** 2, axis=1)
    points = points[sq <= 25000000] * 100
    await manager.broadcast(points.flatten().tolist(), addr[0])


class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue
        self.data_parse = DataParse()

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        pcd = self.data_parse.parse(addr, data)
        if pcd:
            if self.queue.full():
                self.queue.get()
            self.queue.put((pcd, addr))


@app.on_event("startup")
@repeat_every(seconds=0.1)
async def process_pcd():
    if app.state.queue.empty():
        return
    data, addr = app.state.queue.get()
    points = np.frombuffer(data).reshape(-1, 4)
    points = points[points[:, 2] > -1.7]
    await asyncio.gather(send_points(points, addr), main(points))


async def udp_server(queue):
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPProtocol(queue),
        local_addr=("0.0.0.0", cfgs.udp.get("port")),
        family=socket.AF_INET,
    )


async def main(points):
    t = time.time()
    result = await app.state.inference.run(points=points)
    # send result to mqtt
    if result:
        mqtt_client = get_mqtt_client()
        mqtt_client.publish(cfgs.mqtt.get("topic"), result)
    print(time.time() - t)


def start_udp_server(queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(udp_server(queue))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        queue.close()


def run_app(queue):
    app.state.queue = queue
    app.state.inference = Inference()
    uvicorn.run(app, host="0.0.0.0", port=28300)


if __name__ == "__main__":
    udp_process = Process(target=start_udp_server, args=(queue,))
    udp_process.start()

    app_process = Process(target=run_app, args=(queue,))
    app_process.start()

    try:
        udp_process.join()
        app_process.join()
    except KeyboardInterrupt:
        queue.close()
