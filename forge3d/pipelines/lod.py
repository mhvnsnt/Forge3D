"""lod.py — build LOD0/1/2 GLBs from a source model.

PORTED from Bannon's tools/generative/mesh/lod_chain.py
(mhvnsnt/Bannon repo, proprietary — same owner, ported with owner direction
2026-10-06; see LICENSES.md / docs/PROVENANCE.md). Structural port of the
original with one Forge3D extension: a headless-Blender decimate backend so
LOD generation works with zero pip installs (open3d/fast-simplification are
not installed on the free runner).

Decimation backends (tried in order, first available wins):
  1. open3d (MIT) quadric decimation — best quality
  2. fast-simplification (pip install fast-simplification) via trimesh
  3. blender-decimate (Forge3D extension, always available): vendored
     headless Blender applies a COLLAPSE decimate modifier per ratio,
     preserving UVs/materials. Louder/slower than quadric but honest.

If none is installed the stage exits with install instructions rather than
producing a bad LOD. Never silently ships a broken decimation.

Output: <base>_LOD0.glb / _LOD1.glb / _LOD2.glb + a face-count table
printed and written to lod-report.json.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

VENDOR_BLENDER = Path(
    "/home/hatch/workspace/forge3d/_vendor/blender-4.2.4-linux-x64/blender")


def _decimate_open3d(mesh, target_faces):
    import open3d as o3d
    om = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(np.asarray(mesh.vertices)),
        o3d.utility.Vector3iVector(np.asarray(mesh.faces)))
    om = om.simplify_quadric_decimation(max(int(target_faces), 4))
    om.remove_duplicated_vertices()
    om.remove_degenerate_triangles()
    om.remove_unreferenced_vertices()
    v = np.asarray(om.vertices)
    f = np.asarray(om.triangles)
    out = trimesh.Trimesh(vertices=v, faces=f, process=True)
    out.visual = mesh.visual
    return out


def _decimate_fast_simplification(mesh, target_faces):
    # note: trimesh's wrapper RETURNS the simplified mesh (does not modify
    # in place) and drops visuals, so reattach them.
    out = mesh.copy().simplify_quadric_decimation(face_count=int(target_faces))
    try:
        out.visual = mesh.visual
    except Exception:
        pass
    return out


def _decimate_blender(input_path: Path, ratio: float, out_path: Path):
    """Forge3D extension: decimate via vendored headless Blender (COLLAPSE).

    Runs inside one Blender session per ratio; keeps materials/UVs intact
    because Blender exports the whole glTF, not just raw geometry.
    """
    script = f"""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath={str(input_path)!r})
for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    mod = ob.modifiers.new("forge3d_lod", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = {ratio}
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False)
bpy.ops.export_scene.gltf(filepath={str(out_path)!r}, export_format='GLB')
print("LOD_OK", flush=True)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        spath = f.name
    proc = subprocess.run([str(VENDOR_BLENDER), "-b", "--python", spath],
                          capture_output=True, text=True, timeout=1200)
    if proc.returncode != 0 or not out_path.exists() or "LOD_OK" not in proc.stdout:
        tail = (proc.stdout + proc.stderr)[-1500:]
        raise RuntimeError(f"blender decimate failed: {tail}")


def pick_backend():
    try:
        import open3d  # noqa: F401
        return "open3d", _decimate_open3d
    except ImportError:
        pass
    try:
        import fast_simplification  # noqa: F401
        return "fast-simplification", _decimate_fast_simplification
    except ImportError:
        pass
    if VENDOR_BLENDER.exists():
        return "blender-decimate", None
    return None, None


def _count_faces(path: Path) -> tuple[int, int]:
    scene = trimesh.load(str(path), force="scene")
    v = f = 0
    for geom in scene.geometry.values():
        if isinstance(geom, trimesh.Trimesh):
            v += len(geom.vertices)
            f += len(geom.faces)
    return v, f


def build_lods(input_path: Path, outdir: Path,
               ratios=(1.0, 0.5, 0.25)) -> list[dict]:
    name, backend = pick_backend()
    if name is None:
        sys.exit("no decimation backend: pip install open3d  (MIT, recommended)\n"
                 "  or: pip install fast-simplification\n"
                 "  or: use the vendored Blender backend (missing _vendor)")
    print(f"LOD backend: {name}", file=sys.stderr)
    input_path = Path(input_path)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    base = input_path.stem

    results = []
    if name == "blender-decimate":
        for i, r in enumerate(ratios):
            p = outdir / f"{base}_LOD{i}.glb"
            if r >= 1.0:
                shutil.copy(input_path, p)
            else:
                _decimate_blender(input_path, r, p)
            v, f = _count_faces(p)
            results.append({"lod": i, "ratio": r, "backend": name,
                            "vertices": v, "faces": f, "path": str(p)})
            print(f"LOD{i} (ratio {r}): {v}v / {f}f -> {p.name}",
                  file=sys.stderr)
    else:
        scene = trimesh.load(str(input_path), force="scene")
        for i, r in enumerate(ratios):
            out = trimesh.Scene()
            total_in, total_out = 0, 0
            for node_name in scene.graph.nodes_geometry:
                transform, geom_name = scene.graph[node_name]
                geom = scene.geometry[geom_name]
                if not isinstance(geom, trimesh.Trimesh):
                    out.add_geometry(geom, geom_name=node_name,
                                     transform=transform)
                    continue
                total_in += len(geom.faces)
                g = geom if r >= 1.0 else backend(geom, len(geom.faces) * r)
                total_out += len(g.faces)
                out.add_geometry(g, geom_name=node_name, transform=transform)
            p = outdir / f"{base}_LOD{i}.glb"
            out.export(str(p))
            v, f = _count_faces(p)
            results.append({"lod": i, "ratio": r, "backend": name,
                            "faces_in": total_in, "faces_out": total_out,
                            "vertices": v, "faces": f, "path": str(p)})
            print(f"LOD{i}: {total_in} -> {total_out} faces -> {p.name}",
                  file=sys.stderr)
    return results


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--ratios", default="1.0,0.5,0.25")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    ratios = [float(x) for x in a.ratios.split(",")]
    results = build_lods(Path(a.input), Path(a.outdir), ratios)
    print("\nLOD face-count table")
    print(f"{'LOD':<5}{'ratio':<8}{'verts':<10}{'faces':<10}file")
    for r in results:
        print(f"{r['lod']:<5}{r['ratio']:<8}{r['vertices']:<10}"
              f"{r['faces']:<10}{Path(r['path']).name}")
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
