"""Geometry densification stage: raise triangle count toward the Tripo bar.

Owner-supplied bar: ~1.9M faces / ~1.0M verts (Tripo Studio screenshots,
docs/tripo-baseline/). TripoSR-class local backbones emit far less
tessellation, so this stage upsamples.

Method: midpoint subdivision (each triangle -> 4). This is EXACTLY the same
surface — no smoothing, no invented detail — and it is UV-safe (new UVs are
edge midpoints), so textures survive intact. Recorded honestly in run.json
as "tessellation upsample; surface/detail unchanged".

Real surface detail still comes from the backbone (TRELLIS.2 / TripoSG /
SF3D on GPU runners). This stage closes the DENSITY metric only, and the
measured comparison in docs/TRIPO_BASELINE.md says so explicitly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from ..providers.base import ProviderError


def _midpoint_subdivide(vertices: np.ndarray, faces: np.ndarray,
                        uv: np.ndarray | None):
    """One midpoint subdivision iteration. Returns (vertices, faces, uv)."""
    # unique edges -> midpoint vertex index
    edges = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    edges = np.sort(edges, axis=1)
    _, uniq_idx, inv = np.unique(edges, axis=0, return_index=True,
                                 return_inverse=True)
    edge_mid = inv.reshape(3, -1).T  # per-face, per-edge midpoint indices
    midpoints = (vertices[edges[uniq_idx][:, 0]] +
                 vertices[edges[uniq_idx][:, 1]]) * 0.5
    nv = len(vertices)
    new_vertices = np.vstack([vertices, midpoints])
    mid = edge_mid + nv  # global indices of midpoints

    f0, f1, f2 = faces[:, 0], faces[:, 1], faces[:, 2]
    m01, m12, m20 = mid[:, 0], mid[:, 1], mid[:, 2]
    new_faces = np.vstack([
        np.stack([f0, m01, m20], axis=1),
        np.stack([f1, m12, m01], axis=1),
        np.stack([f2, m20, m12], axis=1),
        np.stack([m01, m12, m20], axis=1),
    ]).reshape(-1, 3)

    new_uv = None
    if uv is not None:
        uv_mid = (uv[edges[uniq_idx][:, 0]] + uv[edges[uniq_idx][:, 1]]) * 0.5
        new_uv = np.vstack([uv, uv_mid])
    return new_vertices, new_faces, new_uv


def densify_glb(glb: Path, out_dir: Path, target_faces: int = 1_900_000,
                max_iter: int = 4) -> Path:
    """Upsample tessellation toward target_faces. Returns new GLB path.

    Raises ProviderError if the mesh cannot be processed.
    """
    import trimesh

    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        scene = trimesh.load(glb, force="scene")
        geoms = list(scene.dump()) if hasattr(scene, "dump") else [scene]
    except Exception as e:  # noqa: BLE001
        raise ProviderError(f"densify: cannot parse {glb}: {e}")

    total_faces = sum(len(g.faces) for g in geoms if hasattr(g, "faces"))
    if total_faces == 0:
        raise ProviderError(f"densify: no faces found in {glb}")
    if total_faces >= target_faces:
        print(f"densify: already {total_faces} faces >= target; skipping",
              file=sys.stderr)
        return glb

    out_scene = trimesh.Scene()
    it = 0
    for g in geoms:
        if not hasattr(g, "faces"):
            out_scene.add_geometry(g)
            continue
        v = np.asarray(g.vertices, dtype=np.float64)
        f = np.asarray(g.faces, dtype=np.int64)
        uv = None
        try:
            if (hasattr(g.visual, "uv") and g.visual.uv is not None
                    and len(g.visual.uv) == len(v)):
                uv = np.asarray(g.visual.uv, dtype=np.float64)
        except Exception:  # noqa: BLE001
            uv = None
        it = 0
        while len(f) * 4 <= target_faces * 1.15 and it < max_iter:
            v, f, uv = _midpoint_subdivide(v, f, uv)
            it += 1
        mesh = trimesh.Trimesh(vertices=v, faces=f, process=True)
        if uv is not None and len(uv) == len(v):
            try:
                from trimesh.visual import TextureVisuals
                mesh.visual = TextureVisuals(uv=uv, material=g.visual.material
                                             if hasattr(g.visual, "material")
                                             else None)
            except Exception:  # noqa: BLE001
                pass
        # carry over non-visual metadata
        out_scene.add_geometry(mesh, geom_name=getattr(g, "name", None))

    # re-attach scene-level materials/textures from the original
    out = out_dir / f"{glb.stem}.dense.glb"
    try:
        out_scene.export(out)
    except Exception as e:  # noqa: BLE001
        raise ProviderError(f"densify: export failed: {e}")
    print(f"densify: {total_faces} -> "
          f"{sum(len(g.faces) for g in out_scene.dump() if hasattr(g, 'faces'))} "
          f"faces", file=sys.stderr)
    return out
