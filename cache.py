from __future__ import annotations
from cachetools import TTLCache
from typing import Any, Hashable

class AppCache:
    """Process-local cache (works for a single Streamlit instance)."""
    def __init__(self, maxsize: int, ttl_seconds: int):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def get(self, key: Hashable) -> Any | None:
        return self._cache.get(key)

    def set(self, key: Hashable, value: Any) -> None:
        self._cache[key] = value
