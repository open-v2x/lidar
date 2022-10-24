#!/usr/bin/env python

import asyncio
import json
import time

import websockets


async def hello():
    async with websockets.connect("ws://47.100.126.13:8000/ws/127.0.0.1", max_size=None) as websocket:
        await websocket.send("Hello world!")
        while True:
            data = await websocket.recv()
            data = json.loads(data)
            print(data[:10])
            print(time.time())



asyncio.run(hello())
