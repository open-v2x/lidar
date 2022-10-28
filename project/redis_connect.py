import os

import redis

redis_conn = redis.StrictRedis(
    host=os.environ.get("host", "127.0.0.1"),
    password=os.environ.get("redis_password", "123456"),
    port=6378,
)
