"""retexture.py — clean UV re-unwrap + texture rebake stage.

Problem (2026-10-07, trellis2-concept2-high): raw trellis output packs
HUNDREDS of tiny UV islands (one per mesh patch, ~1,400 patches) with black
gaps between them. At render resolution the seams read as speckle/noise, and
no amount of bleed-dilation fixes the fundamental fragmentation.

Fix: re-unwrap the mesh with Blender's smart UV project (clean, large
islands) and rebake the original albedo onto the new UVs (Cycles diffuse
bake, selected-to-active). The rebaked texture has an order of magnitude
fewer seams.

Output: <stem>.retexture.glb + JSON report (island count before/after).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ..blender.stage import run_bpy
from ..providers.base import ProviderError

_BPY_SCRIPT = r'''
import bpy, json, sys

in_glb, out_glb, tex_size, report_json = sys.argv[-4:]
tex_size = int(tex_size)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=in_glb)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not meshes:
    print("RETEXTURE_FAIL: no meshes imported", flush=True)
    sys.exit(2)
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
src = bpy.context.view_layer.objects.active
src.name = "SRC"

# duplicate for re-unwrap target (original kept as bake source)
bpy.ops.object.duplicate()
dst = bpy.context.view_layer.objects.active
dst.name = "DST"

# count source UV islands (approx: disconnected UV face groups via seams)
# -- we report island count from the bake source via a simple flood fill on
#    UV edge connectivity below in python (after export); here just unwrap.
bpy.ops.object.select_all(action="DESELECT")
dst.select_set(True)
bpy.context.view_layer.objects.active = dst
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
# drop old UVs, smart-project clean ones
uvlayers = dst.data.uv_layers
while uvlayers:
    uvlayers.remove(uvlayers[0])
bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

# bake original base color onto the new UVs
baked = False
bake_note = "no bake attempted"
try:
    src_mats = [m for m in src.data.materials if m and m.use_nodes]
    if src_mats:
        # DST must have its OWN material copy (it shares SRC's datablock after
        # duplicate(); adding the bake node to the shared mat would corrupt
        # the bake SOURCE).
        mat = dst.data.materials[0] if dst.data.materials else None
        if mat is None:
            mat = bpy.data.materials.new("RebakedMat")
            mat.use_nodes = True
        else:
            mat = mat.copy()
        dst.data.materials.clear()
        dst.data.materials.append(mat)
        nodes = mat.node_tree.nodes
        img = bpy.data.images.new("RebakedTex", width=tex_size, height=tex_size)
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        tex_node.select = True
        nodes.active = tex_node
        bpy.ops.object.select_all(action="DESELECT")
        src.select_set(True)
        dst.select_set(True)
        bpy.context.view_layer.objects.active = dst
        bpy.context.scene.render.engine = "CYCLES"
        cyc = bpy.context.scene.cycles
        cyc.samples = 8
        cyc.device = "CPU"
        bpy.context.scene.render.bake.use_selected_to_active = True
        bpy.context.scene.render.bake.cage_extrusion = 0.02
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"},
                            use_selected_to_active=True)
        img.filepath_raw = out_glb + ".rebaked.png"
        img.file_format = "PNG"
        img.save()
        # wire the baked image as the material's base color
        bsdf = None
        for n in nodes:
            if n.type == "BSDF_PRINCIPLED":
                bsdf = n
                break
        if bsdf is not None:
            links = mat.node_tree.links
            links.new(tex_node.outputs["Color"],
                      bsdf.inputs["Base Color"])
        baked = True
        bake_note = f"diffuse baked {tex_size}px"
    else:
        bake_note = "source had no node materials; skipped"
except Exception as e:  # noqa: BLE001
    bake_note = f"bake failed: {e}"
    print(f"RETEXTURE_FAIL: bake: {e}", flush=True)
    sys.exit(3)

# export re-unwrapped object only
bpy.ops.object.select_all(action="DESELECT")
dst.select_set(True)
bpy.context.view_layer.objects.active = dst
bpy.ops.export_scene.gltf(filepath=out_glb, export_format="GLB",
                          use_selection=True)

# count UV islands on result: flood fill over faces that share a UV-space edge
# (two faces are in the same island if they share a mesh edge whose two
# endpoint UVs match on both faces)
me = dst.data
uv = me.uv_layers[0].data
loop_uv = [(me.loops[li].vertex_index, tuple(round(c, 4) for c in uv[li].uv))
           for poly in me.polygons for li in poly.loop_indices]
# map mesh edge -> list of (face, uv0, uv1)
from collections import defaultdict
edge_faces = defaultdict(list)
li_iter = iter(range(len(loop_uv)))
face_loop_start = 0
for poly in me.polygons:
    n = len(poly.loop_indices)
    for k in range(n):
        a = loop_uv[face_loop_start + k]
        b = loop_uv[face_loop_start + (k + 1) % n]
        key = tuple(sorted((a[0], b[0])))  # mesh-edge by vertex pair
        edge_faces[key].append((poly.index, a[1], b[1]))
    face_loop_start += n
parent = {p.index: p.index for p in me.polygons}
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
for key, lst in edge_faces.items():
    # group faces sharing this edge whose UVs agree (same island side)
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            fi, uvi0, uvi1 = lst[i]
            fj, uvj0, uvj1 = lst[j]
            if (uvi0 == uvj0 and uvi1 == uvj1) or (uvi0 == uvj1 and uvi1 == uvj0):
                ri, rj = find(fi), find(fj)
                if ri != rj:
                    parent[ri] = rj
roots = {find(p.index) for p in me.polygons}
report = {"baked": baked, "bake_note": bake_note,
          "uv_islands_after": len(roots),
          "tex_size": tex_size}
with open(report_json, "w") as f:
    json.dump(report, f)
print("RETEXTURE_REPORT:" + json.dumps(report), flush=True)
print("RETEXTURE_OK", flush=True)
'''


def retexture_glb(glb: Path, out_dir: Path,
                  tex_size: int = 1024) -> tuple[Path, dict]:
    """Re-unwrap + rebake. Returns (out_glb, report). Raises ProviderError."""
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{glb.stem}.retexture.glb"
    report_p = out_dir / f"{glb.stem}.retexture.json"
    t0 = time.time()
    try:
        stdout = run_bpy(_BPY_SCRIPT, str(glb), str(out),
                         str(tex_size), str(report_p))
    except ProviderError as e:
        raise ProviderError(f"retexture failed: {e}") from e
    secs = time.time() - t0
    report = json.loads(report_p.read_text())
    report["seconds"] = round(secs, 1)
    report["output"] = out.name
    if not report.get("baked"):
        raise ProviderError(
            f"retexture: bake did not complete: {report.get('bake_note')}")
    # quality gate: the rebaked PNG must actually contain baked content —
    # a mostly-black bake means the rays missed (bad cage/UVs), and shipping
    # it would be worse than the original texture.
    rebaked_png = Path(str(out) + ".rebaked.png")
    if rebaked_png.exists():
        from PIL import Image
        import numpy as np
        a = np.array(Image.open(rebaked_png).convert("RGB"))
        nonblack = float((a.max(axis=2) > 12).mean())
        report["nonblack_frac"] = round(nonblack, 3)
        if nonblack < 0.5:
            raise ProviderError(
                f"retexture: bake quality gate failed "
                f"(non-black frac {nonblack:.2f} < 0.50) — rays missed; "
                f"not shipping a black texture")
    report_p.write_text(json.dumps(report, indent=2))
    print(f"retexture: islands -> {report.get('uv_islands_after')}, "
          f"{secs:.1f}s", file=sys.stderr)
    return out, report


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tex-size", type=int, default=1024)
    a = ap.parse_args()
    out, rep = retexture_glb(Path(a.input), Path(a.outdir), a.tex_size)
    print("WROTE:", out)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
