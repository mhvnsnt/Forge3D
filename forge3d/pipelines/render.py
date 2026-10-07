"""render.py — headless Blender GLB renders for stage evidence.

Deterministic turntable-ish 3/4 front render (EEVEE, 3-point light rig) so
before/after comparisons across stages are apples-to-apples.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VENDOR_BLENDER = Path(
    "/home/hatch/workspace/forge3d/_vendor/blender-4.2.4-linux-x64/blender")

_RENDER_SCRIPT = r"""
import bpy, math, sys, os
from mathutils import Vector

glb_path, png_path, size = sys.argv[-4], sys.argv[-3], int(sys.argv[-2])
hdri_path = sys.argv[-1]
if hdri_path == "NONE":
    hdri_path = None

# clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
    for x in list(coll):
        coll.remove(x)

bpy.ops.import_scene.gltf(filepath=glb_path)

# bounds of imported meshes
mins = Vector((1e9,)*3); maxs = Vector((-1e9,)*3)
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        mins = Vector(map(min, mins, w)); maxs = Vector(map(max, maxs, w))
center = (mins + maxs) / 2
radius = max((maxs - mins).length, 0.001)

# camera: 3/4 front view
cam_data = bpy.data.cameras.new("evcam")
cam = bpy.data.objects.new("evcam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
dist = radius * 2.4
cam.location = center + Vector((dist*0.55, -dist*0.85, dist*0.45))
from mathutils import Euler
d = (center - cam.location)
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# 3-point lights
def add_light(name, ltype, energy, loc):
    ld = bpy.data.lights.new(name, ltype); ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    return lo
key = add_light("key", 'SUN', 4.0, center + Vector((3, -4, 5)))
fill = add_light("fill", 'SUN', 1.5, center + Vector((-4, -2, 2)))
rim = add_light("rim", 'SUN', 2.5, center + Vector((0, 5, 3)))
rim.data.color = (0.85, 0.9, 1.0)

# world: CC0 HDRI environment when provided, else neutral studio gray
world = bpy.context.scene.world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
if hdri_path and os.path.exists(hdri_path):
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputWorld")
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = 1.0
    env = nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdri_path)
    links.new(env.outputs[0], bg.inputs[0])
    links.new(bg.outputs[0], out.inputs[0])
    print("HDRI world:", hdri_path, flush=True)
else:
    bg = nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.55, 0.58, 1.0)
    bg.inputs[1].default_value = 1.0

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Blender 4.2+ name
scene.render.resolution_x = size
scene.render.resolution_y = size
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.filepath = png_path
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("rendered", png_path, flush=True)
"""


def render_glb(glb_path: Path, png_path: Path, size: int = 1024,
               hdri: Path | None = None,
               timeout: int = 600) -> Path:
    """Render a GLB to PNG with the vendored headless Blender.

    hdri: optional CC0 .hdr environment for world lighting
    (see forge3d/assets/cc0/hdris/).
    """
    if not VENDOR_BLENDER.exists():
        raise RuntimeError(f"vendored blender missing: {VENDOR_BLENDER}")
    script = Path("/tmp/forge3d_render_helper.py")
    script.write_text(_RENDER_SCRIPT)
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VENDOR_BLENDER), "-b", "--python", str(script), "--",
           str(glb_path), str(png_path), str(size),
           str(hdri) if hdri else "NONE"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0 or not png_path.exists():
        tail = (proc.stderr or "")[-2000:]
        raise RuntimeError(f"blender render failed (rc={proc.returncode}): {tail}")
    return png_path


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--hdri", default=None,
                    help="CC0 .hdr for environment lighting")
    a = ap.parse_args()
    p = render_glb(Path(a.input), Path(a.output), a.size,
                   Path(a.hdri) if a.hdri else None)
    print(p)


if __name__ == "__main__":
    main()
