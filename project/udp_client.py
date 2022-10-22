import os
import time
from socket import *

from redis_connect import redis_conn

if __name__ == '__main__':

    HOST = os.environ.get('udp_host', '127.0.0.1')
    PORT = 57142

    ADDRESS = (HOST, PORT)

    udpClientSocket = socket(AF_INET, SOCK_DGRAM)
    while True:
        print('开始发送~', flush=True)
        udpClientSocket.sendto(b'1111', ADDRESS)
        try:
            with open("lid23D.cap", "rb")as f_r:
                other_len = 8  # 文件头
                header_len = 96  # 以太头
                data_length = 1340  # 一个数据包
                size = True
                f_r.read(other_len)
                while size:
                    f_r.read(header_len)
                    size = f_r.read(data_length)
                    # 发送数据
                    if size:
                        udpClientSocket.sendto(size, ADDRESS)
                    time.sleep(0.0005)
        except Exception as e:
            pass

        while redis_conn.llen('celery'):
            print('休息~', flush=True)
            time.sleep(1)
