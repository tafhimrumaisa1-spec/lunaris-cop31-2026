from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def load_factors() -> dict:
    return json.loads((_DATA / "factors.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_source_manifest() -> dict:
    return json.loads((_DATA / "source_manifest.json").read_text(encoding="utf-8"))


def factors_verified() -> bool:
    return load_factors()["meta"]["verification_status"] == "verified"
