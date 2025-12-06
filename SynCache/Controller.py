import jsons

from ._core import Controller as _Controller

from .Serializable import to_epoch


class Controller(_Controller):
    def __init__(self, broker_url, broker_auth_token, max_entries):
        super().__init__(broker_url, broker_auth_token, max_entries)

    def set(self, namespace, id, value, ttl=None):
        value = jsons.dumps(value)
        ttl = to_epoch(ttl)
        super().set(namespace, id, value.encode("utf-8"), ttl)

    def get(self, namespace, id, return_type=None):
        value = super().get(namespace, id)

        if return_type is not None:
            return jsons.loads(value.decode("utf-8"), return_type)
        return value.decode("utf-8")

    def evict(self, namespace, id):
        super().evict(namespace, id)

    def evict_all(self):
        super().evict_all()

    def evict_namespace(self, namespace):
        super().evict_namespace(namespace)
