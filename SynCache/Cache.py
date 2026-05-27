from typing import Optional

import jsons

from ._core import Controller as _Controller

_NULL_BYTES = b"\x00__cache_null__\x00"


class _CacheMiss:
    """Sentinel returned by Cache.get() to indicate a cache miss (distinct from a cached None)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self):
        return False

    def __repr__(self):
        return "CACHE_MISS"


CACHE_MISS = _CacheMiss()


class Cache(_Controller):
    _instance = None
    _broker_auth_token = None
    _max_entries = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Cache(cls._broker_auth_token, cls._max_entries)
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def initialize(cls, broker_auth_token: str, max_entries: int):
        cls._broker_auth_token = broker_auth_token
        cls._max_entries = max_entries
        cls._instance = None

    def __init__(self, broker_auth_token, max_entries):
        super().__init__(broker_auth_token, max_entries)

    def set(self, namespace: str, id: str, value, ttl: Optional[int] = None):
        if value is None:
            super().set(str(namespace), str(id), _NULL_BYTES, ttl)
        else:
            if not isinstance(value, str):
                value = jsons.dumps(value)
            super().set(str(namespace), str(id), value.encode('UTF-8'), ttl)

    def _get(self, namespace: str, id: str, return_type=None):
        """Returns CACHE_MISS for misses; None for a cached None. Used internally by decorators."""
        value = super().get(str(namespace), str(id))
        if value is None:
            return CACHE_MISS
        if value == _NULL_BYTES:
            return None
        decoded = value.decode("utf-8")
        if return_type is not None and return_type != str:
            return jsons.loads(decoded, return_type)
        return decoded

    def get(self, namespace: str, id: str, return_type=None):
        result = self._get(namespace, id, return_type)
        return None if result is CACHE_MISS else result

    def evict(self, namespace: str, id: str):
        super().evict(namespace, id)

    def evict_all(self):
        super().evict_all()

    def evict_namespace(self, namespace: str):
        super().evict_namespace(namespace)
