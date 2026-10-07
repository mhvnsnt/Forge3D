"""RAM gate for local inference: wait for free RAM, single-flight lock, thread caps.

On this VM, TripoSR inference needs ~2.5GB sustained RAM while available RAM
swings 0.8-5GB as parallel agents come and go. Running blind = OOM roulette.
This module makes local generation wait its turn instead.
"""
from __future__ import annotations

import fcntl
import os
import time
from contextlib import contextmanager
from pathlib import Path

LOCK_PATH = Path.home() / ".forge3d" / "inference.lock"


def free_gb() -> float:
    """Available RAM in GiB (MemAvailable from /proc/meminfo)."""
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                kb = int(line.split()[1])
                return kb / 1024 / 1024
    raise RuntimeError("could not read MemAvailable")


def wait_for_ram(min_gb: float, timeout_s: float = 1800.0,
                 poll_s: float = 15.0) -> float:
    """Block until MemAvailable >= min_gb. Returns the free GB observed.

    Raises TimeoutError if the timeout expires. Logs progress to stderr so
    a waiting run is visible, not silent.
    """
    import sys
    deadline = time.time() + timeout_s
    waited = 0.0
    while True:
        free = free_gb()
        if free >= min_gb:
            if waited:
                print(f"[ram-gate] {free:.2f}GB free after {waited:.0f}s wait "
                      f"— proceeding", file=sys.stderr)
            return free
        if time.time() >= deadline:
            raise TimeoutError(
                f"only {free:.2f}GB free after {timeout_s:.0f}s; "
                f"need {min_gb:.2f}GB — refusing to OOM")
        if waited == 0 or int(waited) % 120 == 0:
            print(f"[ram-gate] waiting: {free:.2f}GB free, need {min_gb:.2f}GB "
                  f"(timeout {timeout_s - waited:.0f}s left)", file=sys.stderr)
        time.sleep(poll_s)
        waited += poll_s


@contextmanager
def inference_lock(timeout_s: float = 3600.0):
    """Single-flight lock: never two local inferences at once.

    Uses an flock'd lockfile; raises TimeoutError if another inference holds
    it past the timeout.
    """
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout_s
    fh = open(LOCK_PATH, "w")
    while True:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.write(f"{os.getpid()}\n")
            fh.flush()
            break
        except BlockingIOError:
            if time.time() >= deadline:
                fh.close()
                raise TimeoutError(
                    f"another inference holds {LOCK_PATH} past {timeout_s:.0f}s")
            time.sleep(10)
    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def limit_threads(n: int = 1) -> None:
    """Cap thread pools to bound allocator arenas and peak RSS.

    Env vars must be set BEFORE torch/OpenMP load; torch.set_num_threads
    applies to already-imported torch. Call as early as possible.
    """
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(var, str(n))
    try:
        import torch
        torch.set_num_threads(n)
        torch.set_num_interop_threads(n)
    except ImportError:
        pass
