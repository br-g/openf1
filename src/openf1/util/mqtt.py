import os
import ssl

import paho.mqtt.client as mqtt
from loguru import logger

_url = os.getenv("OPENF1_MQTT_URL")
_port = int(os.getenv("OPENF1_MQTT_PORT"))
_username = os.getenv("OPENF1_MQTT_USERNAME")
_password = os.getenv("OPENF1_MQTT_PASSWORD")

_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
_client.username_pw_set(_username, _password)
_client.tls_set(
    ca_certs=None,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS_CLIENT,
)

try:
    logger.info(f"Connecting to MQTT broker {_url}:{_port}...")
    _client.connect(_url, _port, keepalive=60)
    _client.loop_start()
    logger.info("MQTT client connected and running")
except Exception as e:
    logger.error(f"Failed to connect: {e}")
    raise


async def publish_messages_to_mqtt(
    topic: str, messages: list[str], qos: int = 1
) -> bool:
    """
    Publish multiple messages to an MQTT topic asynchronously.

    Args:
        topic: The MQTT topic to publish to
        messages: List of message contents to publish
        qos: Quality of Service level (0, 1, or 2)
    """
    if not messages:
        logger.warning("No messages to publish")
        return True
    try:
        for message in messages:
            result = _client.publish(topic, message, qos=qos)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish: {mqtt.error_string(result.rc)}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error batch publishing: {e}")
        return False
