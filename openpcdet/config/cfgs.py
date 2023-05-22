import os

# default redis config
DEFAULT_REDIS_HOST = "127.0.0.1"
DEFAULT_REDIS_PASSWORD = "password"
DEFAULT_REDIS_PORT = 6379

# default websocket config
DEFAULT_WS_HOST = "127.0.0.1"
DEFAULT_WS_PORT = 28300

# default mqtt config
DEFAULT_MQTT_HOST = "127.0.0.1"
DEFAULT_MQTT_USERNAME = "root"
DEFAULT_MQTT_PASSWORD = "password"
DEFAULT_MQTT_PORT = 1883

# default udp config
DEFAULT_UDP_HOST = "0.0.0.0"
DEFAULT_UDP_PORT = 57142
DEFAULT_DATA_PATH = "data/"

# default openpcdet config
DEFAULT_CFG_FILE = "tools/cfgs/custom_models/centerpoint.yaml"
DEFAULT_CKPT = "ckpt/checkpoint_centerpoint_2100.pth"
DEFAULT_SCORE_THR = 0.3

redis = {
    "host": os.getenv("redis_host") or DEFAULT_REDIS_HOST,
    "port": os.getenv("redis_port") or DEFAULT_REDIS_PORT,
    "password": os.getenv("redis_password") or DEFAULT_REDIS_PASSWORD,
    "db": 1,
}

websocket = {
    "host": os.getenv("ws_host") or DEFAULT_WS_HOST,
    "port": os.getenv("ws_port") or DEFAULT_WS_PORT,
}

mqtt = {
    "host": os.getenv("mqtt_host") or DEFAULT_MQTT_HOST,
    "port": os.getenv("mqtt_port") or DEFAULT_MQTT_PORT,
    "username": os.getenv("mqtt_username") or DEFAULT_MQTT_USERNAME,
    "password": os.getenv("mqtt_password") or DEFAULT_MQTT_PASSWORD,
    "topic": "V2X/DEVICE/LIDAR/PARTICIPANT",
}

udp = {
    "host": os.getenv("udp_host") or DEFAULT_UDP_HOST,
    "port": os.getenv("udp_port") or DEFAULT_UDP_PORT,
    "dir_path": os.getenv("dir_path") or DEFAULT_DATA_PATH,
    "total_lens": int(os.getenv("total_lens", 180 * 10240)),
    "packet_number": int(os.getenv("packet_number", 180)),
    "packet_lens": int(os.getenv("packet_lens", 10240)),
    "sleep_time": float(os.getenv("sleep_time", 0.2)),
}


cfg_file = {
    "cfg_file": DEFAULT_CFG_FILE,
}

ckpt = {
    "ckpt": DEFAULT_CKPT,
}

score_thr = {
    "score_thr": DEFAULT_SCORE_THR,
}
