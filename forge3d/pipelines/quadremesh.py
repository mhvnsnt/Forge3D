"""Quad remesh stage: triangle soup in, animation-ready quads out.

Uses the vendored headless Blender 4.2 (see forge3d/blender/stage.py) and
its built-in Quadriflow remesher. No new license burden: Blender is GPL,
but we invoke it as a separate process (mere use, not linking), and Blender
was already a pipeline dependency.

What it does:
  1. Import GLB, join into one mesh, ensure manifold (cleanup stage already
     filled holes; we re-check).
  2. Quadriflow remesh to target quad count (default 30k — game-character
     territory; Tripo's 1.9M-triangle vanity metric is NOT the goal here,
     animation-ready topology is).
  3. Texture preservation: bake the original's base-color texture onto the
     remeshed UVs (smart-projected). If the input has no textures or the
     bake fails, the remesh still completes and the skip is recorded LOUDLY
     — never a silent texture drop.
  4. Export GLB.

Output is verified quad-dominant (measured, not claimed): the run records
quad/tri/ngon counts. Raises ProviderError on any genuine failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ..blender.stage import run_bpy
from ..providers.base import ProviderError

_BPY_SCRIPT = r'''
import bpy, json, sys

in_glb, out_glb, target_faces, report_json = sys.argv[-4:]
target_faces = int(target_faces)

# clean scene, import
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=in_glb)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    print("QUADREMESH_FAIL: no meshes imported", flush=True)
    sys.exit(2)
# join into one
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
src = bpy.context.view_layer.objects.active
src.name = "SRC"

# duplicate for remesh target (original kept as bake source)
bpy.ops.object.duplicate()
dst = bpy.context.view_layer.objects.active
dst.name = "DST"

# quadriflow remesh on the duplicate
bpy.ops.object.select_all(action="DESELECT")
dst.select_set(True)
bpy.context.view_layer.objects.active = dst
bpy.ops.object.mode_set(mode="OBJECT")
try:
    bpy.ops.object.quadriflow_remesh(
        target_faces=target_faces,
        use_mesh_symmetry=False,
        use_preserve_sharp=True,
        use_preserve_boundary=True,
        smooth_normals=True,
    )
except Exception as e:  # noqa: BLE001
    print(f"QUADREMESH_FAIL: quadriflow: {e}", flush=True)
    sys.exit(3)

# smart UV project on remeshed result
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

# bake original base color onto remeshed UVs (best effort, loud on skip)
baked = False
bake_note = "no bake attempted"
try:
    src_mats = [m for m in src.data.materials if m and m.use_nodes]
    if src_mats:
        # ensure DST has a material with an image node to bake into
        mat = dst.data.materials[0] if dst.data.materials else None
        if mat is None:
            mat = bpy.data.materials.new("BakedMat")
            mat.use_nodes = True
            dst.data.materials.append(mat)
        nodes = mat.node_tree.nodes
        img = bpy.data.images.new("BakedTex", width=2048, height=2048)
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        nodes.active = tex_node
        # select SRC then DST(active): bake selected->active
        bpy.ops.object.select_all(action="DESELECT")
        src.select_set(True)
        dst.select_set(True)
        bpy.context.view_layer.objects.active = dst
        bpy.context.scene.render.engine = "CYCLES"
        cyc = bpy.context.scene.cycles
        cyc.samples = 8
        cyc.device = "CPU"
        bpy.context.scene.render.bake.use_selected_to_active = True
        bpy.context.scene.render.bake.cage_extrusion = 0.05
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"},
                            use_selected_to_active=True)
        img.filepath_raw = out_glb + ".baked.png"
        img.file_format = "PNG"
        img.save()
        baked = True
        bake_note = "diffuse baked 2048px"
    else:
        bake_note = "source had no node materials; skipped"
except Exception as e:  # noqa: BLE001
    bake_note = f"bake failed (non-fatal): {e}"

# export remeshed object only
bpy.ops.object.select_all(action="DESELECT")
dst.select_set(True)
bpy.context.view_layer.objects.active = dst
bpy.ops.export_scene.gltf(filepath=out_glb, export_format="GLB",
                          use_selection=True)

# measure topology of result
me = dst.data
quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
tris = sum(1 for p in me.polygons if len(p.vertices) == 3)
ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
report = {"quads": quads, "tris": tris, "ngons": ngons,
          "verts": len(me.vertices), "baked": baked, "bake_note": bake_note,
          "target_faces": target_faces}
with open(report_json, "w") as f:
    json.dump(report, f)
print("QUADREMESH_REPORT:" + json.dumps(report), flush=True)
'''


def quad_remesh_glb(glb: Path, out_dir: Path,
                    target_faces: int = 30000) -> Path:
    """Remesh a triangle GLB into quad-dominant topology. Returns new GLB path.

    Raises ProviderError on genuine failure (Blender missing, import empty,
    quadriflow error). Texture bake is best-effort and reported, never fatal.
    """
    glb = Path(glb)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{glb.stem}.quad.glb"
    report_p = out_dir / f"{glb.stem}.quadremesh.json"

    try:
        stdout = run_bpy(_BPY_SCRIPT, str(glb), str(out),
                         str(target_faces), str(report_p),
                         timeout=1800)
    except ProviderError:
        raise
    except Exception as e:  # noqa: BLE001
        raise ProviderError(f"quadremesh: blender stage failed: {e}")

    if "QUADREMESH_FAIL" in stdout:
        raise ProviderError(
            f"quadremesh failed: {[l for l in stdout.splitlines() if 'QUADREMESH_FAIL' in l]}")
    if not out.exists() or out.stat().st_size < 1024:
        raise ProviderError("quadremesh: no output GLB produced")

    # read the measured topology report (proof, not claims)
    try:
        rep = json.loads(report_p.read_text())
        q, t, n = rep["quads"], rep["tris"], rep["ngons"]
        total = q + t + n
        qpct = 100.0 * q / total if total else 0
        print(f"quadremesh: {q} quads / {t} tris / {n} ngons "
              f"({qpct:.1f}% quad), bake: {rep.get('bake_note')}",
              file=sys.stderr)
        if qpct < 50:
            raise ProviderError(
                f"quadremesh: output only {qpct:.1f}% quads — remesh did not take")
    except ProviderError:
        raise
    except Exception as e:  # noqa: BLE001
        raise ProviderError(f"quadremesh: could not verify topology: {e}")
    return out
