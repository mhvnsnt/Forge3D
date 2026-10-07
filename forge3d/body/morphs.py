"""Semantic body morphs — Prisma-style body customization without MPI data.

SMPL-X/FLAME/STAR are Max Planck NON-COMMERCIAL research licenses — they
cannot ship in a commercial game pipeline (verified 2026-10-06). These morphs
are authored deformation fields (no statistical model, no tainted weights):
smooth region masks over normalized body space, applied pre-rig.

Pipeline order: generate -> morph -> rig. Morphs run on the unrigged mesh.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from ..providers.base import ProviderError


def _smoothstep(a, b, x):
    t = np.clip((x - a) / max(b - a, 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def region_masks(V):
    """Smooth anatomical region masks over a Y-up humanoid mesh.

    Assumes roughly T/A-pose, feet at y=0. Returns dict of (N,) float masks.
    """
    mn, mx = V.min(0), V.max(0)
    yn = (V[:, 1] - mn[1]) / max(mx[1] - mn[1], 1e-9)  # 0 feet .. 1 head top
    hw = max(mx[0] - mn[0], 1e-9) / 2
    cx = (mn[0] + mx[0]) / 2
    radial = np.abs(V[:, 0] - cx) / hw  # 0 center .. ~1 sides

    legs = 1 - _smoothstep(0.50, 0.56, yn)
    torso = _smoothstep(0.50, 0.56, yn) * (1 - _smoothstep(0.82, 0.88, yn))
    head = _smoothstep(0.86, 0.92, yn)
    arms = (_smoothstep(0.10, 0.22, radial)
            * _smoothstep(0.52, 0.58, yn) * (1 - _smoothstep(0.80, 0.86, yn)))
    chest = torso * _smoothstep(0.68, 0.74, yn) * (1 - _smoothstep(0.80, 0.84, yn))
    belly = torso * _smoothstep(0.56, 0.62, yn) * (1 - _smoothstep(0.70, 0.74, yn))
    front = _smoothstep(0.0, 0.15, V[:, 2] / max(mx[2] - mn[2], 1e-9))
    return {"legs": legs, "torso": torso, "head": head, "arms": arms,
            "chest": chest, "belly": belly, "front": front,
            "yn": yn, "cx": cx, "mn": mn, "mx": mx}


# morph name -> (description, apply function)
def _bulk(V, M, v):
    s = 1 + 0.38 * v * (M["torso"] * 0.7 + M["arms"] * 0.5 + M["chest"] * 0.4)
    V[:, 0] = M["cx"] + (V[:, 0] - M["cx"]) * s
    V[:, 2] = V[:, 2] * (1 + 0.30 * v * M["torso"])


def _height(V, M, v):
    # stretch legs, shift everything above
    leg_gain = 1 + 0.22 * v * M["legs"]
    V[:, 1] = M["mn"][1] + (V[:, 1] - M["mn"][1]) * (
        M["legs"] * leg_gain + (1 - M["legs"]) * (1 + 0.22 * v * (1 - M["legs"])))
    # simpler: scale whole Y by (1+0.12v), extra leg stretch
    V[:, 1] = M["mn"][1] + (V[:, 1] - M["mn"][1]) * (1 + 0.10 * v)
    V[M["legs"] > 0.5, 1] += 0.12 * v * M["legs"][M["legs"] > 0.5] * (M["mx"][1] - M["mn"][1])


def _shoulder_width(V, M, v):
    m = M["chest"] + 0.5 * M["arms"]
    s = 1 + 0.30 * v * np.clip(m, 0, 1)
    V[:, 0] = M["cx"] + (V[:, 0] - M["cx"]) * s


def _belly(V, M, v):
    push = 0.25 * v * M["belly"] * M["front"]
    V[:, 2] = V[:, 2] + push * (M["mx"][2] - M["mn"][2])


def _arm_bulk(V, M, v):
    s = 1 + 0.45 * v * M["arms"]
    V[:, 0] = M["cx"] + (V[:, 0] - M["cx"]) * s
    V[:, 2] = V[:, 2] * (1 + 0.35 * v * M["arms"])


def _leg_bulk(V, M, v):
    s = 1 + 0.40 * v * M["legs"]
    V[:, 0] = M["cx"] + (V[:, 0] - M["cx"]) * s
    V[:, 2] = V[:, 2] * (1 + 0.30 * v * M["legs"])


MORPHS = {
    "bulk": ("overall torso+arm mass", _bulk),
    "height": ("taller via leg stretch", _height),
    "shoulder_width": ("broader shoulders", _shoulder_width),
    "belly": ("belly protrusion", _belly),
    "arm_bulk": ("arm mass", _arm_bulk),
    "leg_bulk": ("leg mass", _leg_bulk),
}


def apply_morphs(glb_in: Path, morph_spec: dict, glb_out: Path) -> Path:
    """Apply semantic morphs to an (unrigged) GLB. morph_spec: {name: -1..1}."""
    import trimesh
    glb_in, glb_out = Path(glb_in), Path(glb_out)
    for name in morph_spec:
        if name not in MORPHS:
            raise ProviderError(f"unknown morph '{name}' (known: {sorted(MORPHS)})")
    scene = trimesh.load(glb_in, force="scene")
    geoms = list(scene.dump()) if hasattr(scene, "dump") else [scene]
    # work in mesh-local space; assume consistent orientation across parts
    for g in geoms:
        V = np.array(g.vertices, dtype=np.float64)
        M = region_masks(V)
        for name, val in morph_spec.items():
            if abs(val) < 1e-9:
                continue
            MORPHS[name][1](V, M, float(val))
        g.vertices = V
    merged = trimesh.util.concatenate(geoms)
    merged.export(glb_out)
    return glb_out


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Semantic body morphs")
    ap.add_argument("input"); ap.add_argument("output")
    for name, (desc, _) in MORPHS.items():
        ap.add_argument(f"--{name}", type=float, default=0.0, help=desc)
    args = ap.parse_args()
    spec = {n: getattr(args, n) for n in MORPHS if abs(getattr(args, n)) > 1e-9}
    if not spec:
        raise SystemExit("no morph values given")
    out = apply_morphs(Path(args.input), spec, Path(args.output))
    print(f"morphs {spec} -> {out}")


if __name__ == "__main__":
    main()
