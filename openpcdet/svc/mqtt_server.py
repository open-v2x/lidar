from __future__ import annotations

import uuid
from logging import LoggerAdapter
from typing import Any, Dict

import paho.mqtt.client as mqtt
from config import cfgs

MQTT_CLIENT: mqtt.Client = None


def get_mqtt_client() -> mqtt.Client:
    global MQTT_CLIENT
    if MQTT_CLIENT is None:
        raise SystemError("MQTT Client is none")
    return MQTT_CLIENT


def _on_connect(client: mqtt.Client, userdata: Any, flags: Any, rc: int) -> None:
    if rc != 0:
        raise SystemError("MQTT Connection failed")

    global MQTT_CLIENT
    MQTT_CLIENT = client


def _on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    # LOG.info(msg.payload.decode("utf-8"))
    pass


def _on_disconnect(client: mqtt.Client, userdata: Any, rc: int) -> None:
    # LOG.error(f"MQTT Connection disconnected, rc: {rc}")
    pass


def connect() -> None:

    _client = mqtt.Client(client_id=uuid.uuid4().hex)
    _client.username_pw_set(cfgs.mqtt.get("username"), cfgs.mqtt.get("password"))
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.on_disconnect = _on_disconnect
    _client.connect(cfgs.mqtt.get("host"), int(cfgs.mqtt.get("port")), 60)
    _client.loop_start()
