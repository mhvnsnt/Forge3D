"""Pose / animate stage — inject Bannon procedural moves into a rigged GLB.

Reuses the owner's Bannon generative motion tools (procedural_moves.py +
common/glb_anim.py) WITHOUT copying them: the module is imported from the
Bannon tree (default ~/workspace/bannon-repair/tools/generative, override
with FORGE3D_BANNON_GENERATIVE) and its export_move_onto_glb() is called
programmatically. Output is validated: the GLB must contain a MOVE_<name>
animation with >0 channels, else ProviderError (never a silent no-op).
"""
from __future__ import annotations

import json
import os
import struct
import sys
from pathlib import Path

from ..providers.base import ProviderError

HOME = Path.home()
DEFAULT_BANNON_GENERATIVE = (
    HOME / "workspace" / "bannon-repair" / "tools" / "generative")


def bannon_generative_dir() -> Path:
    env = os.environ.get("FORGE3D_BANNON_GENERATIVE")
    if env and Path(env).exists():
        return Path(env)
    if DEFAULT_BANNON_GENERATIVE.exists():
        return DEFAULT_BANNON_GENERATIVE
    raise ProviderError(
        "pose stage unavailable: Bannon generative tools not found at "
        f"{DEFAULT_BANNON_GENERATIVE}; set FORGE3D_BANNON_GENERATIVE.")


def list_moves() -> list:
    """Names of available procedural moves."""
    gdir = bannon_generative_dir()
    sys.path.insert(0, str(gdir / "motion"))
    try:
        import procedural_moves as pm
        return sorted(pm.MOVES.keys())
    finally:
        sys.path.remove(str(gdir / "motion"))


def apply_move(glb_in: Path, move: str, glb_out: Path) -> Path:
    """Inject one procedural move as a glTF animation. Returns glb_out."""
    glb_in, glb_out = Path(glb_in), Path(glb_out)
    glb_out.parent.mkdir(parents=True, exist_ok=True)
    gdir = bannon_generative_dir()
    mdir = str(gdir / "motion")
    sys.path.insert(0, mdir)
    try:
        import procedural_moves as pm
        if move not in pm.MOVES:
            raise ProviderError(
                f"pose stage: unknown move '{move}' "
                f"(known: {sorted(pm.MOVES.keys())[:8]}...)")
        pm.export_move_onto_glb(move, str(glb_in), str(glb_out))
    finally:
        sys.path.remove(mdir)

    # validate: animation really landed
    data = glb_out.read_bytes()
    if data[:4] != b"glTF":
        raise ProviderError(f"pose stage: {glb_out.name} is not a GLB")
    ln = struct.unpack("<I", data[12:16])[0]
    js = json.loads(data[20:20 + ln])
    anims = [a for a in js.get("animations", [])
             if a.get("name") == f"MOVE_{move}"]
    chans = sum(len(a.get("channels", [])) for a in anims)
    if not anims or chans == 0:
        raise ProviderError(
            f"pose stage: MOVE_{move} missing/empty in {glb_out.name} "
            f"(node names may not match the 58-bone namespace)")
    print(f"pose: {glb_in.name} + MOVE_{move} -> {glb_out.name} "
          f"({chans} channels)", file=sys.stderr)
    return glb_out
