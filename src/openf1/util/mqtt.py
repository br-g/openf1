import os
import ssl

from aiomqtt import Client, MqttError
from loguru import logger

_url = os.getenv("OPENF1_MQTT_URL")
_port = int(os.getenv("OPENF1_MQTT_PORT"))
_username = os.getenv("OPENF1_MQTT_USERNAME")
_password = os.getenv("OPENF1_MQTT_PASSWORD")

_tls_context = ssl.create_default_context()


async def publish_messages_to_mqtt(
    topic: str, messages: list[str], qos: int = 0
) -> bool:
    """
    Publish multiple messages to an MQTT topic asynchronously.

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
        async with Client(
            hostname=_url,
            port=_port,
            username=_username,
            password=_password,
            tls_context=_tls_context,
        ) as client:
            for message in messages:
                await client.publish(topic, payload=message, qos=qos)

        return True

    except MqttError as e:
        logger.error(f"MQTT Error while publishing to topic '{topic}': {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during MQTT publish: {e}")
        return False
