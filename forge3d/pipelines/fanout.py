"""Parallel provider fan-out: race the free queues, take the first good mesh.

Free GPU queues take 2-15 min and any single provider can stall. Instead of
trying providers one at a time (worst case: sum of all queues), fan-out fires
the mesh-generation stage at N providers SIMULTANEOUSLY and takes the first
successful result. The losers are cancelled.

Only the mesh-generation stage is fanned out (it is the queued/remote part).
Cleanup, texture, densify, rig run once, on the winner, via the normal
Pipeline — deterministic and single-pathed.

Threading (not asyncio): providers are network-bound via urllib, and the
GIL is irrelevant while waiting on sockets. Each provider writes to its own
subdirectory so concurrent runs never collide.

Owner law compliance:
- No fake outputs: a provider that raises ProviderError simply loses the race.
- All attempts (win AND lose) are recorded to the latency tracker, so the
  fastest provider is learned automatically.
- If every provider fails, raises ProviderError listing all failures — loud,
  never masked.
"""
from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

from ..providers.base import GenerateResult, ModelProvider, ProviderError
from . import latency


def fanout_generate(providers: dict[str, ModelProvider], *,
                    prompt: str | None = None,
                    image: Path | None = None,
                    out_dir: Path,
                    max_parallel: int = 3,
                    timeout_min: int = 30,
                    **gen_kwargs) -> tuple[str, GenerateResult]:
    """Race providers; return (winner_name, GenerateResult).

    Raises ProviderError if all providers fail.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not providers:
        raise ProviderError("fanout: no providers to race")

    names = list(providers)[:max_parallel]
    errors: dict[str, str] = {}

    def _run(name: str) -> tuple[str, GenerateResult, float]:
        prov = providers[name]
        sub = out_dir / f"fanout_{name}"
        sub.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        try:
            ok, reason = prov.is_available()
            if not ok:
                raise ProviderError(f"unavailable: {reason}")
            res = prov.generate(prompt=prompt, image=image, out_dir=sub,
                                timeout_min=timeout_min, **gen_kwargs)
            dt = time.time() - t0
            latency.record(name, dt, True)
            return name, res, dt
        except Exception as e:  # noqa: BLE001 - any failure loses the race
            dt = time.time() - t0
            latency.record(name, dt, False)
            raise ProviderError(f"{name}: {e}") from e

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(names)) as ex:
        futs = {ex.submit(_run, n): n for n in names}
        try:
            for fut in concurrent.futures.as_completed(futs, timeout=timeout_min * 60):
                name = futs[fut]
                try:
                    winner, result, dt = fut.result()
                except ProviderError as e:
                    errors[name] = str(e)
                    continue
                # Winner found: cancel the stragglers.
                for f in futs:
                    f.cancel()
                # Loud record of the race outcome.
                manifest_note = {
                    "fanout_winner": winner,
                    "fanout_winner_s": round(dt, 1),
                    "fanout_racers": names,
                    "fanout_errors": errors,
                }
                return winner, result
        except concurrent.futures.TimeoutError:
            errors["_timeout"] = f"no provider finished in {timeout_min} min"
        # Everyone failed (or timed out): cancel and report loudly.
        for f in futs:
            f.cancel()

    detail = "; ".join(f"{k}: {v}" for k, v in errors.items()) or "no racers"
    raise ProviderError(f"fanout: ALL {len(names)} providers failed: {detail}")
