from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class TokenBucket:
    """Simple token bucket for per-session rate limiting."""
    capacity: float
    refill_per_sec: float
    tokens: float
    last_ts: float

    @classmethod
    def per_minute(cls, rpm: int) -> "TokenBucket":
        cap = float(rpm)
        return cls(capacity=cap, refill_per_sec=cap/60.0, tokens=cap, last_ts=time.time())

    def allow(self, cost: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_ts
        self.last_ts = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
