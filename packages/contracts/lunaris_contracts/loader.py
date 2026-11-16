"""Read contracts/data-models.json and contracts/openapi-target.yaml.

data-models.json describes fields with type strings such as "string|null", "number",
"Evidence[]" or enums like "live|historical|modeled|demo|self_reported|verified".
`parse_type_spec` separates enum unions from primitive-type unions so tests can compare
enum members precisely.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

PRIMITIVES = {"string", "number", "boolean", "null", "object", "integer"}
_ENUM_MEMBER = re.compile(r"^[a-z][a-z0-9_]*$")


class ContractNotFound(FileNotFoundError):
    pass


def find_contracts_dir(start: Path | None = None) -> Path:
    """Locate `contracts/` (or `packages/contracts/`) holding data-models.json.

    Order: $LUNARIS_CONTRACTS_DIR, then walk upward from `start` (default: cwd)."""
    env = os.environ.get("LUNARIS_CONTRACTS_DIR")
    if env:
        p = Path(env)
        if (p / "data-models.json").is_file():
            return p
        raise ContractNotFound(f"LUNARIS_CONTRACTS_DIR={env} has no data-models.json")
    here = (start or Path.cwd()).resolve()
    for base in [here, *here.parents]:
        for sub in ("contracts", "packages/contracts"):
            if (base / sub / "data-models.json").is_file():
                return base / sub
    raise ContractNotFound("contracts/data-models.json not found; set LUNARIS_CONTRACTS_DIR")


def load_data_models(contracts_dir: Path | None = None) -> dict[str, Any]:
    d = contracts_dir or find_contracts_dir()
    return json.loads((d / "data-models.json").read_text(encoding="utf-8"))


def parse_type_spec(spec: str) -> tuple[str, Any]:
    """("enum", {members}) | ("type", {parts}) for a contract type string."""
    parts = [p.strip() for p in spec.split("|")]
    if len(parts) > 1 and not (set(parts) <= PRIMITIVES | {"null"}) and all(_ENUM_MEMBER.match(p) for p in parts):
        return "enum", set(parts)
    return "type", set(parts)


def contract_fields(model: str, contracts_dir: Path | None = None) -> set[str]:
    return set(load_data_models(contracts_dir)[model].keys())


def enum_values(model: str, field: str, contracts_dir: Path | None = None) -> set[str]:
    spec = load_data_models(contracts_dir)[model][field]
    kind, members = parse_type_spec(spec)
    if kind != "enum":
        raise ValueError(f"{model}.{field} is not an enum in the contract: {spec!r}")
    return members


def load_openapi_paths(contracts_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    import yaml  # optional dependency (extra: openapi)

    d = contracts_dir or find_contracts_dir()
    doc = yaml.safe_load((d / "openapi-target.yaml").read_text(encoding="utf-8"))
    return doc["paths"]
