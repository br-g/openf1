import asyncio
import os
import ssl

import paho.mqtt.client as mqtt
from loguru import logger


def _get_client():
    broker = os.getenv("OPENF1_MQTT_URL")
    port = int(os.getenv("OPENF1_MQTT_PORT"))
    username = os.getenv("OPENF1_MQTT_USERNAME")
    password = os.getenv("OPENF1_MQTT_PASSWORD")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.tls_set(
        ca_certs=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )

    try:
        logger.info(f"Connecting to MQTT broker {broker}:{port}...")
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        logger.info("MQTT client connected and running")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        raise

    return client


_client = _get_client()


async def publish_messages(topic: str, messages: list[str], qos: int = 1) -> bool:
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


def cleanup():
    _client.loop_stop()
    _client.disconnect()
    logger.info("MQTT client disconnected")


async def main():
    await publish_messages("test/topic", ["Hello5", "Hello4"])
    cleanup()


if __name__ == "__main__":
    asyncio.run(main())
