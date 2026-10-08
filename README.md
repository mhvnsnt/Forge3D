# Forge3D

Free, open-source 3D character model generation — Tripo3D-quality output at zero cost.

**Status: PIPELINE OPERATIONAL — generations running.** The pipeline is wired, self-tested (14/14), and has produced models (`runs/gen1/`, `runs/closeout/`, `runs/quality/`). Anatomical defect gates (horse-leg detectors) are wired into the pipeline and verified against a proof corpus (`docs/ANATOMY_GATES.md`). Generation quality work continues toward the 400% bar.

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

## Web app (Tripo Studio-style, purple/white)

```
pip install -r requirements-web.txt
uvicorn web.backend.app:app --host 0.0.0.0 --port 8765
# open http://localhost:8765
```

Layout mirrors Tripo Studio: left panel (Text to 3D / Image to 3D / Multiview
tabs, prompt box, image upload dropzone, provider picker, Generate), center
Three.js viewport with orbit controls, right panel (job history, model info
with faces/verts front and center, GLB/USD/FBX downloads), top bar with the
Forge3D logo (white diamond in a purple circle) and backend status. Image
upload works from a phone browser (plain file input + dropzone).

API: `POST /api/upload`, `POST /api/generate`, `GET /api/job/{id}`,
`GET /api/download/{id}?format=glb|usdz|fbx`, `GET /api/providers`.
Generation runs the real `forge3d` pipeline in a background thread — the web
layer adds no new meshing code.

Free hosting notes: the app is CPU-safe (TripoSR path). On Hugging Face
Spaces, use the CPU Basic tier with `requirements-web.txt`; expect ~1-3 min
per generation. GPU runners (Kaggle 30h/week free) unlock SF3D/TripoSG/
Hunyuan3D-Paint via the provider registry with no web-code changes.

## Layout

- `providers/` — backend implementations behind `providers/base.py`
- `pipelines/` — stage orchestration (concept → views → mesh → texture → export)
- `configs/` — per-provider and per-stage configs
- `docs/` — inventory, architecture, gaps, runner guide
- `tests/` — selftests and provider smoke tests
- `LICENSES.md` — license manifest for every pulled tool
- `quarantine/` — GPL/AGPL code lives here ONLY, never imported by pipelines
