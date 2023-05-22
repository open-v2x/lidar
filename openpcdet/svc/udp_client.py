import asyncio
import glob
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import cfgs


class UDPClientProtocol:
    def __init__(self, on_con_lost):
        self.on_con_lost = on_con_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        packet_number, packet_lens, dir_path, sleep_time = (
            cfgs.udp.get("packet_number"),
            cfgs.udp.get("packet_lens"),
            cfgs.udp.get("dir_path"),
            cfgs.udp.get("sleep_time"),
        )
        file_extension = "*.bin"  # 指定文件的后缀名
        file_list = glob.glob(os.path.join(dir_path, file_extension))
        file_list.sort(key=lambda x: int(os.path.basename(x).split(".")[0]))
        while True:
            self.transport.sendto(b"end")
            for filename in file_list:
                with open(filename, "rb") as f:
                    for _ in range(packet_number):
                        data = f.read(packet_lens)
                        self.transport.sendto(data)
                        time.sleep(1e-4)
                self.transport.sendto(b"end")
                time.sleep(sleep_time)

    def datagram_received(self, data, addr):
        print("Received:", data.decode())

        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print("Error received:", exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)


async def main():
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPClientProtocol(on_con_lost),
        remote_addr=(cfgs.udp.get("host"), cfgs.udp.get("port")),
    )

    try:
        await on_con_lost
    finally:
        transport.close()


asyncio.run(main())
