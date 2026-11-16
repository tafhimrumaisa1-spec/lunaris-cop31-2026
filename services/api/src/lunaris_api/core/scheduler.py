"""Scheduler interface. Deliberately NO implementation that fakes recurring jobs.

A real implementation (e.g. APScheduler, a worker queue, or cron hitting an internal
endpoint) must be chosen at deployment time. Until then NullScheduler is bound and
reports that nothing is scheduled.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Callable, Protocol


class Scheduler(Protocol):
    def register(self, name: str, func: Callable[[], None], every: timedelta) -> None: ...
    def jobs(self) -> list[str]: ...


class SchedulerNotConfigured(RuntimeError):
    pass


class NullScheduler:
    """Refuses registration so nothing can pretend to run on a schedule."""

    def register(self, name: str, func: Callable[[], None], every: timedelta) -> None:
        raise SchedulerNotConfigured(
            f"No scheduler backend is configured; job {name!r} was NOT scheduled."
        )

    def jobs(self) -> list[str]:
        return []
