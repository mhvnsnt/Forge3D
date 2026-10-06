# PROVENANCE.md — where the code came from

Owner rule: reuse, don't duplicate. Provenance of everything ported in:

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/pipelines/postprocess.py` | AshLanev2 `tools/generative/3d/postprocess.py` | adapted to provider interface; trimesh-based; raises ProviderError on corrupt input (no fake pass-through) |
| `forge3d/providers/triposr.py` | AshLanev2 `tools/generative/3d/triposr_generate.py` | real inference path ported (mc_resolution, bg-removal, chunk_size 8192); honest DOWN until torch+vendor present |
| _(port candidates)_ | Bannon `tools/generative/mesh/mesh_doctor.py` | hole-fill + weld; next port for cleanup stage upgrade |
| _(port candidates)_ | Bannon `tools/generative/mesh/lod_chain.py` | LOD0/1/2 for game-ready exports |
| _(port candidates)_ | AshLanev2 `character/auto-rig.py` | capsule-distance skinning to 58-joint Mixamo skeleton (pure CPU) — rig stage |
| _(handoff only)_ | Bannon `tools/generative/retarget/*`, `motion/*` | stays in Bannon; Forge3D emits handoff-ready GLB |
