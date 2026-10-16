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

Driver: `~/workspace/forge3d-scratch/stage_proof.py`
(note: Blender 4.x renamed OBJ I/O to `wm.obj_import`/`wm.obj_export` —
`bpy.ops.import_scene.obj` no longer exists).

## TripoSR generation proof (CPU)

- Provider: `forge3d/providers/triposr.py` (battle-hardened 2026-10-07:
  bf16 fast path, transformers 4.x pin, torchmcubes CPU shim, component
  filtering, proxy sanitization, `--wait-for-ram` gate).
- Prior measurement on this VM class (2026-10-07, documented in
  docs/FREE_RUNNER_GUIDE.md): deterministic 6,634 verts at 128³,
  ~2–10 min/image on CPU.
- 2026-10-16 rebuild: venv + weights re-download in progress
  (network-throttled); fresh generation proof runs when they land.
  The Colab notebook (`notebooks/Forge3D_Free_Pipeline.ipynb`) is the
  primary generation path (free T4, seconds per model).

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
