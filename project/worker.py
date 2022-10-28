import json
import math
import os
from typing import List

from celery import Celery, platforms
from redis_connect import redis_conn

celery = Celery(__name__)
celery.conf.BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://:123456@127.0.0.1:6379/0")
celery.conf.update(
    CELERY_ACCEPT_CONTENT=["pickle", "json"],
    CELERYD_FORCE_EXECV=True,
    CELERYD_MAX_TASKS_PER_CHILD=500,
    CELERYD_TASK_TIME_LIMIT=60,
)
platforms.C_FORCE_ROOT = True

# 垂直
vertical = [
    0.0,
    -0.582,
    -1.175,
    -1.77,
    -2.38,
    -3.03,
    -3.605,
    -4.142,
    -4.865,
    -5.367,
    -6.025,
    -6.56,
    -7.25,
    -7.807,
    -8.35,
    -8.995,
    -10.01,
    -10.982,
    -12.007,
    -12.925,
    -14.005,
    -14.997,
    -16.001,
    -16.987,
    -19.012,
    -20.847,
    -23.079,
    -24.955,
    -28.052,
    -30.805,
    -33.897,
    -36.575,
]
# 水平
horizontal = [
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
    4.2,
    0.0,
]


def get_value_(b):
    return b & 0xFF


def get_value(b1, b2):
    return get_value_(b2) << 8 | get_value_(b1)


def parse(data, start, values):
    # 转方向角为弧度
    alpha = math.radians(get_value(data[start + 2], data[start + 3]) * 0.01)
    # 每个方向角32条线束
    for i in range(32):
        # 从方向角信息获取当前线束方向角
        omega = math.radians(vertical[i])
        delta = math.radians(horizontal[i])
        # 解析激光束距离
        distance = get_value(data[4 * i + start + 4], data[4 * i + start + 5]) * 4
        # 分别求 x,y,z 方向的距离
        z = round(float(distance * math.sin(omega)))
        if abs(z) >= 4100:
            values.append(round(float(distance * math.cos(omega) * math.sin(alpha + delta))))
            values.append(round(float(distance * math.cos(omega) * math.cos(alpha + delta))))
            values.append(round(float(distance * math.sin(omega))))


@celery.task
def parses(list_data, key):
    # 开始解析

    result: List[int] = []
    for i, value in enumerate(list_data):
        for j in range(10):
            parse(bytes.fromhex(value), j * 132 + 20, result)
    # 存储redis
    redis_conn.set(key, json.dumps(result, separators=(",", ":")), ex=60 * 3)
