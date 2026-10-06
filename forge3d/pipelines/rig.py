"""Auto-rig stage: skin an unrigged GLB to a game skeleton.

Ported from AshLanev2 tools/auto-rig/auto_rig.py (provenance: docs/PROVENANCE.md).
Backend is instance-rig (MIT) via its existing venv — BodyPix 2D pose ->
3D skeleton + skin weights, pure CPU. Runs as a subprocess; output is
validated (bone count > 0) and failures raise ProviderError — never a fake rig.

Note: instance-rig emits its own skeleton topology. Mapping that onto the
owner's 58-bone Mixamo-style game skeleton is the job of the Bannon/AshLanev2
retargeters (handoff stage) — this stage's contract is "rigged, validated",
not "58 bones exactly". The measured bone count is recorded in run.json.

Environment note (2026-10-06): on the CPU-only agent VM the instance-rig
venv is DOWN — its open3d dependency needs system libEGL.so.1, which is not
installed and apt is unavailable. The stage fails loudly with that reason
(no fake rig). It runs on hosts with system GL libs (Kaggle/Colab/GPU box).
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

from ..providers.base import ProviderError

HOME = Path.home()

# instance-rig venv (built by the animation harvest; MIT-licensed tool)
VENV_PY = HOME / "workspace/anim-harvest/.venv-ir/bin/python"


def bone_count(path: Path) -> int:
    """Count skin joints in a GLB. -1 if not a GLB at all."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"glTF":
        return -1
    ln = struct.unpack("<I", data[12:16])[0]
    js = json.loads(data[20:20 + ln])
    return sum(len(s.get("joints", [])) for s in js.get("skins", []))


def rig_glb(glb: Path, out_dir: Path, timeout: int = 600) -> Path:
    """Rig an unrigged GLB. Returns path to the rigged GLB.

    Raises ProviderError on any failure (venv missing, backend crash,
    output unrigged). Already-rigged inputs pass through untouched.
    """
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if bone_count(glb) > 0:
        return glb  # already rigged — honest pass-through

    if not VENV_PY.exists():
        raise ProviderError(
            f"rig stage unavailable: instance-rig venv not found at {VENV_PY}")

    out = out_dir / f"{glb.stem}.rigged.glb"
    cmd = [str(VENV_PY), "-m", "instancerig", str(glb), "-o", str(out)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise ProviderError(f"rig stage timed out after {timeout}s: {e}")
    if r.returncode != 0:
        raise ProviderError(f"rig stage failed: {r.stderr[-800:]}")
    n = bone_count(out)
    if n <= 0:
        raise ProviderError(
            f"rig stage produced unrigged output ({out.name}); refusing to ship it")
    print(f"rig: {glb.name} -> {out.name} ({n} bones)", file=sys.stderr)
    return out
