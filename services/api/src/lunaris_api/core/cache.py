"""Small in-process TTL cache with stale-read support (caching boundary for upstream data).

Single-process only. A multi-instance deployment needs a shared cache (Redis) behind
the same interface; see README "Known limitations".
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Generic, Hashable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CacheHit(Generic[T]):
    value: T
    age_seconds: float


class TTLCache(Generic[T]):
    def __init__(self, max_entries: int = 256, monotonic: Callable[[], float] = time.monotonic) -> None:
        self._max = max_entries
        self._now = monotonic
        self._data: dict[Hashable, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def put(self, key: Hashable, value: T) -> None:
        with self._lock:
            if key not in self._data and len(self._data) >= self._max:
                oldest = min(self._data, key=lambda k: self._data[k][0])
                del self._data[oldest]
            self._data[key] = (self._now(), value)

    def get(self, key: Hashable, max_age_seconds: float) -> CacheHit[T] | None:
        """Return the entry only if it is no older than max_age_seconds."""
        # A zero TTL is an explicit cache bypass. Without this guard, a value can
        # appear fresh when two monotonic reads land on the same clock tick.
        if max_age_seconds <= 0:
            return None
        with self._lock:
            item = self._data.get(key)
        if item is None:
            return None
        age = self._now() - item[0]
        if age > max_age_seconds:
            return None
        return CacheHit(value=item[1], age_seconds=age)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
