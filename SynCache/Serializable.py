import time
import datetime




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

    # Unknown type → error
    raise ValueError(f"Unsupported TTL type: {type(ttl).__name__}")
