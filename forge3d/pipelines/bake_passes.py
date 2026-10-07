"""bake_passes.py — detail-map bake checklist in vanilla bpy (quality100 wave 2).

Bake Wrangler / SimplyBake proved that the extra bake passes (curvature,
cavity, thickness, ID) are the cheap detail multipliers that make generated
textures read as high-resolution. This wires that pass checklist with zero
paid tools: one headless Blender 4.2 session + numpy.

Passes (all UV-space, SIZE px):
  1. curvature — Cycles NORMAL bake -> per-texel mean-curvature magnitude
     from normal-map finite differences (numpy, fast).
  2. cavity    — concavity isolated from curvature (clamp(-div(n))).
  3. thickness — per-vertex raycast thickness via Blender's C BVH
     (ray_cast along -normal, first-hit distance, capped), rasterized
     vertex-attribute -> texture with a barycentric rasterizer.
  4. id        — per material-slot flat color, Cycles EMIT bake.

Distinct from sibling stages: normalmap.py (geometry->tangent normals),
ao_bake.py (occlusion), detail.py (texture micro-contrast). These four are
NEW passes the pipeline did not have.

Output: <stem>.curvature.png / .cavity.png / .thickness.png / .id.png
        + <stem>.bake_passes.json (per-pass mean/std/coverage).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

from ..blender.stage import run_bpy
from ..providers.base import ProviderError

_BPY = r"""
import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
INP, NORMAL_OUT, ID_OUT, THICK_NPY, SIZE, SAMPLES = (
    argv[0], argv[1], argv[2], argv[3], int(argv[4]), int(argv[5]))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INP)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
if not objs:
    print("PASSES_FATAL: no mesh"); sys.exit(1)
ob = objs[0]
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
mesh = ob.data

# ---- per-vertex thickness via BVH raycast (along -normal) ----
dg = bpy.context.evaluated_depsgraph_get()
eval_ob = ob.evaluated_get(dg)
mworld = ob.matrix_world
n_verts = len(mesh.vertices)
thick = np.zeros(n_verts, dtype=np.float32)
import mathutils
for i, v in enumerate(mesh.vertices):
    co = mworld @ v.co
    n = (mworld.to_3x3() @ v.normal).normalized()
    origin = co - n * 0.002
    hit, loc, _nrm, _idx = eval_ob.ray_cast(origin, -n)
    if hit:
        thick[i] = (loc - co).length
    else:
        thick[i] = -1.0  # no hit -> capped later
np.save(THICK_NPY, thick)
finite = thick[thick >= 0]
cap = float(np.percentile(finite, 99)) if len(finite) else 1.0
print(f"PASSES_THICK cap={cap:.4f} hit_rate={len(finite)/n_verts:.3f}")

# ---- bake targets ----
def _bake_target(name):
    img = bpy.data.images.new(name, width=SIZE, height=SIZE, alpha=False)
    img.file_format = 'PNG'
    return img

# ---- 1. NORMAL bake (curvature/cavity derive from this) ----
nimg = _bake_target("forge3d_normal")
mat = ob.data.materials[0] if ob.data.materials else None
if mat is None:
    mat = bpy.data.materials.new("forge3d_pass_mat")
    mat.use_nodes = True
    ob.data.materials.append(mat)
nt = mat.node_tree
bakenode = nt.nodes.new("ShaderNodeTexImage")
bakenode.image = nimg
nt.nodes.active = bakenode

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.render.bake.margin = 8
bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT')
nimg.save_render(NORMAL_OUT)
print("PASSES_OK normal " + NORMAL_OUT)

# ---- 2. ID bake: flat emission color per material slot ----
import colorsys
iimg = _bake_target("forge3d_id")
for si, slot in enumerate(ob.material_slots):
    m = bpy.data.materials.new(f"forge3d_id_{si}")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    r, g, b = colorsys.hsv_to_rgb((si * 0.61803398875) % 1.0, 0.9, 1.0)
    emit.inputs["Color"].default_value = (r, g, b, 1.0)
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    inode = nodes.new("ShaderNodeTexImage")
    inode.image = iimg
    nodes.active = inode
    slot.material = m
