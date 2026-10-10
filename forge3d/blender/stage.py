"""Blender stage — headless bpy ops on generated meshes.

Blender-in-full inside Forge3D: the vendored portable Blender 4.2 binary
(repo `_vendor/`, gitignored — download once per host) runs generated bpy
scripts via `blender --background --python`. No `bpy` pip wheel exists for
this Python, so the portable binary IS the headless module.

Provenance: op sequences adapted from Bannon's bannon_blender_rig.py
(headless GLB import -> join -> merge doubles -> normals -> decimate ->
segment -> auto-weight -> export); generalized here as pipeline stages.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from ..providers.base import ProviderError

REPO = Path(__file__).resolve().parents[2]
VENDORED = REPO / "_vendor" / "blender-4.2.4-linux-x64" / "blender"


def blender_bin() -> Path:
    env = os.environ.get("FORGE3D_BLENDER_BIN")
    if env and Path(env).exists():
        return Path(env)
    if VENDORED.exists():
        return VENDORED
    raise ProviderError(
        "Blender stage unavailable: no Blender binary. Download the Blender "
        "4.2 portable release into forge3d/_vendor/ (see docs/PRISMA_WORKFLOW.md) "
        "or set FORGE3D_BLENDER_BIN.")


def run_bpy(script: str, *args: str, timeout: int = 900) -> str:
    """Run a bpy script headless. Args are passed after `--`. Returns stdout."""
    bbin = blender_bin()
    # absolutize path-like args: Blender resolves relatives against its own CWD
    def _fix(a):
        if isinstance(a, str) and (a.endswith((".glb", ".gltf", ".obj", ".json"))
                                   or "/" in a):
            return str(Path(a).resolve())
        return a
    args = [_fix(a) for a in args]
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name
    try:
        # xvfb-run provides the GLX context Blender needs (EGL breaks on restarts)
        import shutil
        xvfb = shutil.which("xvfb-run")
        cmd = [str(bbin), "--background", "--python", script_path, "--", *args]
        if xvfb:
            cmd = [xvfb, "-a"] + cmd
        r = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise ProviderError(f"blender stage timed out after {timeout}s: {e}")
    finally:
        Path(script_path).unlink(missing_ok=True)
    if r.returncode != 0:
        raise ProviderError(f"blender stage failed:\n{r.stderr[-1500:]}")
    return r.stdout


_PREAMBLE = """
import bpy, sys, json, math
argv = sys.argv[sys.argv.index("--") + 1:]
INP, OUTP = argv[0], argv[1]

def meshes():
    return [o for o in bpy.data.objects if o.type == 'MESH']

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=INP)
ms = meshes()
if not ms:
    print("[blender] FATAL: no mesh in", INP); sys.exit(1)
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1:
    bpy.ops.object.join()
OBJ = bpy.context.view_layer.objects.active
"""


def cleanup(in_glb: Path, out_glb: Path, decimate_ratio: float = 0.0,
            timeout: int = 900) -> Path:
    """Import -> join -> merge doubles -> recalc normals -> smart UV (if none)
    -> optional decimate -> apply transforms -> export GLB."""
    script = _PREAMBLE + """
