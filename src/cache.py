# src/cache.py
from __future__ import annotations

import time
from typing import Any, Callable


class AppCache:
    """
    Simple in-memory TTL cache.
    - ttl_seconds: how long a key stays valid
    - maxsize: soft cap (evicts oldest when exceeded)
    """

    def __init__(self, ttl_seconds: int = 300, maxsize: int = 2048):
        self.ttl_seconds = int(ttl_seconds)
        self.maxsize = int(maxsize)
        self._store: dict[str, tuple[float, Any]] = {}  # key -> (expires_at, value)
        self._order: list[str] = []  # insertion order for eviction

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [k for k, (exp, _) in self._store.items() if exp <= now]
        for k in expired:
            self._store.pop(k, None)
            # remove from order if present
            try:
                self._order.remove(k)
            except ValueError:
                pass

    def get(self, key: str) -> Any | None:
        self._purge_expired()
        item = self._store.get(key)
        if not item:
            return None
        exp, val = item
        if exp <= time.time():
            self._store.pop(key, None)
            try:
                self._order.remove(key)
            except ValueError:
                pass
            return None
        return val

    def set(self, key: str, value: Any) -> None:
        self._purge_expired()
        expires_at = time.time() + self.ttl_seconds

        # update existing key in-order
        if key in self._store:
            self._store[key] = (expires_at, value)
            return

        # evict if needed
        if len(self._store) >= self.maxsize and self._order:
            oldest = self._order.pop(0)
            self._store.pop(oldest, None)

        self._store[key] = (expires_at, value)
        self._order.append(key)

    def get_or_set(self, key: str, compute_fn: Callable[[], Any]) -> Any:
        """
        Return cached value if available; otherwise compute, store, return.
        """
        cached = self.get(key)
        if cached is not None:
            return cached

        value = compute_fn()
        self.set(key, value)
        return value

    def clear(self) -> None:
        self._store.clear()
        self._order.clear()
