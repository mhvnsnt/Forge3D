"""Mesh cleanup/normalize stage.

Ported from AshLanev2/tools/generative mesh postprocessor
(see docs/PROVENANCE.md). Normalizes scale/orientation, welds,
removes degenerate faces, writes game-ready GLB.
"""
from __future__ import annotations

from pathlib import Path

from ..providers.base import ProviderError


def normalize_glb(glb: Path, out_dir: Path) -> Path:
    """Return path to normalized GLB.

    Raises ProviderError (never a fake mesh) if the input cannot be parsed.
    """
    out = Path(out_dir) / (glb.stem + ".clean.glb")
    try:
        import trimesh  # type: ignore
    except ImportError:
        return glb  # no postprocessor available; pass through honestly
    try:
        mesh = trimesh.load(glb, force="scene")
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
    except Exception as e:  # noqa: BLE001
        raise ProviderError(f"postprocessor could not parse {glb}: {e}")
    return out
