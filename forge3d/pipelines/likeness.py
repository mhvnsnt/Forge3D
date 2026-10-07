"""Likeness sheet: side-by-side approval renders for the owner's eyes-on loop.

Given a reference image (portrait/concept) + a generated GLB, produces one
PNG sheet: reference | front | side | back, labeled. This is the concrete
"sucked / that was good" loop — the owner judges likeness from this sheet,
never from a bare GLB.

Rendering: headless vendored Blender 4.2, Workbench engine (CPU-safe),
3 cameras (0/90/180 deg), neutral lighting, white background.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from ..blender.stage import run_bpy
from ..providers.base import ProviderError

_RENDER_SCRIPT = """
import bpy, sys, math
argv = sys.argv[sys.argv.index("--") + 1:]
INP, OUTDIR = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INP)
ms = [o for o in bpy.data.objects if o.type == 'MESH']
if not ms:
    print("[likeness] FATAL: no mesh in", INP); sys.exit(1)

# frame the model: center + scale to ~2 units tall
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
bpy.ops.object.join()
obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = obj
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
loc = obj.location.copy(); obj.location = (0, 0, 0)
import mathutils
dims = obj.dimensions
s = 2.0 / max(dims.y, 0.001)   # glTF Y-up: height on Y
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x, scene.render.resolution_y = 512, 512
scene.render.film_transparent = False
scene.world.color = (1, 1, 1)
scene.display.shading.light = 'MATCAP'
scene.display.shading.studio_light = 'check_rim.dark.exr'

# camera on a ring, looking at origin
cam_data = bpy.data.cameras.new("likecam")
cam = bpy.data.objects.new("likecam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for ang_deg, name in [(0, "front"), (90, "side"), (180, "back")]:
    a = math.radians(ang_deg)
    r = 4.5
    cam.location = (r * math.sin(a), -r * math.cos(a), 1.2)
    d = mathutils.Vector((0, 0, 0.9)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = OUTDIR + "/" + name + ".png"
    bpy.ops.render.render(write_still=True)
print("[likeness] rendered 3 views to", OUTDIR)
"""


def render_views(glb_path: Path, out_dir: Path) -> list[Path]:
    """Render front/side/back PNGs of a GLB via headless Blender."""
    out_dir.mkdir(parents=True, exist_ok=True)
    run_bpy(_RENDER_SCRIPT, str(glb_path), str(out_dir), timeout=600)
    views = [out_dir / f"{n}.png" for n in ("front", "side", "back")]
    missing = [v for v in views if not v.exists()]
    if missing:
        raise ProviderError(f"likeness: blender did not render {missing}")
    return views


def likeness_sheet(reference: Path, glb_path: Path, out_path: Path,
                   labels: tuple[str, str, str, str] = (
                       "REFERENCE", "FRONT", "SIDE", "BACK")) -> Path:
    """Build the 4-panel approval sheet. Returns the sheet path."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        views = render_views(glb_path, Path(td))
        ref = Image.open(reference).convert("RGB")
        panels = [ref] + [Image.open(v).convert("RGB") for v in views]
        # normalize to 512px tall
        norm = []
        for p in panels:
            w, h = p.size
            nw = int(w * 512 / h)
            norm.append(p.resize((nw, 512), Image.LANCZOS))
        tw = sum(p.size[0] for p in norm)
        sheet = Image.new("RGB", (tw, 512 + 36), "white")
        d = ImageDraw.Draw(sheet)
        x = 0
        for p, lab in zip(norm, labels):
            sheet.paste(p, (x, 36))
            d.text((x + 8, 10), lab, fill="black")
            x += p.size[0]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out_path)
    return out_path
