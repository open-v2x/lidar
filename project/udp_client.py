import os
import time
from socket import AF_INET, SOCK_DGRAM, socket
from typing import List

if __name__ == "__main__":

    HOST = os.environ.get("udp_host", "127.0.0.1")
    PORT = 57142

    ADDRESS = (HOST, PORT)
    udp_client = socket(AF_INET, SOCK_DGRAM)
    file_list = os.listdir("velo")
    file_list.sort(key=lambda x: int(x.split(".")[0]))
    data: List = [[] for _ in range(392)]
    for i, filename in enumerate(file_list):
        with open(f"velo/{filename}", "rb") as f:
            for _ in range(180):
                data[i].append(f.read(1024 * 10))
    while True:
        try:
            for udp_data_list in data:
                for udp_data in udp_data_list:
                    udp_client.sendto(udp_data, ADDRESS)
                    time.sleep(0.001)
                time.sleep(0.01)
        except Exception as e:
            print(e)
        time.sleep(2)
        udp_client.sendto(b"clear", ADDRESS)
