"""Forge3D provider registry. Auto-discovery of providers/ modules."""
from __future__ import annotations

import importlib
import pkgutil

from .base import ModelProvider


def discover() -> dict[str, ModelProvider]:
    found: dict[str, ModelProvider] = {}
    import forge3d.providers as pkg
    for mod in pkgutil.iter_modules(pkg.__path__):
        if mod.name in ("base", "registry"):
            continue
        try:
            module = importlib.import_module(f"forge3d.providers.{mod.name}")
        except Exception:
            continue
        for attr in dir(module):
            obj = getattr(module, attr)
            if (isinstance(obj, type) and issubclass(obj, ModelProvider)
                    and obj is not ModelProvider):
                try:
                    inst = obj()
                    found[inst.info.name] = inst
                except Exception:
                    continue
    return found


def available() -> dict[str, ModelProvider]:
    return {n: p for n, p in discover().items() if p.is_available()[0]}
