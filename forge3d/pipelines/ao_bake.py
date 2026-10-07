"""ao_bake.py — ambient occlusion bake via headless Blender Cycles.

Closes the NATIVE DETAIL gap from the lighting side: baked AO adds the
contact-shadow depth that makes generated characters read as solid instead
of flat. Attached as glTF occlusionTexture (R channel) on materials that
lack one.

Distinct from sibling stages: normalmap.py (geometry normals), detail.py
(texture micro-detail), speckle.py (seam bleed). This is pure occlusion.

Output: <stem>.ao.glb + <stem>.ao.png + <stem>.ao.json.
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

from PIL import Image

from ..blender.stage import run_bpy
from ..providers.base import ProviderError
from .glbutil import append_images, parse_glb, write_glb

_BPY = r"""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
INP, IMG_OUT, SIZE, SAMPLES = argv[0], argv[1], int(argv[2]), int(argv[3])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INP)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
if not objs:
    print("AO_FATAL: no mesh"); sys.exit(1)
ob = objs[0]
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob

# AO bake target image
img = bpy.data.images.new("forge3d_ao", width=SIZE, height=SIZE, alpha=False)
img.file_format = 'PNG'
# ensure the active material has an image node pointing at our bake target
mat = ob.data.materials[0] if ob.data.materials else None
if mat is None:
    mat = bpy.data.materials.new("forge3d_ao_mat")
    mat.use_nodes = True
    ob.data.materials.append(mat)
nt = mat.node_tree
bakenode = nt.nodes.new("ShaderNodeTexImage")
bakenode.image = img
nt.nodes.active = bakenode

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.render.bake.margin = 8
bpy.ops.object.bake(type='AO')
img.save_render(IMG_OUT)
print("AO_OK " + IMG_OUT)
"""


def run(glb_path: str | Path, out_dir: str | Path | None = None,
        size: int = 1024, samples: int = 24) -> dict:
    t0 = time.time()
    glb_path = Path(glb_path)
    out_dir = Path(out_dir) if out_dir else glb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = glb_path.stem
    ao_png = out_dir / f"{stem}.ao.png"

    try:
        out = run_bpy(_BPY, str(glb_path), str(ao_png), str(size),
                      str(samples), timeout=1200)
    except ProviderError as e:
        raise ProviderError(f"ao_bake failed: {e}") from e
    if "AO_OK" not in out or not ao_png.exists():
        raise ProviderError(f"ao_bake: blender did not produce {ao_png}")

    # quality gate: AO map must have real variance (not flat white/black)
    a = Image.open(ao_png).convert("L")
    import numpy as np
    arr = np.asarray(a, dtype=np.float32)
    std = float(arr.std())
    mean = float(arr.mean())
    if std < 4.0:
        raise ProviderError(
            f"ao_bake: quality gate failed (std {std:.1f} < 4.0) — bake is flat")

    # attach as occlusionTexture where missing
    doc, blob = parse_glb(glb_path)
    payload = ao_png.read_bytes()
    doc, new_blob, (img_idx,) = append_images(
        doc, blob, [(payload, "image/png")])
    if "textures" not in doc:
        doc["textures"] = []
    doc["textures"].append({"source": img_idx, "name": "forge3d_ao"})
    tex_idx = len(doc["textures"]) - 1
    attached = 0
    for mat in doc.get("materials", []):
        if "occlusionTexture" not in mat:
            mat["occlusionTexture"] = {"index": tex_idx, "texCoord": 0,
                                       "strength": 1.0}
            attached += 1

    out_glb = out_dir / f"{stem}.ao.glb"
    write_glb(doc, new_blob, out_glb)
    report = {"input": str(glb_path), "stage": "ao-bake",
              "size": size, "samples": samples,
              "ao_mean": round(mean, 1), "ao_std": round(std, 1),
              "occlusion_attached_to": attached,
              "ao_png": str(ao_png), "output": str(out_glb),
              "total_seconds": round(time.time() - t0, 1)}
    (out_dir / f"{stem}.ao.json").write_text(json.dumps(report, indent=2))
    return report


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m forge3d.pipelines.ao_bake <in.glb> [outdir]")
        return 2
    print(json.dumps(run(argv[1], argv[2] if len(argv) > 2 else None),
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
