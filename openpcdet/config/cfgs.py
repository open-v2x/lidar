import os

DEFAULT_REDIS_HOST = "127.0.0.1"
DEFAULT_REDIS_PASSWORD = "password"

DEFAULT_WS_HOST = "127.0.0.1"

redis = {
    "host": os.getenv("redis_host") or DEFAULT_REDIS_HOST,
    "port": 6379,
    "password": os.getenv("redis_password") or DEFAULT_REDIS_PASSWORD,
    "db": 1,
}

websocket = {
    "host": os.getenv("ws_host") or DEFAULT_WS_HOST,
    "port": 28300,
}
