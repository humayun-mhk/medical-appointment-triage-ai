from time import monotonic
from typing import Callable, TypeVar

T = TypeVar("T")

_CACHE: dict[str, tuple[float, object]] = {}


def cached_value(key: str, ttl_seconds: int, factory: Callable[[], T]) -> T:
    now = monotonic()
    cached = _CACHE.get(key)
    if cached:
        expires_at, value = cached
        if expires_at > now:
            return value  # type: ignore[return-value]

    value = factory()
    _CACHE[key] = (now + ttl_seconds, value)
    return value


def clear_cache_prefix(prefix: str) -> None:
    for key in list(_CACHE):
        if key.startswith(prefix):
            _CACHE.pop(key, None)
