"""remesh.py — remesh shootout: voxel remesh vs bmesh cleanup.

Two contenders, same input mesh, measured on faces / watertight / seconds:
  voxel   — Blender REMESH modifier (VOXEL mode): full volumetric rebuild.
            Produces a clean, watertight, evenly-tessellated mesh at the
            cost of detail smoothing and face-count growth/shrinkage.
  cleanup — Blender bmesh ops: merge-by-distance, delete loose,
            degenerate dissolve, recalc normals. Topology-preserving
            repair: keeps the original surface, only fixes defects.

Both run in the vendored headless Blender so UVs/materials survive via
glTF round-trip. Watertightness is measured with trimesh (is_watertight)
on the exported GLB.

Output: <stem>.remesh-voxel.glb / <stem>.remesh-cleanup.glb + JSON report.
See docs/REMESH_SHOOTOUT.md for the judged winner.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import trimesh
import numpy as np

from ..providers.base import ProviderError

VENDOR_BLENDER = Path(
    "/home/hatch/workspace/forge3d/_vendor/blender-4.2.4-linux-x64/blender")

_VOXEL_SCRIPT = r"""
import bpy
in_path, out_path, voxel = sys.argv[-3], sys.argv[-2], float(sys.argv[-1])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=in_path)
for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    mod = ob.modifiers.new("forge3d_voxel", 'REMESH')
    mod.mode = 'VOXEL'  # Blender 4.2 enum is VOXEL, not VOXELS
    mod.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False)
bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')
print("REMESH_OK", flush=True)
"""

_CLEANUP_SCRIPT = r"""
import bpy, bmesh
in_path, out_path, merge_dist = sys.argv[-3], sys.argv[-2], float(sys.argv[-1])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=in_path)
for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_dist)  # weld
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces],
                     context='VERTS')                             # loose verts
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces],
                     context='EDGES')                             # loose edges
    bmesh.ops.dissolve_degenerate(bm, dist=merge_dist)            # degenerate
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)              # winding
    bm.to_mesh(me)
    bm.free()
    me.update()
bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')
print("REMESH_OK", flush=True)
"""


def _watertight_trimesh(glb: Path, out: Path) -> dict:
    """Stitch + close a patch-soup mesh (pure trimesh, UV-safe, no Blender).

    Raw trellis output is ~1,400 disconnected shells with exact-duplicate
    vertices at patch joints. This welds exact duplicates (position+uv+normal,
    so UV seams stay split correctly), drops tiny debris components, and
    fills holes. Returns stats dict; watertight is reported honestly —
    sub-pixel pinholes may remain on pathological inputs.
    """
    from trimesh.graph import connected_components
    t0 = time.time()
    scene = trimesh.load(glb, force="scene")
    geoms = [g for g in scene.geometry.values()
             if isinstance(g, trimesh.Trimesh)]
    if not geoms:
        raise ProviderError("watertight: no mesh geometry found")
    g = max(geoms, key=lambda x: len(x.faces))
    before_faces = len(g.faces)
    e0 = g.edges_sorted
    _, c0 = np.unique(e0, axis=0, return_counts=True)
    before_boundary = int((c0 == 1).sum())

    m = g.copy()
    m.merge_vertices(merge_tex=True, merge_norm=True)  # exact weld, UV-safe
    comp = connected_components(m.face_adjacency,
                                nodes=np.arange(len(m.faces)))
    big = [c for c in comp if len(c) >= 100]
    if big:
        keep = np.concatenate(big)
        m = trimesh.Trimesh(vertices=m.vertices, faces=m.faces[keep],
                            vertex_normals=m.vertex_normals,
                            visual=m.visual, process=True)
        m.remove_unreferenced_vertices()
    trimesh.repair.fill_holes(m)
    # re-weld after fill (fill can duplicate boundary verts)
    m.merge_vertices(merge_tex=True, merge_norm=True)

    e1 = m.edges_sorted
    _, c1 = np.unique(e1, axis=0, return_counts=True)
    after_boundary = int((c1 == 1).sum())
    nonmanifold = int((c1 > 2).sum())
    watertight = bool(m.is_watertight)

    # export: merge_vertices already kept visual (uv + material) consistent,
    # so the scene export carries textures through.
    out_scene = trimesh.Scene()
    out_scene.add_geometry(m, geom_name="mesh")
    out_scene.export(out)
    secs = time.time() - t0
    stats = {"mode": "watertight", "seconds": round(secs, 1),
             "faces_before": before_faces, "faces_after": len(m.faces),
             "boundary_before": before_boundary,
             "boundary_after": after_boundary,
             "nonmanifold_edges": nonmanifold,
             "watertight": watertight}
    print(f"watertight[trimesh]: {before_faces}f -> {len(m.faces)}f, "
          f"boundary {before_boundary} -> {after_boundary}, "
          f"watertight={watertight}, {secs:.1f}s", file=sys.stderr)
    return stats


def _run_blender(script: str, args: list[str], timeout: int = 1200):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("import sys\n" + script)
        spath = f.name
    proc = subprocess.run([str(VENDOR_BLENDER), "-b", "--python", spath,
                           "--", *args],
                          capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0 or "REMESH_OK" not in proc.stdout:
        tail = (proc.stdout + proc.stderr)[-1500:]
        raise ProviderError(f"blender remesh failed: {tail}")


def _measure(path: Path) -> dict:
    scene = trimesh.load(str(path), force="scene")
    v = f = 0
    watertight = True
    for geom in scene.geometry.values():
        if isinstance(geom, trimesh.Trimesh):
            v += len(geom.vertices)
            f += len(geom.faces)
            watertight = watertight and bool(geom.is_watertight)
    return {"vertices": v, "faces": f, "watertight": watertight,
            "bytes": path.stat().st_size}


def remesh(glb: Path, out_dir: Path, mode: str,
           voxel_size: float = 0.02, merge_dist: float = 1e-4) -> tuple[Path, dict]:
    """Run one remesh contender. Returns (out_glb, stats)."""
    if mode not in ("voxel", "cleanup", "watertight"):
        raise ProviderError(f"unknown remesh mode: {mode}")
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{glb.stem}.remesh-{mode}.glb"

    before = _measure(glb)
    t0 = time.time()
    if mode == "watertight":
        # pure-trimesh stitch+close (UV-safe); stats printed inside
        stats = _watertight_trimesh(glb, out)
        stats["before"] = before
        stats["after"] = _measure(out)
        return out, stats
    if mode == "voxel":
        _run_blender(_VOXEL_SCRIPT,
                     [str(glb), str(out), str(voxel_size)])
    else:
        _run_blender(_CLEANUP_SCRIPT,
                     [str(glb), str(out), str(merge_dist)])
    secs = time.time() - t0
    after = _measure(out)
    stats = {"mode": mode, "seconds": round(secs, 1),
             "before": before, "after": after}
    print(f"remesh[{mode}]: {before['faces']}f -> {after['faces']}f, "
          f"watertight={after['watertight']}, {secs:.1f}s", file=sys.stderr)
    return out, stats


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mode", required=True, choices=["voxel", "cleanup", "watertight"])
    ap.add_argument("--voxel-size", type=float, default=0.02)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    out, stats = remesh(Path(a.input), Path(a.outdir), a.mode,
                        voxel_size=a.voxel_size)
    print(out)
    if a.report:
        Path(a.report).write_text(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
