# LICENSES.md — license manifest

Every pulled tool, model, and API dependency used by Forge3D. Updated whenever a
provider is added. Owner rule: GPL/AGPL-viral code is quarantined out of the
shipped tree; pre-ship license audit is mandatory. All rows verified 2026-10-06
against official repos (see docs/research/).

| Component | License | Commercial use | Notes |
|---|---|---|---|
| Forge3D own code (`forge3d/`, docs, configs) | MIT (TBD — owner picks at ship) | yes | prototype stage |
| trimesh (mesh I/O, cleanup, densify) | MIT | yes | base requirement |
| Pillow (texture extraction/upscale) | HPND | yes | base requirement |
| numpy | BSD-3-Clause | yes | base requirement |
| requests (API providers) | Apache-2.0 | yes | base requirement |
| instance-rig (auto-rig backend, external venv) | MIT | yes | not vendored; subprocess via `pipelines/rig.py` |
| TripoSR (Stability AI × Tripo) | MIT (code + weights) | yes | CPU-capable fallback provider; vendored tree patched 2026-10-06 for lazy rembg (see row below) |
| rembg (TripoSR optional bg-removal dep) | MIT | yes | optional; needed only when remove_bg=True; fails loudly if called without it |
| omegaconf / einops (TripoSR vendored-dep requirements) | BSD-3-Clause / MIT | yes | in requirements-local.txt |
| Stable Fast 3D | Stability AI Community License | yes, <$1M annual revenue | default GPU provider; gated HF checkpoint |
| TripoSG (VAST AI) | MIT | yes | shape fallback; geometry-only |
| Unique3D | MIT | yes | hero-asset provider (16 GB) |
| TRELLIS.2 (Microsoft) | MIT (code + weights) | yes | hero provider; 24 GB VRAM |
| Hunyuan3D-Paint (Tencent) | Tencent Hunyuan 3D 2.0 Community License | gated: EU/UK/SK excluded, 1M MAU cap, no-training-on-outputs, attribution | texture stage only; 16GB VRAM |
| MV-Adapter (ICCV 2025) | Apache-2.0 (adapter); SDXL base = Open RAIL++-M | yes (propagate RAIL Attachment-A) | commercial-safe multi-view (replaces Zero123++); ~14GB VRAM |
| TRELLIS.2 (Microsoft) | MIT (code + weights) | yes | SOTA quality anchor; 24GB VRAM (FP8 variant lower); DINOv3 dep is HF-gated |
| TripoSG (VAST AI) | MIT (code + weights) | yes | watertight geometry workhorse, 8-12GB VRAM; geometry-only — pair with Paint |
| Hi3DGen (Stable-X) | MIT per upstream README — VERIFY LICENSE at pull time | yes (pending check) | best-detail geometry option; 16-19GB VRAM; geometry-only |
| Pollinations.ai (image + 3D API) | service terms | check terms before shipping | free key; 3D costs Pollen |
| Tripo3D API Platform | service terms, free tier CC BY 4.0 non-commercial | NO on free tier | prototyping/reference only |
| Meshy AI | service terms, free tier CC BY 4.0 | yes with attribution | web UI only (no free API) |
| TRELLIS.2 via HF Space (microsoft/TRELLIS.2) | MIT (code + weights); HF Spaces terms | yes | keyless Gradio REST provider `trellis2-space`; GPU on HF side; quality anchor |
| InstantMesh via HF Space (TencentARC/InstantMesh) | Apache-2.0; HF Spaces terms | yes | keyless Gradio REST provider `instantmesh-space`; fast iteration path |
| Pixal3D (TencentARC, SIGGRAPH 2026) | check at pull time | TBD | pixel-aligned TRELLIS.2 successor; not yet wired — candidate for next round |
| Blender 4.2 LTS (portable binary, `_vendor/`, gitignored) | GPL-3.0 | yes — used as a *tool*, not linked/vendored; scripts drive it headless via `--background --python` | Blender stage (`forge3d/blender/`); binary never committed |
| Blender Quadriflow remesher (built into Blender 4.2) | GPL-3.0 (part of Blender) | yes — same tool-use as Blender itself | quad-remesh stage (`pipelines/quadremesh.py`); no new license burden |
| Zero123++ (SUDO-AI-3D, via public HF Space) | CC-BY-NC 4.0 | NO — research-only | multi-view backend `zero123plus` (`pipelines/multiview.py`); NEVER in commercial auto path; verified 2026-10-07 against github.com/SUDO-AI-3D/zero123plus |
| Instant Meshes (wjakob) | BSD-3-Clause (verified 2026-10-07 against LICENSE.txt) | yes | EVALUATED, NOT WIRED — interactive GUI only, no CLI/batch mode for headless pipeline; Blender Quadriflow chosen instead |
| google/GNM head model (weights, HF `google/gnm-3`) | Apache-2.0 (repo + model) | yes | `forge3d/body/gnm_head.py`; weights cached repo-local, never committed |
| Prisma 3D (app) | commercial, NOT open source | n/a | workflow replicated as stages (docs/PRISMA_WORKFLOW.md); no code pulled |
| COLMAP / pycolmap | BSD-3-Clause | yes | scan path evaluated only (docs/SCAN_PATH.md); not wired |

## Parametric body models — license verdicts (2026-10-06)

| Model | License | Commercial-safe? | Forge3D decision |
|---|---|---|---|
| google/GNM head | Apache-2.0 | **yes** | WIRED — identity/expression parametric head |
| SMPL / SMPL-X / FLAME / STAR (MPI) | Max Planck non-commercial research only | **NO** | research reference only; weights never downloaded, outputs never derived |
| GHUM / GHUML (Google) | request-form gated | **NO (gated)** | reference only |
| Body morphs (`forge3d/body/morphs.py`) | Forge3D-original | yes | authored deformation fields, no statistical model, no tainted data |

## Hard no-gos (never wired as providers)
- Zero123++ weights — CC-BY-NC 4.0 (non-commercial). Code is Apache-2.0; weights are the blocker. Research/R&D only, quarantined from shipped builds.
- Hunyuan3D-2/2.1 full weights — territory exclusion, 1M MAU gate, no-training-use clause (same Tencent license family as Paint; Paint is the narrower, texture-only pull)
- nvdiffrast-dependent TRELLIS v1 pipeline — NVIDIA non-commercial source license (use TRELLIS.2/Hi3DGen instead)

## Quarantine policy
- `quarantine/` holds any GPL/AGPL-licensed code. NOTHING in `forge3d/` may import from it.
- Non-commercial-licensed models are research-only providers, clearly marked, never in the default `auto` path for money work.
