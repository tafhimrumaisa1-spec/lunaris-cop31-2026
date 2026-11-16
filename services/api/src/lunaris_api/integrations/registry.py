"""Bind providers from "module:attr" entrypoints. Fails fast on misconfiguration."""
from __future__ import annotations

import importlib
import inspect
from typing import Any

from ..config import Settings
from .ports import Providers


class ProviderLoadError(RuntimeError):
    pass


def load_entrypoint(spec: str) -> Any:
    """`pkg.mod:Attr`. A class is instantiated with no args; a function is called with no args;
    anything else (an already-built object) is used as-is."""
    if ":" not in spec:
        raise ProviderLoadError(f"entrypoint {spec!r} must look like 'package.module:Attr'")
    mod_name, attr = spec.split(":", 1)
    try:
        module = importlib.import_module(mod_name)
        obj = getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise ProviderLoadError(f"cannot load provider {spec!r}: {exc}") from exc
    if inspect.isclass(obj) or inspect.isfunction(obj):
        try:
            return obj()
        except Exception as exc:  # noqa: BLE001
            raise ProviderLoadError(f"provider {spec!r} failed to initialise: {exc}") from exc
    return obj


def load_providers(settings: Settings) -> Providers:
    p = Providers()
    for field_name, spec in (
        ("weather", settings.weather_provider),
        ("climate", settings.climate_engine),
        ("choices", settings.choices_engine),
        ("places", settings.places_provider),
        ("business", settings.business_evidence_provider),
    ):
        if spec:
            setattr(p, field_name, load_entrypoint(spec))
    return p
