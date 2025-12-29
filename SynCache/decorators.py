import re
from functools import wraps

from SynCache.Cache import Cache


def _eval_single(expr, args, kwargs, result=None):
    """Evaluate a single '#expr' like '#user.id'."""
    expr = expr[1:]  # remove leading '#'
    parts = expr.split(".")

    if parts[0] == "result":
        value = result
    elif parts[0] in kwargs:
        value = kwargs[parts[0]]
    else:
        raise SyntaxError(
            f"Cannot evaluate expression '#{expr}'. "
            f"To use parameter names in cache key expressions, you must call your function with named parameters.\n"
            f"Example: Instead of get_user(123), use get_user(user_id=123)"
        )

    for p in parts[1:]:
        value = getattr(value, p) if hasattr(value, p) else value[p]

    return value


def _eval_expr(expr, args, kwargs, result=None):
    """
    Evaluate compound expressions like:
    - "#user.id-#order_type"
    - "#user.id_#order_type"
    - "#user.id/#order_type"
    - "#user.id#order_type"
    """

    # Regex that captures:
    # #word(.word)*
    pattern = r"#\w+(?:\.\w+)*"

    def replacer(match):
        return str(_eval_single(match.group(0), args, kwargs, result))

    return re.sub(pattern, replacer, expr)


def cacheable(namespace: str, key: str, return_type=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            controller = Cache.get_instance()

            cache_key = str(_eval_expr(key, args, kwargs))
            cached = controller.get(namespace, cache_key, return_type)

            if cached is not None:
                return cached

            result = func(*args, **kwargs)

            controller.set(namespace, cache_key, result)
            return result

        return wrapper

    return decorator


def cache_put(namespace: str, key: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            controller = Cache.get_instance()
            result = func(*args, **kwargs)

            cache_key = str(_eval_expr(key, args, kwargs, result=result))
            controller.set(namespace, cache_key, result)

            return result

        return wrapper

    return decorator


def cache_evict(namespace: str, key: str = None, all_entries=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            controller = Cache.get_instance()

            result = func(*args, **kwargs)

            if not all_entries and key is None:
                raise SyntaxError("Either 'key' or 'all_entries' must be specified.")

            if all_entries:
                controller.evict_namespace(namespace)
            else:
                cache_key = str(_eval_expr(key, args, kwargs, result=result))
                controller.evict(namespace, cache_key)

            return result

        return wrapper

    return decorator
