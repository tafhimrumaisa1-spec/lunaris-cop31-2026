from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    """Timezone-aware UTC now. UTC is the only internal representation."""
    return datetime.now(timezone.utc)
