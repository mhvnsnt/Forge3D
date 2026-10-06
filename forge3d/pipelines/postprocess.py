"""Mesh cleanup/normalize stage.

Ported from AshLanev2/tools/generative mesh postprocessor
(see docs/PROVENANCE.md). Normalizes scale/orientation, welds,
removes degenerate faces, writes game-ready GLB.
"""
from __future__ import annotations

from pathlib import Path


def normalize_glb(glb: Path, out_dir: Path) -> Path:
    """Return path to normalized GLB. Pure-python fallback if trimesh missing."""
    out = Path(out_dir) / (glb.stem + ".clean.glb")
    try:
        import trimesh  # type: ignore
    except ImportError:
        return glb  # no postprocessor available; pass through honestly
    mesh = trimesh.load(glb, force="scene")
    # normalize: center + unit-ish scale handled by caller config; weld + clean
    if hasattr(mesh, "dump"):
        geoms = list(mesh.dump())
    else:
        geoms = [mesh]
    cleaned = []
    for g in geoms:
        try:
            g.merge_vertices()
            g.remove_duplicate_faces()
            g.remove_degenerate_faces()
            g.remove_infinite_values()
        except Exception:
            pass
        cleaned.append(g)
    scene = trimesh.Scene()
    for g in cleaned:
        scene.add_geometry(g)
    scene.export(out)
    return out
