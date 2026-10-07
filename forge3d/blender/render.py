"""Headless proof-render stage — Cycles CPU renders of pipeline outputs.

Used for stage evidence (docs/stage-evidence/): shape-key sweeps, posed
animation frames. Frames the full mesh bbox with margin (arm reach visible).
"""
from __future__ import annotations

from pathlib import Path

from ..providers.base import ProviderError
from .stage import run_bpy


def render_glb(in_glb: Path, out_png: Path, *, shape_values: dict | None = None,
               frame: int | None = None, action_name: str | None = None,
               view: tuple = (0.85, 0.30, 1.35), width: int = 768,
               height: int = 768, samples: int = 24, margin: float = 1.35,
               timeout: int = 900) -> Path:
    """Render a GLB headless.

    shape_values: {shape-key name: 0..1} applied before render.
    frame/action_name: pose an imported glTF animation at this frame.
    view: camera direction (x, y, z); camera looks at the bbox center.
    """
    in_glb, out_png = Path(in_glb), Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sv = shape_values or {}
    script = """
import bpy, sys, math
argv = sys.argv[sys.argv.index("--") + 1:]
INP, OUTP = argv[0], argv[1]
import json as _j
SV = _j.loads(argv[2]); FRAME = int(argv[3]); ACT = argv[4]
VW = float(argv[5]); VH = float(argv[6]); SAMP = int(argv[7])
MARG = float(argv[8]); VDIR = _j.loads(argv[9])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INP)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
if not meshes:
    print("[render] FATAL: no mesh in", INP); sys.exit(1)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
OBJ = bpy.context.view_layer.objects.active

# shape keys
if SV:
    kb = OBJ.data.shape_keys.key_blocks if OBJ.data.shape_keys else {}
    for name, val in SV.items():
        if name in kb:
            kb[name].value = float(val)
            print(f"[render] shape {name} = {val}")
        else:
            print(f"[render] WARN: shape key '{name}' not found")

# animation pose
if ACT and ACT != "NONE":
    act = bpy.data.actions.get(ACT)
    if act is None:
        cands = [a for a in bpy.data.actions if a.name.startswith("MOVE_")]
        act = cands[0] if cands else None
    for arm in arms:
        if act:
            if not arm.animation_data: arm.animation_data_create()
            arm.animation_data.action = act
    if FRAME >= 0:
        bpy.context.scene.frame_set(FRAME)
        bpy.context.view_layer.update()
        print(f"[render] posed {(act.name if act else None)} at frame {FRAME}")

# frame camera on bbox with margin
import mathutils
bb = [OBJ.matrix_world @ mathutils.Vector(c) for c in OBJ.bound_box]
mn = mathutils.Vector((min(v[i] for v in bb) for i in range(3)))
mx = mathutils.Vector((max(v[i] for v in bb) for i in range(3)))
center = (mn + mx) / 2
size = max((mx - mn).length, 1e-6)
d = mathutils.Vector(VDIR)
d = d / d.length
cam_data = bpy.data.cameras.new('proofcam')
cam_data.lens = 50
cam = bpy.data.objects.new('proofcam', cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
fov = 2 * math.atan(16 / cam_data.lens)  # vertical fov, 32mm sensor height
dist = (size * MARG / 2) / math.tan(fov / 2)
cam.location = center + d * dist
qv = (-d).to_track_quat('-Z', 'Y')
cam.rotation_euler = qv.to_euler()

# studio lighting: key sun + fill area + rim
sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN'))
sun.data.energy = 3.0
sun.location = center + mathutils.Vector((2.5, 1.5, 3.0))
bpy.context.collection.objects.link(sun)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'AREA'))
fill.data.energy = 60.0 * size
fill.data.size = size * 1.2
fill.location = center + mathutils.Vector((-2.5, 1.0, 2.0))
bpy.context.collection.objects.link(fill)
rim = bpy.data.objects.new('rim', bpy.data.lights.new('rim', 'SUN'))
rim.data.energy = 1.2
rim.location = center + mathutils.Vector((-1.0, 2.0, -2.5))
bpy.context.collection.objects.link(rim)
world = bpy.data.worlds.new('studioworld')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.82, 0.82, 0.84, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
bpy.context.scene.world = world

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMP
sc.render.resolution_x = int(VW); sc.render.resolution_y = int(VH)
sc.render.film_transparent = False
sc.render.filepath = OUTP
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("[render] wrote", OUTP)
"""
    import json as _json
    run_bpy(script, str(in_glb), str(out_png), _json.dumps(sv),
            str(frame if frame is not None else -1),
            action_name or "NONE", str(width), str(height), str(samples),
            str(margin), _json.dumps(list(view)), timeout=timeout)
    if not out_png.exists():
        raise ProviderError(f"render stage produced no PNG at {out_png}")
    return out_png
