"""Measure peak RSS of a TripoSR generation run.

Parent process: gates on free RAM, takes the single-flight lock, spawns the
venv python as a child running the provider, polls /proc/PID/status for
VmHWM (kernel high-water mark — no sampling gaps), and reports peak RSS +
timing. Usage:

    python3 -m forge3d.tools.measure_ram --image runs/gen1/concept1.jpg \\
        --resolution 128 --out /tmp/ramtest --min-ram 2.0
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
VENV_PY = Path.home() / "workspace" / "forge3d-venv" / "bin" / "python"

CHILD_DRIVER = r"""
import os, sys, time
sys.path.insert(0, {repo!r})
from forge3d.tools.ram_gate import limit_threads
limit_threads(1)
from pathlib import Path
from forge3d.providers.triposr import TripoSRProvider
p = TripoSRProvider()
t0 = time.time()
r = p.generate(image={image!r}, out_dir=Path({out!r}),
               mc_resolution={res}, remove_bg=False)
print("RESULT", r.glb_path, f"{{time.time()-t0:.1f}}s", flush=True)
"""


def peak_hwm(pid: int, poll_s: float = 1.0):
    """Poll VmHWM until the process exits. Returns (peak_gb, wall_s)."""
    peak_kb = 0
    t0 = time.time()
    while True:
        try:
            with open(f"/proc/{pid}/status") as f:
                for line in f:
                    if line.startswith("VmHWM:"):
                        kb = int(line.split()[1])
                        peak_kb = max(peak_kb, kb)
                        break
        except FileNotFoundError:
            break
        if proc.poll() is not None:
            # one last read attempt right after exit
            try:
                with open(f"/proc/{pid}/status") as f:
                    for line in f:
                        if line.startswith("VmHWM:"):
                            peak_kb = max(peak_kb, int(line.split()[1]))
                            break
            except FileNotFoundError:
                pass
            break
        time.sleep(poll_s)
    return peak_kb / 1024 / 1024, time.time() - t0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--resolution", type=int, default=128)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-ram", type=float, default=2.0)
    ap.add_argument("--timeout", type=float, default=1800.0)
    ap.add_argument("--chunk", type=int, default=8192)
    args = ap.parse_args()

    from forge3d.tools.ram_gate import wait_for_ram, inference_lock
    wait_for_ram(args.min_ram, timeout_s=args.timeout)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["FORGE3D_TRIPOSR_CHUNK"] = str(args.chunk)
    env["FORGE3D_TRIPOSR_BF16"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"

    driver = CHILD_DRIVER.format(repo=str(REPO), image=args.image,
                                 out=str(out), res=args.resolution)
    with inference_lock():
        proc = subprocess.Popen(
            [str(VENV_PY), "-c", driver],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, env=env, cwd=str(REPO))
        peak_gb, wall_s = peak_hwm(proc.pid)
        tail = proc.stdout.read()[-1500:]
    rc = proc.returncode
    print(f"resolution={args.resolution} chunk={args.chunk} "
          f"peak_rss={peak_gb:.2f}GB wall={wall_s:.0f}s rc={rc}")
    print("--- child tail ---")
    print(tail)
    sys.exit(0 if rc == 0 else 1)
