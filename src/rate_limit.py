# src/rate_limit.py
from __future__ import annotations

import time


class TokenBucket:
    """
    Simple token bucket rate limiter.
    - rpm: allowed requests per minute
    - burst: max burst tokens stored (defaults to rpm)
    """

    def __init__(self, rpm: int, burst: int | None = None):
        if rpm <= 0:
            raise ValueError("rpm must be > 0")

        self.rpm = int(rpm)
        self.capacity = int(burst) if burst is not None else int(rpm)
        self.tokens = float(self.capacity)
        self.refill_per_sec = self.rpm / 60.0
        self.updated_at = time.monotonic()

    def allow(self, cost: float = 1.0) -> bool:
        """Return True if request is allowed; otherwise False."""
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.updated_at = now

        # refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)

        if self.tokens >= cost:
            self.tokens -= cost
            return True

        return False
