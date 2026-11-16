"""Sliding-window rate limiter (in-memory, per process)."""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from typing import Callable


class SlidingWindowLimiter:
    def __init__(self, monotonic: Callable[[], float] = time.monotonic, max_keys: int = 10_000) -> None:
        self._now = monotonic
        self._max_keys = max_keys
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: float) -> tuple[bool, int]:
        """Record a hit. Returns (allowed, retry_after_seconds). Denied hits are not recorded."""
        now = self._now()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            cutoff = now - window_seconds
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= limit:
                retry = max(1, math.ceil(q[0] + window_seconds - now))
                return False, retry
            q.append(now)
            if len(self._hits) > self._max_keys:
                self._purge(now, window_seconds)
            return True, 0

    def _purge(self, now: float, window_seconds: float) -> None:
        for k in [k for k, q in self._hits.items() if not q or q[-1] <= now - window_seconds]:
            del self._hits[k]
