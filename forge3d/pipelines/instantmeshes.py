"""instantmeshes.py — Instant Meshes quad-dominant remesh backend (quality100 wave 2).

Wraps the Instant Meshes batch CLI (wjakob/instant-meshes, BSD-3-Clause,
built from source — see docs/QUALITY100.md for the TBB/GCC build notes).
Field-aligned quad-dominant remeshing: the topology-gap closer for
animation-ready edge flow.

This is a NEW backend feeding the sibling's REMESH_SHOOTOUT.md — it does
not duplicate forge3d/pipelines/quadremesh.py (Blender Quadriflow path);
both backends are contenders in the shootout.

Binary resolution: $FORGE3D_INSTANTMESHES_BIN, else
~/workspace/build/instant-meshes/build/"Instant Meshes".

Output: <stem>.im.obj/.im.glb + <stem>.instantmeshes.json
(quad fraction, face counts, seconds).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

from ..providers.base import ProviderError

DEFAULT_BIN = (Path.home() / "workspace" / "build" / "instant-meshes"
               / "build" / "Instant Meshes")


def _binary() -> Path:
    env = os.environ.get("FORGE3D_INSTANTMESHES_BIN")
    if env and Path(env).exists():
        return Path(env)
    if DEFAULT_BIN.exists():
        return DEFAULT_BIN
    raise ProviderError(
        "instantmeshes: binary not found — build wjakob/instant-meshes "
        "or set FORGE3D_INSTANTMESHES_BIN")


def _quad_fraction(obj_path: Path) -> dict:
    """Fraction of quad faces by counting face vertex records in the OBJ."""
    quads = tris = 0
    with open(obj_path) as f:
        for line in f:
            if line.startswith("f "):
                n = len(line.split()) - 1
                if n == 4:
                    quads += 1
                elif n == 3:
                    tris += 1
    total = quads + tris
    return {"quads": quads, "tris": tris,
            "quad_fraction": round(quads / total, 4) if total else 0.0}


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        faces: int = 20000, deterministic: bool = True,
        smooth_iter: int = 2) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = _binary()

    scene = trimesh.load(str(glb_path), force="scene")
    mesh = list(scene.geometry.values())[0]
    obj_in = out_dir / f"{glb_path.stem}.im_in.obj"
    obj_out = out_dir / f"{glb_path.stem}.im_out.obj"
    mesh.export(str(obj_in))

    cmd = [str(binary), str(obj_in), "-o", str(obj_out), "-f", str(faces),
           "-S", str(smooth_iter)]
    if deterministic:
        cmd.append("-d")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not obj_out.exists():
        raise ProviderError(
            f"instantmeshes: batch failed: {r.stderr[-1500:]}")

    q = _quad_fraction(obj_out)
    out_glb = out_dir / f"{glb_path.stem}.im.glb"
    trimesh.load(str(obj_out), force="mesh").export(str(out_glb))

    metrics = {"input": str(glb_path), "binary": str(binary),
               "in_faces": int(len(mesh.faces)),
               "target_faces": faces, "deterministic": deterministic,
               **q, "output": str(out_glb),
               "seconds": round(time.time() - t0, 1)}
    (out_dir / f"{glb_path.stem}.instantmeshes.json").write_text(
        json.dumps(metrics, indent=2))
    return metrics


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: instantmeshes.py <in.glb> <out_dir> [faces]", file=sys.stderr)
        sys.exit(2)
    faces = int(sys.argv[3]) if len(sys.argv) == 4 else 20000
    print(json.dumps(run(sys.argv[1], sys.argv[2], faces=faces), indent=2))


if __name__ == "__main__":
    main()
