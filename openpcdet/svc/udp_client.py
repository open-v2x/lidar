import glob
import os
import time
from socket import AF_INET, SOCK_DGRAM, socket
from typing import List

from config import cfgs

if __name__ == "__main__":

    ADDRESS = (cfgs.udp.get("host"), cfgs.udp.get("port"))
    udp_client = socket(AF_INET, SOCK_DGRAM)
    dir_path = "velo"  # 指定目录的路径
    file_extension = "*.bin"  # 指定文件的后缀名
    file_list = glob.glob(os.path.join(dir_path, file_extension))
    num_files = len(file_list)  # 获取文件数量
    file_list.sort(key=lambda x: int(os.path.basename(x).split(".")[0]))
    data: List = [[] for _ in range(num_files)]
    for i, filename in enumerate(file_list):
        with open(f"velo/{filename}", "rb") as f:
            for _ in range(180):
                data[i].append(f.read(1024 * 10))
    while True:
        try:
            for udp_data_list in data:
                for udp_data in udp_data_list:
                    udp_client.sendto(udp_data, ADDRESS)
                    time.sleep(0.0001)
                time.sleep(0.01)
        except Exception as e:
            print(e)
        time.sleep(2)
        udp_client.sendto(b"clear", ADDRESS)
