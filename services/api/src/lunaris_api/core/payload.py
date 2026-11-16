"""Envelope checks for free-form JSON bodies handed to downstream packages."""
from __future__ import annotations

import math
from typing import Any


class PayloadError(ValueError):
    pass


def check_json_payload(obj: Any, *, max_depth: int = 8, max_nodes: int = 2000, max_string: int = 2000) -> None:
    """Reject NaN/Infinity, excessive depth, node count or string length. Raises PayloadError."""
    nodes = 0

    def walk(v: Any, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            raise PayloadError("payload has too many values")
        if depth > max_depth:
            raise PayloadError("payload is nested too deeply")
        if isinstance(v, float) and not math.isfinite(v):
            raise PayloadError("payload contains a non-finite number")
        elif isinstance(v, str):
            if len(v) > max_string:
                raise PayloadError("payload contains an overlong string")
        elif isinstance(v, dict):
            for k, x in v.items():
                if not isinstance(k, str) or len(k) > 200:
                    raise PayloadError("payload contains an invalid key")
                walk(x, depth + 1)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x, depth + 1)
        elif v is None or isinstance(v, (bool, int, float)):
            pass
        else:
            raise PayloadError("payload contains a non-JSON value")

    walk(obj, 0)
