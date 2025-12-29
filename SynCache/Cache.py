import jsons

from ._core import Controller as _Controller


class Cache(_Controller):
    _instance = None
    _broker_url = None
    _broker_auth_token = None
    _max_entries = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = Cache(cls._broker_url, cls._broker_auth_token,
                                  cls._max_entries)
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the singleton has been initialized with parameters."""
        return cls._instance is not None

    @classmethod
    def initialize(cls, broker_url: str, broker_auth_token: str, max_entries: int):
        """Initialize the singleton instance."""
        cls._broker_url = broker_url
        cls._broker_auth_token = broker_auth_token
        cls._max_entries = max_entries

    def __init__(self, broker_url, broker_auth_token, max_entries):
        super().__init__(broker_url, broker_auth_token, max_entries)

    def set(self, namespace: str, id: str, value, ttl: int = None):
        if not isinstance(value, str):
            value = jsons.dumps(value)

        super().set(str(namespace), str(id), value.encode('UTF-8'), ttl)

    def get(self, namespace: str, id: str, return_type=None):
        value = super().get(str(namespace), str(id))

        if value is None or value.decode('UTF-8') == "null":
            return None
        if return_type is not None and return_type != str:
            return jsons.loads(value.decode("utf-8"), return_type)
        return value.decode("utf-8")

    def evict(self, namespace: str, id: str):
        super().evict(namespace, id)

    def evict_all(self):
        super().evict_all()

    def evict_namespace(self, namespace: str):
        super().evict_namespace(namespace)
