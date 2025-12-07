import jsons

from ._core import Controller as _Controller


class Controller(_Controller):
    def __init__(self, broker_url, broker_auth_token, max_entries):
        super().__init__(broker_url, broker_auth_token, max_entries)

    def set(self, namespace: str, id: str, value, ttl: int = None):
        value = jsons.dumps(value)
        super().set(str(namespace), str(id), value.encode("utf-8"), ttl)

    def get(self, namespace: str, id: str, return_type=None):
        value = super().get(str(namespace), str(id))

        if value is None:
            return None
        if return_type is not None:
            return jsons.loads(value.decode("utf-8"), return_type)
        return value.decode("utf-8")

    def evict(self, namespace: str, id: str):
        super().evict(namespace, id)

    def evict_all(self):
        super().evict_all()

    def evict_namespace(self, namespace: str):
        super().evict_namespace(namespace)
