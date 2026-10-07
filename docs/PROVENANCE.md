# PROVENANCE.md — where the code came from

Owner rule: reuse, don't duplicate. Provenance of everything ported in:

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/pipelines/postprocess.py` | AshLanev2 `tools/generative/3d/postprocess.py` | adapted to provider interface; trimesh-based; raises ProviderError on corrupt input (no fake pass-through) |
| `forge3d/providers/triposr.py` | AshLanev2 `tools/generative/3d/triposr_generate.py` | real inference path ported (mc_resolution, bg-removal, chunk_size 8192); honest DOWN until torch+vendor present |
| _(port candidates)_ | Bannon `tools/generative/mesh/mesh_doctor.py` | hole-fill + weld; next port for cleanup stage upgrade |
| _(port candidates)_ | Bannon `tools/generative/mesh/lod_chain.py` | LOD0/1/2 for game-ready exports |
| `forge3d/pipelines/rig.py` | AshLanev2 `tools/auto-rig/auto_rig.py` | capsule/instance-rig skinning ported as library stage; external MIT venv via subprocess; validates bone count, raises ProviderError on failure |
| `forge3d/pipelines/texture.py` | new (Forge3D-original) | embedded-texture 2x refinement; backends: lanczos (CPU, honest resample), realesrgan (BSD, when installed), hunyuan-paint (Tencent license, gated — not wired) |
| `forge3d/pipelines/densify.py` | new (Forge3D-original) | midpoint subdivision toward ~1.9M-face Tripo bar; same surface, UV-safe; tessellation only, not detail |
| `forge3d/pipelines/measure.py` | new (Forge3D-original) | honest GLB metrics vs Tripo bar (faces/verts/texture-res/watertight/bones); feeds docs/TRIPO_BASELINE.md |
| `forge3d/pipelines/multiview.py` | new (Forge3D-original) | stage interface; backends fail loudly until wired (zero123plus = CC-BY-NC research-only; mv-adapter = Apache-2.0 verified 2026-10-06) |
| _(handoff only)_ | Bannon `tools/generative/retarget/*`, `motion/*` | stays in Bannon; Forge3D emits handoff-ready GLB |
| `forge3d/pipelines/skeleton_58.json` | Bannon `out/CIPHER_repaired.glb` (extracted joint names + rest pose) | canonical 58-bone Mixamo skeleton, grounded 2026-10-06 — the retarget target |
| `forge3d/pipelines/mixamo_map.json` | Bannon `tools/generative/retarget/mixamo_map.json` | BVH/instance-rig joint name -> `mixamorig:` bone map used by retarget_58 |
| `forge3d/blender/stage.py` | Bannon `bannon_blender_rig.py` (op sequence: headless import -> join -> merge doubles -> normals -> decimate -> auto-weight -> export) | generalized as pipeline stages (cleanup/remesh/weights/58-retarget); bmesh used for mesh surgery (merge_by_distance op is unstable headless) |
| `forge3d/body/gnm_head.py` | google/GNM (Apache-2.0, cloned to `_vendor/gnm`, gitignored) | wrapped NumPy-side; model weights from public HF, cached repo-local, never committed |
| `forge3d/body/morphs.py` | new (Forge3D-original) | authored region-mask deformation fields; no MPI data anywhere in the chain |
| `forge3d/pipelines/transfer_weights.cjs` | Bannon `tools/model_diag/transfer_weights.cjs` @ 95300506b4b2a8be7ee7af54d2e93a2016dd9c4a | K=6 inverse-distance KNN donor→target skin-weight copy (verbatim skeleton + IBMs, target geometry/texture); proof run 2026-10-06: donor `docs/stage-evidence/bannon_15bone.glb` → 4mm-perturbed noskin target, 14789 verts, 15 joints, weight-sums exactly 1.0, top-joint agreement 100%, mean |W−W_donor| 0.01276; render + GLB under `docs/stage-evidence/donor-transfer/` |
| `forge3d/pipelines/normalize_to_donor.cjs` | Bannon `out/tools/normalize_to_donor.cjs` (build-output dir, untracked) @ 95f68f4bd2af8241e9d63fc2e1c6979db99279f3 | companion: bakes target mesh into donor bind space (uniform height scale + centre translate) before transfer |
| Bannon LICENSE for both ports | Copyright (c) 2026 mhvnsnt, All Rights Reserved | ported intra-owner (same copyright holder) at owner direction; no third-party code involved |
