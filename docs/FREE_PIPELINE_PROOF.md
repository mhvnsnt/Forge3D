# FREE_PIPELINE_PROOF.md — end-to-end evidence (2026-10-16)

Track 2 deliverable: the free pipeline proven with measured numbers.
Every claim below carries its artifact path.

## Stage-wiring proof (CPU sandbox, local Blender 4.0.2 headless)

Input: `fixtures/fixture_tpose.obj` — synthetic T-pose test figure
(1056 verts / 2080 tris, TEST FIXTURE ONLY, not a deliverable model).

| Stage | In → Out | Measured result |
|---|---|---|
| obj→glb | fixture_tpose.obj → fixture.glb | 263,152 bytes, valid GLB |
| quadremesh (Quadriflow) | fixture.glb → fixture.quad.glb | **60 quads / 0 tris / 0 ngons (100.0% quad)** — coarse because the fixture is 6 disconnected parts at 2k tris; real TripoSR meshes are single-component 6–50k tris |
| auto_skin → 58-bone WH skeleton | fixture.quad.glb → fixture.rigged.glb | **58 joints verified** (`mixamorig:Hips` … `mixamorig:LeftToeBase`), `JOINTS_0` + `WEIGHTS_0` skinning attributes present |
| export | rigged.glb → .fbx + .obj | FBX 150,428 bytes, OBJ 11,523 bytes |

**Quadriflow limitation (2026-10-16):** `bpy.ops.object.quadriflow_remesh`
silently no-ops (returns FINISHED, 0 quads) on TripoSR-generated meshes
(tested 29,690-tri flamingo, with/without preserve flags) — works fine on
the synthetic fixture. The stage fails loudly via its 0%-quad gate rather
than passing through bad topology. Root cause unidentified; quadremesh of
AI-generated meshes needs GPU-side investigation.

Driver: `~/workspace/forge3d-scratch/stage_proof.py`
(note: Blender 4.x renamed OBJ I/O to `wm.obj_import`/`wm.obj_export` —
`bpy.ops.import_scene.obj` no longer exists).

## TripoSR generation proof (CPU) — 2026-10-16

- Weights: `~/.forge3d/weights/triposr/model.ckpt` (1,677,246,742 bytes,
  zip-valid 553 entries) + `config.yaml`, downloaded via resilient
  `wget -c` loop (egress proxy kills connections ~hourly; loop relaunches).
- Provider: `forge3d/providers/triposr.py` — bf16 fast path, transformers
  4.40.0, torchmcubes CPU shim (skimage-backed, recreated 2026-10-16 with
  bf16→fp32 cast fix), component filtering.
- **Pipeline wiring: PROVEN end-to-end.** Three generations ran without
  errors:
  - `tripo-studio-redhooded-tpose.png` (phone screenshot) → 14,842 verts /
    29,690 faces, 594,736-byte GLB, vertex colors present
  - `flamingo.png` (official TripoSR test image) → 12,650 verts /
    25,300 faces, 506,984-byte GLB (bf16 and fp32 both)
  - Rig: 58-bone auto_skin verified (`JOINTS_0`+`WEIGHTS_0`), exports:
    GLB 4,999,964 B / FBX 2,065,548 B / OBJ 4,620,968 B
- **Quality limitation (honest):** CPU generations are flattened
  ("pancake") — e.g. flamingo extents 0.967×0.959×0.183 instead of a
  proper 3D bird. Debugging 2026-10-16: DINO encoder healthy
  (input-dependent features), 549/549 checkpoint keys match, shim
  verified correct via sphere test, preprocessing matches upstream,
  fp32=bf16, transformers 4.40=4.57. Root cause unidentified; needs GPU
  validation (CUDA torchmcubes + GPU inference may resolve).
- Artifacts: `~/workspace/forge3d-scratch/proof/gen2/`,
  `gen3/`, `gen4/`, `gen5/` (comparison renders included).
- The Colab notebook (`notebooks/Forge3D_Free_Pipeline.ipynb`) remains
  the primary quality generation path (free T4, seconds per model).

## TRELLIS.2 provider

- `forge3d/providers/trellis2.py` wired against the real upstream API
  (verified from microsoft/TRELLIS.2 source 2026-10-16:
  `Trellis2ImageTo3DPipeline.from_pretrained("microsoft/TRELLIS.2-4B")`
  → `.cuda()` → `.run(image, seed)` → `o_voxel.postprocess.to_glb(...)` PBR).
- GPU execution pending first GPU-runner run (no CUDA in sandbox).
  Fails loudly until then — never a fake mesh.

## License posture

- Shipped path is MIT-only: TripoSR (MIT) + TRELLIS.2 (MIT).
- Hunyuan3D 2.1 EXCLUDED from the license-strict default
  (Tencent community license — territory exclusions). Pre-existing
  `hunyuan-paint` provider stays as-is (clearly labeled in LICENSES.md);
  no new non-MIT/Apache components added by this work.
- Full manifest: docs/WEIGHTS.md. Hardware truth: docs/HARDWARE_MATRIX.md.
