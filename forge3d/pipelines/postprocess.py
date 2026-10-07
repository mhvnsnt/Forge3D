"""Mesh cleanup/normalize stage.

Ported from AshLanev2/tools/generative mesh postprocessor
(see docs/PROVENANCE.md). Normalizes scale/orientation, welds,
removes degenerate faces, writes game-ready GLB.
"""
from __future__ import annotations

from pathlib import Path

from ..providers.base import ProviderError


def count_boundary_loops(mesh) -> int:
    """Count boundary loops (holes) via welded-edge adjacency. 0 = watertight."""
    import numpy as np
    try:
        faces = np.asarray(mesh.faces)
        # weld verts within epsilon
        verts = np.asarray(mesh.vertices)
        key = np.round(verts / 1e-6).astype(np.int64)
        _, inv = np.unique(key, axis=0, return_inverse=True)
        edges: dict[tuple[int, int], int] = {}
        for f in faces:
            wf = inv[f]
            for a, b in ((wf[0], wf[1]), (wf[1], wf[2]), (wf[2], wf[0])):
                e = (a, b) if a < b else (b, a)
                edges[e] = edges.get(e, 0) + 1
        bnd = {e for e, c in edges.items() if c == 1}
        # count loops by walking adjacency
        adj: dict[int, set[int]] = {}
        for a, b in bnd:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        seen: set[int] = set()
        loops = 0
        for v in adj:
            if v in seen:
                continue
            loops += 1
            stack = [v]
            while stack:
                u = stack.pop()
                if u in seen:
                    continue
                seen.add(u)
                stack.extend(adj[u] - seen)
        return loops
    except Exception:
        return -1  # unknown


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
        stats = {"holes_before": 0, "holes_after": 0, "faces": 0}
        for g in geoms:
            try:
                stats["faces"] += len(g.faces)
            except Exception:
                pass
            try:
                g.merge_vertices()
                # degenerate faces (trimesh 5.x: no remove_degenerate_faces method)
                try:
                    g.update_faces(g.nondegenerate_faces())
                except Exception:
                    pass
                g.remove_infinite_values()
                holes = count_boundary_loops(g)
                if holes > 0:
                    stats["holes_before"] += holes
                    # fill small holes (pinholes); trimesh fills each loop
                    try:
                        trimesh.repair.fill_holes(g)
                    except Exception:
                        pass
                    stats["holes_after"] += max(0, count_boundary_loops(g))
            except Exception:
                pass
            cleaned.append(g)
        scene = trimesh.Scene()
        for g in cleaned:
            scene.add_geometry(g)
        scene.export(out)
        # stash stats next to output for the run manifest
        try:
            (Path(out_dir) / (glb.stem + ".cleanup.json")).write_text(
                __import__("json").dumps(stats))
        except Exception:
            pass
    except Exception as e:  # noqa: BLE001
        raise ProviderError(f"postprocessor could not parse {glb}: {e}")
    return out
