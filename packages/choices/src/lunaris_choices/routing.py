"""Pluggable routing interface. DISABLED: no licensed provider/key is configured, so no route, time or traffic is ever produced."""
from __future__ import annotations

from typing import Protocol


class RoutingDisabled(RuntimeError):
    pass


class RoutingProvider(Protocol):
    name: str
    enabled: bool

    def route(self, origin: tuple, destination: tuple, mode: str) -> dict: ...


class DisabledRoutingProvider:
    name = "disabled"
    enabled = False
    reason = "No licensed routing provider or API key configured (see DATA_AND_EVIDENCE.md item 6)."

    def route(self, origin, destination, mode):
        raise RoutingDisabled(self.reason)