bpy.ops.object.bake(type='EMIT')
iimg.save_render(ID_OUT)
print("PASSES_OK id " + ID_OUT)
"""


def _rasterize_vertex_attr(verts, faces, uvs, attr, size):
    """Barycentric rasterization of a per-vertex float attribute -> texture."""
    out = np.zeros((size, size), dtype=np.float32)
    wsum = np.zeros((size, size), dtype=np.float32)
    uv_px = uvs * size
    fuv = uv_px[faces]
    fa = attr[faces]
    for s in range(0, len(faces), 8192):
        e = min(s + 8192, len(faces))
        tri = fuv[s:e]
        x0, y0 = tri[:, 0, 0], tri[:, 0, 1]
        x1, y1 = tri[:, 1, 0], tri[:, 1, 1]
        x2, y2 = tri[:, 2, 0], tri[:, 2, 1]
        xmin = np.clip(np.floor(tri[:, :, 0].min(1)).astype(int), 0, size - 1)
        xmax = np.clip(np.ceil(tri[:, :, 0].max(1)).astype(int), 0, size - 1)
        ymin = np.clip(np.floor(tri[:, :, 1].min(1)).astype(int), 0, size - 1)
        ymax = np.clip(np.ceil(tri[:, :, 1].max(1)).astype(int), 0, size - 1)
        ok = (xmax > xmin) & (ymax > ymin)
        for j in np.nonzero(ok)[0]:
            xs = np.arange(xmin[j], xmax[j] + 1)
            ys = np.arange(ymin[j], ymax[j] + 1)
            xx, yy = np.meshgrid(xs, ys)
            px, py = xx.ravel() + 0.5, yy.ravel() + 0.5
            ax, ay = x0[j], y0[j]
            d = (y1[j] - y2[j]) * (ax - x2[j]) + (x2[j] - x1[j]) * (ay - y2[j])
            if abs(d) < 1e-12:
                continue
            w0 = ((y1[j] - y2[j]) * (px - x2[j]) + (x2[j] - x1[j]) * (py - y2[j])) / d
            w1 = ((y2[j] - ay) * (px - x2[j]) + (ax - x2[j]) * (py - y2[j])) / d
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not np.any(inside):
                continue
            vals = w0[inside] * fa[s + j, 0] + w1[inside] * fa[s + j, 1] + w2[inside] * fa[s + j, 2]
            xi = px[inside].astype(int)
            yi = py[inside].astype(int)
            np.add.at(out, (yi, xi), vals)
            np.add.at(wsum, (yi, xi), 1.0)
    out[wsum > 0] /= wsum[wsum > 0]
    return out, wsum > 0


def _curvature_cavity(normal_png: Path):
    """Mean-curvature magnitude + concavity from a tangent-space normal map."""
    n = np.asarray(Image.open(normal_png).convert("RGB"), dtype=np.float32) / 255.0
    n = n * 2.0 - 1.0
    # screen-space derivatives of the normal field
    dnx = np.gradient(n[..., 0], axis=1)
    dny = np.gradient(n[..., 1], axis=0)
    dnzx = np.gradient(n[..., 2], axis=1)
    dnzy = np.gradient(n[..., 2], axis=0)
    curve = np.sqrt(dnx ** 2 + dny ** 2 + dnzx ** 2 + dnzy ** 2)
    # concavity: where normals converge -> negative divergence of (nx, ny)
    div = dnx + dny
    cavity = np.clip(-div, 0, None)
    return curve, cavity


def _stats(a: np.ndarray, mask: np.ndarray) -> dict:
    v = a[mask]
    if v.size == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "coverage": 0.0}
    return {"mean": round(float(v.mean()), 4), "std": round(float(v.std()), 4),
            "min": round(float(v.min()), 4), "max": round(float(v.max()), 4),
            "coverage": round(float(mask.mean()), 4)}


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        size: int = 1024, samples: int = 8) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = glb_path.stem
    normal_png = out_dir / f"{stem}.bake-normal.png"
    id_png = out_dir / f"{stem}.id.png"
    thick_npy = out_dir / f"{stem}.thickness_raw.npy"

    try:
        run_bpy(_BPY, str(glb_path), str(normal_png), str(id_png),
                str(thick_npy), str(size), str(samples), timeout=1800)
    except ProviderError as e:
        raise ProviderError(f"bake_passes failed: {e}") from e
    for p in (normal_png, id_png, thick_npy):
        if not p.exists():
            raise ProviderError(f"bake_passes: blender did not produce {p}")

    # curvature + cavity from the normal bake
    curve, cavity = _curvature_cavity(normal_png)
    curve_n = curve / max(curve.max(), 1e-9)
    cavity_n = cavity / max(cavity.max(), 1e-9)
    curve_png = out_dir / f"{stem}.curvature.png"
    cavity_png = out_dir / f"{stem}.cavity.png"
    Image.fromarray((curve_n * 255).astype(np.uint8)).save(curve_png)
    Image.fromarray((cavity_n * 255).astype(np.uint8)).save(cavity_png)

    # thickness: cap no-hits, rasterize vertex attr -> texture
    scene = trimesh.load(str(glb_path), force="scene")
    m = list(scene.geometry.values())[0]
    verts = np.asarray(m.vertices, dtype=np.float64)
    faces = np.asarray(m.faces, dtype=np.int64)
    uvs = np.asarray(m.visual.uv, dtype=np.float64)
    thick = np.load(str(thick_npy)).astype(np.float64)
    finite = thick[thick >= 0]
    cap = float(np.percentile(finite, 99)) if finite.size else 1.0
    thick[thick < 0] = cap
    thick = np.clip(thick, 0, cap) / cap
    thick_tex, tmask = _rasterize_vertex_attr(verts, faces, uvs, thick, size)
    thick_png = out_dir / f"{stem}.thickness.png"
    Image.fromarray((thick_tex * 255).astype(np.uint8)).save(thick_png)

    nmask = None
    try:
        nimg = np.asarray(Image.open(normal_png).convert("RGB"), dtype=np.float32)
        nmask = (nimg.mean(-1) > 2)
    except Exception:
        nmask = np.ones((size, size), bool)

    metrics = {
        "input": str(glb_path),
        "size": size, "samples": samples,
        "thickness_cap_world": round(cap, 4),
        "thickness_hit_rate": round(float((np.load(str(thick_npy)) >= 0).mean()), 4),
        "curvature": _stats(curve_n, nmask),
        "cavity": _stats(cavity_n, nmask),
        "thickness": _stats(thick_tex, tmask),
        "outputs": [str(curve_png), str(cavity_png), str(thick_png), str(id_png)],
        "seconds": round(time.time() - t0, 1),
    }
    out_json = out_dir / f"{stem}.bake_passes.json"
    out_json.write_text(json.dumps(metrics, indent=2))
    return metrics


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: bake_passes.py <in.glb> <out_dir> [size]", file=sys.stderr)
        sys.exit(2)
    size = int(sys.argv[3]) if len(sys.argv) == 4 else 1024
    print(json.dumps(run(sys.argv[1], sys.argv[2], size=size), indent=2))


if __name__ == "__main__":
    main()
