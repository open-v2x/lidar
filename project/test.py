import time

import redis

redis_conn = redis.StrictRedis(password=123456, db=0)
for i in redis_conn.keys():
    redis_conn.delete(i)
