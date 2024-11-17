import base64
import json
import zlib


def decode(data: str) -> dict:
    """Decodes raw data from either JSON or Base64 encoded compressed JSON"""
    data = data.strip()
    try:
        return json.loads(data.strip('"'))
    except Exception:
        s = zlib.decompress(base64.b64decode(data), -zlib.MAX_WBITS)
        return json.loads(s.decode("utf-8-sig"))