RATIO = float(argv[2]) if len(argv) > 2 else 0.0
import bmesh, traceback
bpy.context.view_layer.objects.active = OBJ
# merge doubles + recalc normals via bmesh (headless-safe; the
# bpy.ops.mesh.merge_by_distance operator is unstable in this build)
try:
    bm = bmesh.new(); bm.from_mesh(OBJ.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(OBJ.data); bm.free(); OBJ.data.update()
    print("[blender] bmesh clean: verts=", len(OBJ.data.vertices))
except Exception:
    traceback.print_exc(); print("[blender] FATAL: bmesh clean"); sys.exit(1)
# smart UV project only if the mesh has no UVs
try:
    if not OBJ.data.uv_layers:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[blender] smart UV projected")
except Exception as e:
    print("[blender] UV project skipped:", e)
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except Exception: pass
if RATIO > 0:
    try:
        mod = OBJ.modifiers.new('decim', 'DECIMATE')
        mod.ratio = RATIO
        bpy.context.view_layer.objects.active = OBJ
        bpy.ops.object.modifier_apply(modifier=mod.name)
        print("[blender] decimated: verts=", len(OBJ.data.vertices))
    except Exception as e:
        print("[blender] decimate skipped:", e)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.export_scene.gltf(filepath=OUTP, export_format='GLB')
print("[blender] exported", OUTP)
"""
    run_bpy(script, str(in_glb), str(out_glb), str(decimate_ratio),
            timeout=timeout)
    return Path(out_glb)


def remesh_voxel(in_glb: Path, out_glb: Path, voxel_size: float = 0.012,
                 timeout: int = 1200) -> Path:
    """Voxel remesh for even, watertight-ish topology (attacks triangle soup)."""
    script = _PREAMBLE + """
VOX = float(argv[2]) if len(argv) > 2 else 0.012
mod = OBJ.modifiers.new('remesh', 'REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = VOX
bpy.ops.object.modifier_apply(modifier=mod.name)
print("[blender] remesh done: verts=", len(OBJ.data.vertices))
bpy.ops.export_scene.gltf(filepath=OUTP, export_format='GLB')
"""
    run_bpy(script, str(in_glb), str(out_glb), str(voxel_size), timeout=timeout)
    return Path(out_glb)


def smooth_weights(in_glb: Path, out_glb: Path, factor: float = 0.5,
                   repeat: int = 4, timeout: int = 900) -> Path:
    """Smooth every vertex group (skin-weight cleanup hook)."""
    script = _PREAMBLE + """
FAC = float(argv[2]) if len(argv) > 2 else 0.5
REP = int(argv[3]) if len(argv) > 3 else 4
bpy.context.view_layer.objects.active = OBJ
for i, vg in enumerate(OBJ.vertex_groups):
    OBJ.vertex_groups.active_index = i
    bpy.ops.object.vertex_group_smooth(factor=FAC, repeat=REP)
print("[blender] smoothed", len(OBJ.vertex_groups), "vertex groups")
bpy.ops.export_scene.gltf(filepath=OUTP, export_format='GLB')
"""
    run_bpy(script, str(in_glb), str(out_glb), str(factor), str(repeat),
            timeout=timeout)
    return Path(out_glb)


def auto_skin(in_glb: Path, out_glb: Path, bones_json: Path,
              timeout: int = 900) -> Path:
    """Build an armature from a bone list and bind with automatic weights.

    bones_json: {"bones": [{"name":..., "parent": idx|None, "rest":[x,y,z]}]}
    Generalizes bannon_blender_rig.py's skin() to any bone list.
    """
    script = _PREAMBLE + """
BJ = argv[2]
skel = json.load(open(BJ))
bones = skel["bones"]
# scale skeleton to mesh: match bbox heights
bb = [OBJ.matrix_world @ v.co for v in OBJ.data.vertices]
miny = min(v.y for v in bb); maxy = max(v.y for v in bb)
ry = [b["rest"][1] for b in bones]
ry0, ry1 = min(ry), max(ry)
S = (maxy - miny) / max(ry1 - ry0, 1e-9)
cx = sum(v.x for v in bb) / len(bb); cz = sum(v.z for v in bb) / len(bb)
scx = sum(b["rest"][0] for b in bones) / len(bones)
scz = sum(b["rest"][2] for b in bones) / len(bones)
def W(b):
    return (cx + (b["rest"][0]-scx)*S, miny + (b["rest"][1]-ry0)*S, cz + (b["rest"][2]-scz)*S)

arm_data = bpy.data.armatures.new('FORGE_RIG')
arm = bpy.data.objects.new('FORGE_RIG', arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for b in bones:
    e = arm_data.edit_bones.new(b["name"]); e.head = W(b); eb[b["name"]] = e
for i, b in enumerate(bones):
    if b["parent"] is not None:
        p = bones[b["parent"]]["name"]; eb[b["name"]].parent = eb[p]
        eb[b["name"]].tail = W(bones[b["parent"]])
    else:
        e = eb[b["name"]]; e.tail = (e.head[0], e.head[1]-0.06*S, e.head[2])
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
OBJ.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
try:
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
except Exception as e:
    print("[blender] auto-weight fallback:", e)
    bpy.ops.object.parent_set(type='ARMATURE')
print("[blender] skinned to", len(bones), "bones")
bpy.ops.export_scene.gltf(filepath=OUTP, export_format='GLB')
"""
    run_bpy(script, str(in_glb), str(out_glb), str(bones_json), timeout=timeout)
    return Path(out_glb)


def retarget_58(in_glb: Path, out_glb: Path, skeleton_json: Path,
                mixamo_map_json: Path | None = None, timeout: int = 1200) -> Path:
    """Re-skin a rigged GLB onto the canonical 58-bone Mixamo skeleton.

    How it works (honest, no spatial hallucination): the source mesh's vertex
    groups are RENAMED onto the 58-bone namespace (exact match first, then
    mixamo_map.json for foreign rigs like instance-rig/BVH names), groups with
    no target bone are dropped and logged, a fresh 58-bone armature is built
    at rest pose scaled to the mesh, the source armature is deleted, and the
    mesh is bound with type='ARMATURE' (transferred weights preserved).
    Fails loudly if under 50% of groups map.
    """
    script = _PREAMBLE + """
BJ = argv[2]
MJ = argv[3] if len(argv) > 3 and argv[3] != "NONE" else None
skel = json.load(open(BJ)); bones = skel["bones"]
TARGET = set(b["name"] for b in bones)
mmap = json.load(open(MJ)) if MJ else {}
def norm(n):
    return n.lower().replace("mixamorig:", "").replace("_", "").replace(" ", "")
normmap = {norm(k): v for k, v in mmap.items() if not k.startswith("_")}

SRC_ARM = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        SRC_ARM = o; break
if SRC_ARM is None:
    print("[blender] FATAL: no armature in", INP); sys.exit(1)

# --- rename vertex groups onto the 58-bone namespace ---
kept, dropped, renamed = [], [], {}
for vg in list(OBJ.vertex_groups):
    n = vg.name
    if n in TARGET:
        kept.append(n); continue
    tgt = normmap.get(norm(n))
    if tgt and tgt in TARGET and tgt not in [v.name for v in OBJ.vertex_groups]:
        vg.name = tgt; renamed[n] = tgt; kept.append(tgt)
    elif tgt and tgt in TARGET:
        # merge into existing group of same target name
        renamed[n] = tgt + " (merged)"
        # merge weights: add to existing
        dst = OBJ.vertex_groups[tgt]
        for v in OBJ.data.vertices:
            try:
                w = vg.weight(v.index)
            except RuntimeError:
                continue
            try:
                dst.add([v.index], w, 'ADD')
            except RuntimeError:
                pass
        OBJ.vertex_groups.remove(vg)
        kept.append(tgt)
    else:
        dropped.append(n)
        OBJ.vertex_groups.remove(vg)
cov = len(kept) / max(len(kept) + len(dropped), 1)
print(f"[blender] group map: kept={len(kept)} renamed={len(renamed)} dropped={len(dropped)} coverage={cov:.2f}")
print("[blender] dropped:", dropped[:12])
if cov < 0.5:
    print("[blender] FATAL: mapping coverage < 50%"); sys.exit(1)

# --- build 58-bone armature at rest pose, scaled to mesh ---
bb = [OBJ.matrix_world @ v.co for v in OBJ.data.vertices]
miny = min(v.y for v in bb); maxy = max(v.y for v in bb)
ry = [b["rest"][1] for b in bones]; ry0, ry1 = min(ry), max(ry)
S = (maxy - miny) / max(ry1 - ry0, 1e-9)
cx = sum(v.x for v in bb)/len(bb); cz = sum(v.z for v in bb)/len(bb)
scx = sum(b["rest"][0] for b in bones)/len(bones)
scz = sum(b["rest"][2] for b in bones)/len(bones)
def W(b):
    return (cx + (b["rest"][0]-scx)*S, miny + (b["rest"][1]-ry0)*S, cz + (b["rest"][2]-scz)*S)
arm_data = bpy.data.armatures.new('mixamorig')
arm = bpy.data.objects.new('mixamorig', arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for b in bones:
    e = arm_data.edit_bones.new(b["name"]); e.head = W(b); eb[b["name"]] = e
for i, b in enumerate(bones):
    if b["parent"] is not None:
        p = bones[b["parent"]]["name"]; eb[b["name"]].parent = eb[p]
        eb[b["name"]].tail = W(bones[b["parent"]])
    else:
        e = eb[b["name"]]; e.tail = (e.head[0], e.head[1]-0.06*S, e.head[2])
bpy.ops.object.mode_set(mode='OBJECT')
bpy.data.objects.remove(SRC_ARM, do_unlink=True)

# --- bind, preserving renamed groups ---
bpy.ops.object.select_all(action='DESELECT')
OBJ.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE')
print("[blender] bound to 58 bones; vgroups=", len(OBJ.vertex_groups))
bpy.ops.export_scene.gltf(filepath=OUTP, export_format='GLB')
print("[blender] exported", OUTP)
"""
    run_bpy(script, str(in_glb), str(out_glb), str(skeleton_json),
            str(mixamo_map_json) if mixamo_map_json else "NONE",
            timeout=timeout)
    return Path(out_glb)
