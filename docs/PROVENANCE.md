# PROVENANCE.md — where the code came from

Owner rule: reuse, don't duplicate. Provenance of everything ported in:

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/pipelines/postprocess.py` | AshLanev2 `tools/generative/3d/postprocess.py` | adapted to provider interface; trimesh-based; raises ProviderError on corrupt input (no fake pass-through) |
| `forge3d/providers/triposr.py` | AshLanev2 `tools/generative/3d/triposr_generate.py` | real inference path ported (mc_resolution, bg-removal, chunk_size 8192); honest DOWN until torch+vendor present |
| _(port candidates)_ | Bannon `tools/generative/mesh/mesh_doctor.py` | hole-fill + weld; next port for cleanup stage upgrade |
| _(ported 2026-10-07)_ | Bannon `tools/generative/mesh/lod_chain.py` | LOD0/1/2 for game-ready exports → now `forge3d/pipelines/lod.py` (see Vertical depth expansion) |
| `forge3d/pipelines/rig.py` | AshLanev2 `tools/auto-rig/auto_rig.py` | capsule/instance-rig skinning ported as library stage; external MIT venv via subprocess; validates bone count, raises ProviderError on failure |
| `forge3d/pipelines/texture.py` | new (Forge3D-original) | embedded-texture 2x refinement; backends: lanczos (CPU, honest resample), realesrgan (BSD, when installed), hunyuan-paint (Tencent license, gated — not wired) |
| `forge3d/pipelines/densify.py` | new (Forge3D-original) | midpoint subdivision toward ~1.9M-face Tripo bar; same surface, UV-safe; tessellation only, not detail |
| `forge3d/pipelines/measure.py` | new (Forge3D-original) | honest GLB metrics vs Tripo bar (faces/verts/texture-res/watertight/bones); feeds docs/TRIPO_BASELINE.md |
| `forge3d/pipelines/multiview.py` | new (Forge3D-original) | stage interface; backends fail loudly until wired (zero123plus = CC-BY-NC research-only; mv-adapter = Apache-2.0 verified 2026-10-06) |
| _(handoff only)_ | Bannon `tools/generative/retarget/*` | stays in Bannon; Forge3D emits handoff-ready GLB |
| _(imported in-place)_ | Bannon `tools/generative/motion/*`, `common/glb_anim.py` | NOT handoff-only anymore: consumed directly by `forge3d/animation/pose.py` (see row above); no code copied |
| `forge3d/pipelines/skeleton_58.json` | Bannon `out/CIPHER_repaired.glb` (extracted joint names + rest pose) | canonical 58-bone Mixamo skeleton, grounded 2026-10-06 — the retarget target |
| `forge3d/pipelines/mixamo_map.json` | Bannon `tools/generative/retarget/mixamo_map.json` | BVH/instance-rig joint name -> `mixamorig:` bone map used by retarget_58 |
| `forge3d/blender/stage.py` | Bannon `bannon_blender_rig.py` (op sequence: headless import -> join -> merge doubles -> normals -> decimate -> auto-weight -> export) | generalized as pipeline stages (cleanup/remesh/weights/58-retarget); bmesh used for mesh surgery (merge_by_distance op is unstable headless) |
| `forge3d/body/gnm_head.py` | google/GNM (Apache-2.0, cloned to `_vendor/gnm`, gitignored) | wrapped NumPy-side; model weights from public HF, cached repo-local, never committed |
| `forge3d/body/morphs.py` | new (Forge3D-original) | authored region-mask deformation fields; no MPI data anywhere in the chain |
| `forge3d/body/attach_head.py` | new (Forge3D-original) | GNM head → body merge: head-joint fallback OR geometric neck detection (deepest-significant cross-section minimum), scale/orient/seat, cosine-falloff neck-seam blending; unit-tested on synthetic + Bannon rig |
| `forge3d/scan/stage.py` | new (Forge3D-original) | COLMAP/pycolmap (BSD-3-Clause) phone-photogrammetry stage; HARD GPU gate (ScanError, never a fake mesh); Kaggle path in docs/SCAN_PATH.md |
| `forge3d/pipelines/transfer_weights.cjs` | Bannon `tools/model_diag/transfer_weights.cjs` @ 95300506b4b2a8be7ee7af54d2e93a2016dd9c4a | K=6 inverse-distance KNN donor→target skin-weight copy (verbatim skeleton + IBMs, target geometry/texture); proof run 2026-10-06: donor `docs/stage-evidence/bannon_15bone.glb` → 4mm-perturbed noskin target, 14789 verts, 15 joints, weight-sums exactly 1.0, top-joint agreement 100%, mean |W−W_donor| 0.01276; render + GLB under `docs/stage-evidence/donor-transfer/` |
| `forge3d/pipelines/normalize_to_donor.cjs` | Bannon `out/tools/normalize_to_donor.cjs` (build-output dir, untracked) @ 95f68f4bd2af8241e9d63fc2e1c6979db99279f3 | companion: bakes target mesh into donor bind space (uniform height scale + centre translate) before transfer |
| Bannon LICENSE for both ports | Copyright (c) 2026 mhvnsnt, All Rights Reserved | ported intra-owner (same copyright holder) at owner direction; no third-party code involved |

## CC0 asset library (2026-10-07 expansion)

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/assets/cc0_sources.py` | new (Forge3D-original) | registry of 8 blanket-CC0 sources + 3 per-asset sources; every blanket entry's terms read live 2026-10-07 (log: docs/CC0_SOURCES.md) |
| `forge3d/assets/fetch.py` | new (Forge3D-original) | keyless fetchers (ambientCG zip, Poly Haven file API, Kenney pack scrape) with sha256 `cc0_manifest.json` provenance; live-tested (Wood096 PBR set, 11 files, all CC0) |
| `forge3d/providers/cloudflare_workers_ai.py` | new (Forge3D-original) | key-ready SDXL text-to-image (free 10K Neurons/day, no card); creds via keys.py (owner signup); raises loudly without creds |
| CC0 texture proof | ambientCG Wood096_1K-JPG.zip | `runs/assets/cc0/Wood096/` + `cc0_manifest.json` — Color/NormalDX/GL/Displacement/Roughness, visually verified |

## Vertical depth expansion (2026-10-07)

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/pipelines/lod.py` | Bannon `tools/generative/mesh/lod_chain.py` (mhvnsnt/Bannon, proprietary — same owner, ported at owner direction 2026-10-07) | structural port; Forge3D extension: vendored headless-Blender COLLAPSE-decimate backend (open3d/fast-simplification not installed on free runner); LOD0/1/2 GLBs + face-count table; proof `docs/stage-evidence/lod/` |
| `forge3d/pipelines/upscale.py` | new (Forge3D-original) | Real-ESRGAN 2x texture upscale: vendored BasicSR RRDBNet arch (Apache-2.0) + official RealESRGAN_x2 weights (BSD-2-Clause), tiled torch-CPU inference; the ncnn-vulkan binary was evaluated and rejected on this box (needs Vulkan GPU — proven `vkCreateInstance failed -9`; api-wiring's own install notes agree); proof `docs/stage-evidence/upscale/` |
| `forge3d/pipelines/normalmap.py` | new (Forge3D-original) | tangent-space normal map baked from mesh geometry (trimesh+numpy UV rasterization), attached as material normalTexture; proof `docs/stage-evidence/normalmap/` |
| `forge3d/pipelines/remesh.py` | new (Forge3D-original) | voxel remesh vs bmesh-cleanup shootout harness (vendored headless Blender); verdict in `docs/REMESH_SHOOTOUT.md`; proof `docs/stage-evidence/remesh/` |
| `forge3d/pipelines/glbutil.py` | new (Forge3D-original) | shared GLB parse/append/write helpers — texture.py refactored onto it so upscale/normalmap extend rather than duplicate |
| `forge3d/pipelines/render.py` | new (Forge3D-original) | deterministic headless-Blender EEVEE 3/4-view render for stage evidence before/after pairs; `--hdri` wires CC0 HDRI environment lighting from the shared `assets/cc0/` library |
| `forge3d/pipelines/materials.py` | new (Forge3D-original) | CC0 PBR material stage on the **shared** library (`assets/cc0/`, pulled via the providers crew's `forge3d/assets/fetch.py` → `cc0_manifest.json`; catalog `docs/CC0_SOURCES.md`) — roughness + normal overlay (keeps GLB albedo) or full albedo swap; consolidated 2026-10-07 (parallel `docs/CC0_ASSETS.md` folded into `docs/CC0_SOURCES.md`, no competing system) |
| `forge3d/pipelines/texture.py` (edit) | existing | `_realesrgan2x` backend now actually wired via `upscale.esrgan2x` (was a loud-failure stub for the uninstalled `realesrgan` package); GLB rebuild refactored onto `glbutil` — behavior unchanged (verified: lanczos 768→1536 re-run byte-identical path) |
| `_vendor/realesrgan/` (rrdbnet_arch.py, LICENSE.txt, models/RealESRGAN_x2.pth) | xinntao/BasicSR (arch, Apache-2.0) + xinntao/Real-ESRGAN official v0.2.1 release (weights, BSD-2-Clause) | weights (67MB) downloaded 2026-10-07 via HuggingFace mirror (github.com blocked by egress proxy); gitignored, never committed |

## Keyless HF Space providers (2026-10-07 expansion)

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/providers/keys.py` | new (Forge3D-original) | `FORGE3D_<PROVIDER>_KEY` resolution: env first, then `~/.config/forge3d/api_keys.env` (600, `export KEY=...`); never prints/logs/commits values |
| `forge3d/providers/trellis1_space.py` | new (Forge3D-original, pattern from `hf_space.py`/`trellis2_space.py`) | trellis-community/TRELLIS space, single stateless `/generate_and_extract_glb` -> GLB; MIT weights; nvdiffrast-NC server-side caveat in LICENSES.md |
| `forge3d/providers/flux_space.py` | new (Forge3D-original, pattern from `pollinations_image.py`) | black-forest-labs/FLUX.1-schnell space, stateless `/infer` text-to-image concept stage (`fetch_image()`); Apache-2.0 |
| `forge3d/providers/instantmesh_space.py` (rewrite) | new (Forge3D-original) | stateless `/preprocess` + `/generate_mvs` (real artifacts saved); `/make3d` proven unusable over REST 3 ways (session_hash -> SSE `error: 404: Not Found`; official gradio_client -> AppError; stateless -> `error: null`) — raises ProviderError loudly with the forensics |
| `forge3d/providers/trellis2_space.py` (rewrite) | new (Forge3D-original) | stateless `/image_to_3d` (preview HTML saved); `/extract_glb` needs gr.State (null stateless, 404 session-pinned) — raises loudly; points at trellis1-space |
| REST forensics method | `https://huggingface.co/spaces/TencentARC/InstantMesh/raw/main/app.py`, `.../microsoft/TRELLIS.2/raw/main/app.py`, `.../trellis-community/TRELLIS/raw/main/app.py` | read upstream app.py to confirm gr.State chaining is the blocker; all community InstantMesh copies paused (HTTP 503); stabilityai/stable-fast-3d space 404 (down) |
| `forge3d/animation/pose.py` | new (Forge3D-original) | wraps Bannon `procedural_moves.export_move_onto_glb` via in-place import (no code copied); validates the `MOVE_*` animation landed with >0 channels, else ProviderError |
| `forge3d/blender/shapekeys.py` | new (Forge3D-original) | bakes `forge3d/body/morphs.py` region-mask deformations as Blender shape keys on the unrigged mesh → glTF morph targets; purges factory default objects before import (build-quirk fix) |
| `forge3d/blender/render.py` | new (Forge3D-original) | headless Cycles proof-render stage for stage evidence: bbox framing, studio lights, shape-key values + animation frame posing |
