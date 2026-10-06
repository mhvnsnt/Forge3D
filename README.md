# Forge3D

Free, open-source 3D character model generation — Tripo3D-quality output at zero cost.

**Status: PHASE 1 — pipeline built, no models generated yet.** The pipeline is wired and self-tested; the first generation run happens only after owner review of the architecture.

## What it is

One interface (`forge3d generate`) over multiple backends:

- **Local providers** — open-source models run on your own hardware (TripoSR, TRELLIS, Shap-E, Hunyuan3D, InstantMesh, …). Free forever, limited by your GPU.
- **Free-API providers** — Meshy, Tripo3D, Rodin/Hyper3D, Pollinations, Hugging Face Inference — free tiers behind one interface with quota tracking.

## Pipeline stages

```
text prompt ──► concept image ──► multi-view ──► mesh ──► texture ──► GLB export
   (free image APIs / local SD)   (Zero123++ /     (local or API)   (Hunyuan3D-Paint /
                                    provider-native)                  provider-native)
                                              │
                                              ▼
                                    cleanup / normalize
                                    (existing mesh postprocessor,
                                     ported from AshLanev2 tools)
                                              │
                                              ▼
                                    handoff → retarget / rig tooling
                                    (existing Bannon/AshLanev2 generative tooling)
```

## Honest Tripo comparison

| | Tripo3D | Forge3D (target) |
|---|---|---|
| Cost | paid / limited free | $0 |
| Topology | clean, animation-ready-ish | best local models still need cleanup — postprocessor + retarget stage closes the gap |
| Textures | PBR, crisp | Hunyuan3D-Paint / provider textures; weakest link on local-only runs |
| Anatomy | strong | multi-view stage is the bottleneck — garbage views in, garbage mesh out |
| Speed | seconds–minutes (cloud) | local: minutes–tens of minutes; free APIs: queue-bound |

See `docs/INVENTORY.md` for the full model/API/compute audit and `docs/GAPS_VS_TRIPO.md` for the honest gap list.

## Quick start (free runner)

```bash
pip install -r requirements.txt
python -m forge3d selftest        # verifies pipeline wiring without generating
python -m forge3d generate --prompt "..." --provider auto --out out/
```

`--provider auto` picks the best available backend: free API with quota remaining → local model if GPU present → CPU fallback (slow, honest about it).

See `docs/FREE_RUNNER_GUIDE.md` for Kaggle/Colab/HF Spaces setups.

## Layout

- `providers/` — backend implementations behind `providers/base.py`
- `pipelines/` — stage orchestration (concept → views → mesh → texture → export)
- `configs/` — per-provider and per-stage configs
- `docs/` — inventory, architecture, gaps, runner guide
- `tests/` — selftests and provider smoke tests
- `LICENSES.md` — license manifest for every pulled tool
- `quarantine/` — GPL/AGPL code lives here ONLY, never imported by pipelines
