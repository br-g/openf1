import os
import ssl

from aiomqtt import Client, MqttError
from loguru import logger

_url = os.getenv("OPENF1_MQTT_URL")
_port_str = os.getenv("OPENF1_MQTT_PORT")
_username = os.getenv("OPENF1_MQTT_USERNAME")
_password = os.getenv("OPENF1_MQTT_PASSWORD")
_disable_tls = os.getenv("OPENF1_MQTT_NO_TLS")

if _disable_tls.lower() == "true":
    _tls_context = None
else:
    _tls_context = ssl.create_default_context()

_client: Client | None = None


async def initialize_mqtt():
    """
    Initializes and connects the global MQTT client.
    Should be called once when the application starts.
    """
    if not _url:
        logger.info("MQTT credentials not found, MQTT is disabled")
        return

    global _client
    if _client is None:
        logger.info("Initializing MQTT client...")
        _client = Client(
            hostname=_url,
            port=int(_port_str),
            username=_username,
            password=_password,
            tls_context=_tls_context,
        )
        try:
            await _client.__aenter__()
            logger.info("Successfully connected to MQTT broker")
        except (MqttError, ValueError, OSError) as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            _client = None
    else:
        logger.info("MQTT client is already initialized")


async def publish_messages_to_mqtt(
    topic: str, messages: list[str], qos: int = 0
) -> bool:
    """
    Publishes multiple messages to an MQTT topic asynchronously.
    Assumes initialize_mqtt() has already been called.

    Args:
        topic: The MQTT topic to publish to
        messages: List of message contents to publish
        qos: Quality of Service level (0, 1, or 2)
    """
    if not _url:
        return False

    if not messages:
        logger.warning("No messages to publish")
        return True

    try:
        for message in messages:
            await _client.publish(topic, payload=message, qos=qos)
        return True
    except MqttError as e:
        logger.exception(f"MQTT error while publishing to topic '{topic}': {e}")
        return False
    except Exception:
        logger.exception("An unexpected error occurred during MQTT publish")
        return False
