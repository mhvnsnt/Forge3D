# Prisma 3D workflow, replicated in Forge3D (2026-10-06)

**Prisma 3D status (verified 2026-10-06): commercial Android app**
(package `com.prisma3D.prisma3D`, developer Prisma3D, free with in-app
purchases, Google Play). It is **NOT open source** — there is no code to
pull. What we replicate is its *workflow*, as pipeline stages, which is what
the owner asked for ("the way they work").

## Prisma 3D's workflow (from its public feature list)

1. **Model** — create/select 3D objects, group multiple models, 3D mesh
   creator, digital drawing, 3D sculpting, 3D vector editing, 3D text.
2. **Texture / look** — design 3D textures and colors, texture mapping.
3. **Rig** — rigging, skinning (bone + weight paint on device).
4. **Morph / customize** — reshape, tweak proportions.
5. **Pose / animate** — timeline + keyframes, object positions over time,
   fast render to video, share.

## Forge3D mapping (every step exists as a stage)

**Status 2026-10-06: all 7 Prisma steps now have Forge3D stages.** The last
two unbuilt stages — morph-as-shape-keys and pose/animate in-Forge3D — were
implemented and checked off in the table below (✅ DONE rows).

| Prisma 3D step | Forge3D stage | Notes |
|---|---|---|
| Model (generate) | `providers/` + `pipelines/pipeline.py` | text/image -> mesh, free |
| Sculpt / mesh edit | `forge3d/blender/` | headless Blender: cleanup, voxel remesh, decimate, transforms |
| Texture / paint | `pipelines/texture.py` | Hunyuan3D-Paint refinement; Real-ESRGAN upscale |
| Rig + skinning | `pipelines/rig.py` (+ `blender/stage.py`) | auto-rig, auto-skin, weight smoothing, **58-bone retarget** |
| Morph / customize | `forge3d/body/morphs.py` + `forge3d/blender/shapekeys.py` | bulk, height, shoulders, belly, limbs — pre-rig; ✅ DONE 2026-10-06: morphs bake to real Blender shape keys → glTF morph targets (`docs/stage-evidence/shapekeys/trellis_morphs.glb`, 3 targets + 6 proof renders at 0.0/1.0) |
| Face | `forge3d/body/gnm_head.py` | GNM parametric head: identity + 383 expression blendshapes |
| Pose / animate | `forge3d/animation/pose.py` (Bannon `tools/generative/` moves imported in-place, never copied) | ✅ DONE 2026-10-06: one Bannon procedural clip (`TAUNT_CROWD`) injected as `MOVE_TAUNT_CROWD` glTF animation (5 channels) into 58-bone rigged GLB (`docs/stage-evidence/pose/pose_TAUNT_CROWD.glb` + 2 proof frames); input cleaned to single body (upstream 58-bone sources carry a double-body defect, documented in `docs/stage-evidence/pose/README.md`) |

## Blender setup (per host, once)

`bpy` has no PyPI wheel for this Python, so Forge3D uses the portable
Blender binary headless (`blender --background --python script.py`):

```bash
mkdir -p forge3d/_vendor && cd forge3d/_vendor
curl -sL -o blender.tar.xz https://download.blender.org/release/Blender4.2/blender-4.2.4-linux-x64.tar.xz
tar -xf blender.tar.xz   # -> blender-4.2.4-linux-x64/blender
```

`_vendor/` is gitignored (never committed). Override path with
`FORGE3D_BLENDER_BIN`. Headless-safe rule learned 2026-10-06: use `bmesh`
for mesh surgery — `bpy.ops.mesh.merge_by_distance` hard-kills the script
in this build with no traceback.

## What Prisma 3D does NOT give us (and we don't chase)

- Its on-device sculpt UI (touch sculpting) — out of scope for a pipeline;
  the web app (`web/`) is the Forge3D editing surface.
- Its renderer / video export — Bannon's pipeline owns animation render.
