import asyncio
import os
import ssl

from aiomqtt import Client, MqttError
from loguru import logger

_url = os.getenv("OPENF1_MQTT_URL")
_port = int(os.getenv("OPENF1_MQTT_PORT"))
_username = os.getenv("OPENF1_MQTT_USERNAME")
_password = os.getenv("OPENF1_MQTT_PASSWORD")


async def _simulate_network_hang():
    """This function simulates a hanging network call and will never return."""
    logger.warning(">>> SIMULATING NETWORK HANG. THIS TASK WILL NOW FREEZE. <<<")
    hang_event = asyncio.Event()
    await hang_event.wait()  # This will wait forever as the event is never set


_client = Client(
    hostname=_url,
    port=_port,
    username=_username,
    password=_password,
    tls_context=ssl.create_default_context(),
)


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
    print(topic, messages)
    if _client is None:
        return False

    # if "driver" in topic.lower():
    #    await _simulate_network_hang()

    if not messages:
        logger.warning("No messages to publish.")
        return True

    try:
        async with _client as client:
            for message in messages:
                await client.publish(topic, payload=message, qos=qos)
        return True
    except MqttError as e:
        logger.error(f"MQTT Error while publishing to topic '{topic}': {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during MQTT publish: {e}")
        return False


"""
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
    _client = None

"""
