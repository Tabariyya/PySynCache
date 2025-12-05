import json
import base64
import decimal
import uuid
import inspect

import time
import datetime


class Serializable:
    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        params = inspect.signature(cls.__init__).parameters
        ctor_args = {
            name: data[name]
            for name in params
            if name != 'self' and name in data
        }

        return cls(**ctor_args)


def to_json(value):
    # None, bool, int, float, str are already JSON-safe
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    # Serializable objects → their JSON dict
    if isinstance(value, Serializable):
        return json.loads(value.to_json())

    # dict → recursively convert
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}

    # list, tuple, set → list of converted items
    if isinstance(value, (list, tuple, set)):
        return [to_json(v) for v in value]

    # datetime → ISO8601 string
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()

    # Decimal → convert to float or str (I choose str to avoid precision loss)
    if isinstance(value, decimal.Decimal):
        return str(value)

    # UUID → string
    if isinstance(value, uuid.UUID):
        return str(value)

    # bytes → base64
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(value).decode()

    # fallback: attempt str() (safe_str behavior)
    try:
        return str(value)
    except Exception:
        return f"<unserializable {type(value).__name__}>"


def to_epoch(ttl):
    """Convert many time formats into epoch seconds.
    Raises ValueError if the value cannot be interpreted as time.
    """

    # None → not allowed
    if ttl is None:
        return None

    # Already epoch (int or float)
    if isinstance(ttl, (int, float)):
        return int(ttl)

    # datetime → epoch
    if isinstance(ttl, datetime.datetime):
        if ttl.tzinfo is None:
            ttl = ttl.replace(tzinfo=datetime.timezone.utc)
        return int(ttl.timestamp())

    # date → epoch at midnight UTC
    if isinstance(ttl, datetime.date):
        dt = datetime.datetime(ttl.year, ttl.month, ttl.day, tzinfo=datetime.timezone.utc)
        return int(dt.timestamp())

    # timedelta → now + delta
    if isinstance(ttl, datetime.timedelta):
        return int(time.time()) + int(ttl.total_seconds())

    # Strings
    if isinstance(ttl, str):
        s = ttl.strip().lower()

        # Relative formats (10s, 10m, 2h, 1d)
        if s[-1] in ("s", "m", "h", "d") and len(s) > 1:
            unit = s[-1]
            num = s[:-1]
            try:
                amount = float(num)
                seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
                return int(time.time()) + int(amount * seconds)
            except:
                raise ValueError(f"Invalid TTL relative format: {ttl}")

        # Try a series of datetime formats
        datetime_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%MZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ]

        for fmt in datetime_formats:
            try:
                dt = datetime.datetime.strptime(s, fmt)
                dt = dt.replace(tzinfo=datetime.timezone.utc)
                return int(dt.timestamp())
            except:
                pass

        # Check for epoch string
        if s.isdigit():
            return int(s)

        raise ValueError(f"Cannot parse TTL: {ttl}")

    # Unknown type → error
    raise ValueError(f"Unsupported TTL type: {type(ttl).__name__}")
