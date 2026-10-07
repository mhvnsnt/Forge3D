"""Blendshape stage — bake semantic body morphs into Blender shape keys.

Takes the authored deformation fields from forge3d.body.morphs (region-mask
based, no statistical model) and bakes each one as a real Blender SHAPE KEY
on the mesh, so morphs ride the model as blendshapes and export to glTF as
morph targets. The morph code runs INSIDE Blender (imported, not duplicated).

Pipeline order stays: generate -> morph(keys) -> rig. Baking keys on the
unrigged mesh keeps them compatible with later skinning.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from ..providers.base import ProviderError
from .stage import REPO, run_bpy


def bake_shape_keys(in_glb: Path, morph_spec: dict, out_glb: Path,
                    key_prefix: str = "morph_", timeout: int = 1200) -> Path:
    """Bake morphs.py deformations into shape keys. morph_spec: {name: value}.

    Each morph becomes one shape key (Basis + key per morph). Exports GLB;
    validates the export really carries len(spec) morph targets.
    """
    in_glb, out_glb = Path(in_glb), Path(out_glb)
    out_glb.parent.mkdir(parents=True, exist_ok=True)
    if not morph_spec:
        raise ProviderError("bake_shape_keys: empty morph_spec")
    script = """
import bpy, sys, math
argv = sys.argv[sys.argv.index("--") + 1:]
INP, OUTP = argv[0], argv[1]
import json as _j
SPEC = _j.loads(argv[2]); PREFIX = argv[3]
sys.path.insert(0, %r)
import numpy as np
from forge3d.body import morphs as M

bad = [k for k in SPEC if k not in M.MORPHS]
if bad:
    print("[shapekeys] FATAL: unknown morphs", bad); sys.exit(1)

bpy.ops.wm.read_factory_settings(use_empty=True)
# factory "empty" is not guaranteed empty in every build (seen: a default
# Icosphere survives) — purge every object before import so stray factory
# geometry can never join the bake or leak into the export.
for _o in list(bpy.data.objects):
    bpy.data.objects.remove(_o, do_unlink=True)
bpy.ops.import_scene.gltf(filepath=INP)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
if not meshes:
    print("[shapekeys] FATAL: no mesh in", INP); sys.exit(1)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
OBJ = bpy.context.view_layer.objects.active
bpy.context.view_layer.objects.active = OBJ

n = len(OBJ.data.vertices)
base = np.empty(n * 3, dtype=np.float64)
OBJ.data.vertices.foreach_get("co", base)
base = base.reshape(n, 3)
print(f"[shapekeys] base verts={n}")

made = []
for name, val in SPEC.items():
    V = base.copy()
    masks = M.region_masks(V)
    M.MORPHS[name][1](V, masks, float(val))
    if not OBJ.data.shape_keys:
        OBJ.shape_key_add(name="Basis", from_mix=False)
    sk = OBJ.shape_key_add(name=PREFIX + name, from_mix=False)
    try:
        sk.data.foreach_set("co", V.reshape(-1))
    except Exception:
        for i, co in enumerate(V):
            sk.data[i].co = co
    sk.value = 0.0
    delta = np.abs(V - base).max()
    made.append(sk.name)
    print(f"[shapekeys] key '{sk.name}' baked, max delta={delta:.4f}")
    OBJ.data.update()

bpy.ops.export_scene.gltf(filepath=OUTP, export_format='GLB')
print("[shapekeys] exported", OUTP, "keys:", made)
""" % str(REPO)
    import json as _json
    run_bpy(script, str(in_glb), str(out_glb), _json.dumps(morph_spec),
            key_prefix, timeout=timeout)
    # validate the export carries real morph targets
    data = out_glb.read_bytes()
    if data[:4] != b"glTF":
        raise ProviderError(f"shapekeys: {out_glb.name} is not a GLB")
    ln = struct.unpack("<I", data[12:16])[0]
    js = json.loads(data[20:20 + ln])
    targets = []
    names = []
    for m in js.get("meshes", []):
        for p in m.get("primitives", []):
            targets.extend(p.get("targets", []))
        names.extend(((m.get("extras") or {}).get("targetNames") or []))
    if len(targets) < len(morph_spec):
        raise ProviderError(
            f"shapekeys: expected >={len(morph_spec)} morph targets, "
            f"found {len(targets)} in {out_glb.name}")
    print(f"shapekeys: {out_glb.name} carries {len(targets)} morph targets "
          f"{names}")
    return out_glb
