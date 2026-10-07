"""Per-provider latency tracking: learn which provider is fastest, prefer it.

Records every generation attempt (provider, seconds, success) into
~/.forge3d/latency.json. `ranked()` sorts candidate providers by their
exponential moving average of successful latencies; providers with no
history sort after measured ones (they get tried, then learned).

This does NOT reduce queue latency itself — it minimizes WASTED time by
trying the historically-fastest provider first and deprioritizing
providers that are slow or flaky. Combined with fan-out (pipelines/fanout.py)
it attacks the 2-15 min free-queue problem from both ends.

Honest note (owner law): without paid compute, latency floor is the
fastest free queue available. This module finds that floor automatically.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

STORE = Path.home() / ".forge3d" / "latency.json"
ALPHA = 0.35  # EMA weight for new observations


def _load() -> dict:
    try:
        return json.loads(STORE.read_text())
    except Exception:  # noqa: BLE001 - missing/corrupt store = fresh start
        return {}


def _save(data: dict) -> None:
    try:
        STORE.parent.mkdir(parents=True, exist_ok=True)
        STORE.write_text(json.dumps(data, indent=2))
    except Exception:  # noqa: BLE001 - latency tracking is best-effort
        pass


def record(provider: str, seconds: float, success: bool) -> None:
    """Record one generation attempt. Never raises."""
    data = _load()
    e = data.setdefault(provider, {"ema": None, "n": 0, "fails": 0,
                                   "last_ts": 0.0})
    if success:
        e["ema"] = seconds if e["ema"] is None else ALPHA * seconds + (1 - ALPHA) * e["ema"]
        e["n"] += 1
    else:
        e["fails"] += 1
    e["last_ts"] = time.time()
    _save(data)


def ema(provider: str) -> float | None:
    """Historical mean latency for successful runs, or None if unknown."""
    return _load().get(provider, {}).get("ema")


def ranked(candidates: list[str]) -> list[str]:
    """Sort providers: measured-fastest first, unmeasured next, known-flaky last.

    Flaky = more fails than successes and no recent success. Unmeasured
    providers still get tried (they might BE the fast one) but after
    providers with proven speed.
    """
    data = _load()

    def key(name: str):
        e = data.get(name, {})
        ema_v = e.get("ema")
        n = e.get("n", 0)
        fails = e.get("fails", 0)
        flaky = fails > n and n == 0
        # (flaky last, unmeasured middle, measured by ema first)
        return (1 if flaky else 0,
                0 if ema_v is not None else 1,
                ema_v if ema_v is not None else 0.0,
                name)

    return sorted(candidates, key=key)


def summary() -> dict:
    """Human-readable latency table for docs/debugging."""
    data = _load()
    return {k: {"ema_s": round(v["ema"], 1) if v.get("ema") else None,
                "runs": v.get("n", 0), "fails": v.get("fails", 0)}
            for k, v in sorted(data.items())}
