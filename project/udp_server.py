import asyncio
import multiprocessing
import socket
from multiprocessing import Process, Queue
from typing import Dict

from redis_connect import redis_conn

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
    if data == b"clear":
        data_dict[ip].clear()
        return
    if ip not in data_dict:
        data_dict[ip] = list()
    data_dict[ip].append(data)
    if len(data_dict[ip]) == 180:
        if redis_conn.llen(ip) + 1 > 500:
            redis_conn.rpop(ip)
        data = b"".join(data_dict[ip])
        redis_conn.lpush(ip, data)
        data_dict[ip].clear()


def deal_handle(queue):
    while True:
        try:
            addr, data = queue.get()
            if data:
                deal_parse(addr, data)
        except Exception as e:
            print("deal error", e, flush=True)


async def read_data(sock, queue):
    while True:
        try:
            data, addr = sock.recvfrom(1024 * 10)  # 返回数据和接入连接的（服务端）地址
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
