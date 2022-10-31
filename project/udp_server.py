import asyncio
import multiprocessing
import socket
import time
from multiprocessing import Process, Queue
from typing import Dict

from redis_connect import redis_conn
from worker import parses

queue: multiprocessing.Queue = Queue()
data_dict: Dict[str, list] = {}


class MyUDP:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

    def __enter__(self):
        return self.sock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()


def deal_parse(addr, data):
    ip = addr[0]
    if ip not in data_dict:
        data_dict[ip] = []
    if data == b"1111":
        data_dict[ip] = []
        redis_conn.delete(ip)
        return
    data_dict[ip].append(data.hex())
    if len(data_dict[ip]) == 180:
        data_list = data_dict.get(ip)
        key = time.time()
        if redis_conn.llen(ip) + 1 > 500:
            print("超过队列", flush=True)
            redis_conn.rpop(ip)
        redis_conn.lpush(ip, key)
        parses.apply_async((data_list, key))
        data_dict[ip] = []


def deal_handle(queue):
    while True:
        try:
            addr, data = queue.get()
            if not data:
                continue
            deal_parse(addr, data)
        except Exception as e:
            print("deal error", e, flush=True)


async def read_data(sock, queue):
    while True:
        try:
            data, addr = sock.recvfrom(1024 * 5)  # 返回数据和接入连接的（服务端）地址
            queue.put((addr, data))
        except Exception as e:
            print("read data error", e, flush=True)


def udp_connect(host, port, queue):
    with MyUDP(host, port) as sock:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [
            asyncio.ensure_future(read_data(sock=sock, queue=queue), loop=loop),
        ]
        loop.run_until_complete(asyncio.wait(tasks))
        try:
            loop.run_forever()
        except Exception as e:
            print(e, flush=True)
        finally:
            loop.close()


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 57142
    udp_process = Process(target=udp_connect, args=(host, port, queue))
    deal_process = Process(target=deal_handle, args=(queue,))
    udp_process.start()
    deal_process.start()
    udp_process.join()
    deal_process.join()
