"""In-process rate limiting for authentication and upload endpoints.

A single-process limiter is adequate for the pilot deployment. Replacing it with
a shared store is a deployment decision, not an API change.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.errors import ApiError


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, *, code: str = "rate_limited") -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                raise ApiError(
                    429,
                    code,
                    "Too many requests",
                    detail="Please wait before retrying.",
                    retryable=True,
                )
            hits.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)


_limiter: SlidingWindowLimiter | None = None


def get_limiter() -> SlidingWindowLimiter:
    global _limiter
    if _limiter is None:
        from app.core.config import get_settings

        _limiter = SlidingWindowLimiter(get_settings().auth_rate_limit_per_minute)
    return _limiter
