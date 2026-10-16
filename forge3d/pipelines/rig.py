"""Auto-rig stage: skin an unrigged GLB to a game skeleton.

Ported from AshLanev2 tools/auto-rig/auto_rig.py (provenance: docs/PROVENANCE.md).
Backend is instance-rig (MIT) via its existing venv — BodyPix 2D pose ->
3D skeleton + skin weights, pure CPU. Runs as a subprocess; output is
validated (bone count > 0) and failures raise ProviderError — never a fake rig.

Note: instance-rig emits its own skeleton topology. Mapping that onto the
owner's 58-bone Mixamo-style game skeleton is the job of the Bannon/AshLanev2
retargeters (handoff stage) — this stage's contract is "rigged, validated",
not "58 bones exactly". The measured bone count is recorded in run.json.

Environment note (2026-10-16): on the CPU-only agent VM the instance-rig
venv is DOWN — its open3d dependency needs system libEGL.so.1, which is not
installed and apt is unavailable. When the venv is missing, the stage falls
back to the Blender auto_skin path (headless, Bannon lineage), which rigs
straight onto the canonical 58-bone Western Heart skeleton. Either path
validates bone count > 0 and raises loudly on failure — never a fake rig.
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

# canonical 58-bone Mixamo-style skeleton (extracted from CIPHER_repaired.glb,
# provenance: docs/PROVENANCE.md) + BVH->mixamorig name map (from Bannon)
SKELETON_58 = Path(__file__).resolve().parent / "skeleton_58.json"
MIXAMO_MAP = Path(__file__).resolve().parent / "mixamo_map.json"


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

    out = out_dir / f"{glb.stem}.rigged.glb"

    # Fallback chain (2026-10-16): the instance-rig venv needs system GL libs
    # and is DOWN on minimal CPU hosts. The Blender auto_skin path (proven
    # Bannon lineage, headless) rigs straight onto the canonical 58-bone
    # Western Heart skeleton and runs anywhere Blender runs.
    if not VENV_PY.exists():
        from ..blender.stage import auto_skin
        print(f"rig: instance-rig venv missing — Blender auto_skin fallback "
              f"onto {SKELETON_58.name}", file=sys.stderr)
        auto_skin(glb, out, SKELETON_58, timeout=timeout)
        n = bone_count(out)
        if n <= 0:
            raise ProviderError(
                f"rig stage (blender fallback) produced unrigged output "
                f"({out.name}); refusing to ship it")
        print(f"rig: {glb.name} -> {out.name} ({n} bones, blender fallback)",
              file=sys.stderr)
        return out

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


def retarget_to_58(glb: Path, out_dir: Path, timeout: int = 1200) -> Path:
    """Re-skin a rigged GLB onto the canonical 58-bone Mixamo skeleton.

    Extends (does not fork) the rig stage: delegates to the Blender stage's
    retarget_58, then validates the output really has 58 joints. Raises
    ProviderError on any failure — never a fake rig.
    """
    from ..blender.stage import retarget_58 as _blender_retarget_58
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not SKELETON_58.exists():
        raise ProviderError(f"retarget stage: {SKELETON_58.name} missing")
    out = out_dir / f"{glb.stem}.58bone.glb"
    _blender_retarget_58(glb, out, SKELETON_58,
                         MIXAMO_MAP if MIXAMO_MAP.exists() else None,
                         timeout=timeout)
    n = bone_count(out)
    if n != 58:
        raise ProviderError(
            f"retarget stage: expected 58 bones, got {n} in {out.name}")
    print(f"rig: {glb.name} -> {out.name} (58 bones verified)",
          file=sys.stderr)
    return out
