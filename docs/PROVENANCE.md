# PROVENANCE.md — where the code came from

Owner rule: reuse, don't duplicate. Provenance of everything ported in:

| Forge3D file | Source | Notes |
|---|---|---|
| `forge3d/pipelines/postprocess.py` | AshLanev2 `tools/generative/` mesh postprocessor | adapted to provider interface; trimesh-based |
| `forge3d/providers/triposr.py` | AshLanev2 `tools/generative/` TripoSR wrapper | rewritten against `ModelProvider` base |
| _(pending)_ trellis/hunyuan providers | AshLanev2 wrappers | port after inventory confirms versions |
| _(pending)_ retarget/rig handoff | Bannon `tools/generative/` retargeters + mesh repair | handoff contract only — that tooling stays in Bannon, Forge3D emits handoff-ready GLB |
