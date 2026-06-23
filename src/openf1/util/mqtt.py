import os
import ssl

from aiomqtt import Client
from loguru import logger

_url = os.getenv("OPENF1_MQTT_URL")
_port_str = os.getenv("OPENF1_MQTT_PORT")
_port = int(_port_str)
_username = os.getenv("OPENF1_MQTT_USERNAME")
_password = os.getenv("OPENF1_MQTT_PASSWORD")
_disable_tls = os.getenv("OPENF1_MQTT_NO_TLS")

if isinstance(_disable_tls, str) and _disable_tls.lower() == "true":
    _tls_context = None
else:
    _tls_context = ssl.create_default_context()

_client: Client | None = None


async def _connect() -> None:
    """Tear down any existing client and open a fresh one.
    Never raises; leaves _client as None if connecting fails."""
    global _client
    old, _client = _client, None
    if old is not None:
        try:
            await old.__aexit__(None, None, None)
        except Exception:
            pass
    client = Client(
        hostname=_url,
        port=_port,
        username=_username,
        password=_password,
        tls_context=_tls_context,
    )
    try:
        await client.__aenter__()
        _client = client
        logger.info("Connected to MQTT broker")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")


async def initialize_mqtt() -> None:
    """Connect at startup. Publish will also reconnect on its own if needed."""
    if not _url:
        logger.info("MQTT credentials not found, MQTT is disabled")
        return
    await _connect()


async def publish_messages_to_mqtt(
    topic: str, messages: list[str], qos: int = 0
) -> bool:
    """
    Publishes multiple messages to an MQTT topic asynchronously.
    Assumes initialize_mqtt() has already been called.
    Never raises; on failure it drops the batch and returns False.

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

    if _client is None:
        await _connect()
    if _client is None:
        return False

    try:
        for message in messages:
            await _client.publish(topic, payload=message, qos=qos)
        return True
    except Exception as e:
        logger.warning(f"MQTT publish to '{topic}' failed, dropping batch: {e}")
        await _connect()  # reopen for the next call
        return False
