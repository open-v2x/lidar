#!/usr/bin/env python

import asyncio
import json
import time

import websockets


async def hello():
    async with websockets.connect("ws://150.158.47.136:8000/ws/127.0.0.1", max_size=None) as websocket:
    # async with websockets.connect("ws://127.0.0.1:8000/ws/127.0.0.1") as websocket:
        await websocket.send("Hello world!")
        while True:
            data = await websocket.recv()
            data = json.loads(data)
            # print(data[:10])
            # with open('test', 'w')as f:
            #     f.write(data)
            print(time.time())

            # await websocket.send("Hello world!")


asyncio.run(hello())
