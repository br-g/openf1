import asyncio
import os
import ssl

from aiomqtt import Client, MqttError
from loguru import logger

_url = os.getenv("OPENF1_MQTT_URL")
_port_str = os.getenv("OPENF1_MQTT_PORT")
_username = os.getenv("OPENF1_MQTT_USERNAME")
_password = os.getenv("OPENF1_MQTT_PASSWORD")

_tls_context = ssl.create_default_context()

_client: Client | None = None
_client_lock = asyncio.Lock()


def _is_client_connected(client: Client | None) -> bool:
    """
    Check if the client is connected.
    Handles inconsistencies in how aiomqtt exposes connection status by checking
    the internal `_connected` Future object directly.
    """
    if not client or not hasattr(client, "_connected"):
        return False
    return client._connected.done() and not client._connected.cancelled()


async def _get_or_create_client() -> Client:
    """
    Lazily initializes and returns the MQTT client.
    This ensures the client is only created within a running event loop.
    """
    global _client
    async with _client_lock:
        if _client is None:
            logger.info("Initializing MQTT client")
            _client = Client(
                hostname=_url,
                port=int(_port_str),
                username=_username,
                password=_password,
                tls_context=_tls_context,
            )
            logger.info("MQTT client initialized")
    return _client


async def _connect_client():
    """Connects the client if it's not already connected."""
    client = await _get_or_create_client()
    if not _is_client_connected(client):
        logger.info("Connecting to MQTT broker")
        await client.__aenter__()
        logger.info("Successfully connected to MQTT broker")


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
        client = await _get_or_create_client()
        if not _is_client_connected(client):
            await _connect_client()

        for message in messages:
            await client.publish(topic, payload=message, qos=qos)
        return True

    except (MqttError, ValueError) as e:
        logger.error(f"MQTT error while publishing to topic '{topic}': {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during MQTT publish: {e}")
        return False
