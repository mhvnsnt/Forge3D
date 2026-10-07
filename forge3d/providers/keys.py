"""Shared API-key loader for Forge3D providers.

Resolution order for ``FORGE3D_<PROVIDER>_KEY``:
  1. Process environment (explicit export wins).
  2. ``~/.config/forge3d/api_keys.env`` (mode 600, ``KEY=VALUE`` lines) —
     the documented home for keys per ``docs/ACCOUNTS.md``.

Keys are NEVER printed, logged, or committed. This module only reads them
into memory for outbound API calls.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

KEY_FILE = Path.home() / ".config" / "forge3d" / "api_keys.env"


@lru_cache(maxsize=1)
def _file_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    try:
        text = KEY_FILE.read_text(encoding="utf-8")
    except OSError:
        return keys
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        if name.startswith("export "):  # allow `export KEY=...` syntax
            name = name[len("export "):].strip()
        value = value.strip().strip('"').strip("'")
        if name and value:
            keys[name] = value
    return keys


def get_key(env_name: str) -> str:
    """Return the key for ``env_name`` (env first, then the key file)."""
    key = os.environ.get(env_name, "").strip()
    if key:
        return key
    return _file_keys().get(env_name, "")


def key_source(env_name: str) -> str:
    """Where a key resolved from, without revealing the value."""
    if os.environ.get(env_name, "").strip():
        return "env"
    if env_name in _file_keys():
        return "key-file"
    return "missing"
