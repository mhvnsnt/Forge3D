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
| `forge3d/pipelines/multiview.py` | new (Forge3D-original) | stage interface; backends fail loudly until wired (zero123plus = CC-BY-NC research-only; mv-adapter license unverified) |
| _(handoff only)_ | Bannon `tools/generative/retarget/*`, `motion/*` | stays in Bannon; Forge3D emits handoff-ready GLB |
