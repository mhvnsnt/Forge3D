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
| Hi3DGen (Stable-X) | MIT — confirmed via Stable-X/Hi3DGen README "License" section 2026-10-06 | yes | best-detail geometry option; 16-19GB VRAM; geometry-only |
| Pollinations.ai (image + 3D API) | service terms | check terms before shipping | free key; 3D costs Pollen |
| Tripo3D API Platform | service terms, free tier CC BY 4.0 non-commercial | NO on free tier | prototyping/reference only |
| Meshy AI | service terms, free tier CC BY 4.0 | yes with attribution | web UI only (no free API) |
| TRELLIS.2 via HF Space (microsoft/TRELLIS.2) | MIT (code + weights); HF Spaces terms | yes | keyless Gradio REST provider `trellis2-space`; GPU on HF side; quality anchor. REST LIMIT 2026-10-07: /extract_glb needs gr.State — null over stateless REST, session-pinned calls 404 on this Gradio version — so generate() runs /image_to_3d (preview HTML saved) then raises loudly; use trellis1-space for working keyless GLB |
| InstantMesh via HF Space (TencentARC/InstantMesh) | Apache-2.0 (code+weights); Zero123++ stage weights CC-BY-NC 4.0; HF Spaces terms | NO — Zero123++ weights are non-commercial | keyless Gradio REST provider `instantmesh-space`. REST LIMIT 2026-10-07: session-pinned chain (preprocess->mvs->make3d) broken — every session_hash call fails SSE `error: 404: Not Found` (proven 3 ways); stateless /preprocess + /generate_mvs work (artifacts saved for MULTIVIEW stage), /make3d raises loudly |
| TRELLIS v1 via HF Space (trellis-community/TRELLIS) | MIT (microsoft/TRELLIS code + weights); HF Spaces terms | gated — upstream v1 pipeline uses nvdiffrast (NVIDIA non-commercial source license) server-side; no NC code in our tree, but treat outputs as research-only pending owner call | keyless Gradio REST provider `trellis1-space`; single stateless /generate_and_extract_glb -> GLB; GPU on HF side. LIVE-TEST 2026-10-07: schema verified, end-to-end GLB run quota-blocked (ZeroGPU anon quota exhausted, reset ~22h) — retest pending |
| FLUX.1-schnell via HF Space (black-forest-labs/FLUX.1-schnell) | Apache-2.0; HF Spaces terms | yes | keyless Gradio REST provider `flux-space`; TEXT_TO_IMAGE concept stage (fetch_image()); GPU on HF side |
| Pixal3D (TencentARC, SIGGRAPH 2026) | check at pull time | TBD | pixel-aligned TRELLIS.2 successor; not yet wired — candidate for next round |
| Blender 4.2 LTS (portable binary, `_vendor/`, gitignored) | GPL-3.0 | yes — used as a *tool*, not linked/vendored; scripts drive it headless via `--background --python` | Blender stage (`forge3d/blender/`); binary never committed |
| Blender Quadriflow remesher (built into Blender 4.2) | GPL-3.0 (part of Blender) | yes — same tool-use as Blender itself | quad-remesh stage (`pipelines/quadremesh.py`); no new license burden |
| Zero123++ (SUDO-AI-3D, via public HF Space) | CC-BY-NC 4.0 | NO — research-only | multi-view backend `zero123plus` (`pipelines/multiview.py`); NEVER in commercial auto path; verified 2026-10-07 against github.com/SUDO-AI-3D/zero123plus |
| Instant Meshes (wjakob) | BSD-3-Clause (verified 2026-10-07 against LICENSE.txt) | yes | EVALUATED, NOT WIRED — interactive GUI only, no CLI/batch mode for headless pipeline; Blender Quadriflow chosen instead |
| google/GNM head model (weights, HF `google/gnm-3`) | Apache-2.0 (repo + model) | yes | `forge3d/body/gnm_head.py`; weights cached repo-local, never committed |
| Prisma 3D (app) | commercial, NOT open source | n/a | workflow replicated as stages (docs/PRISMA_WORKFLOW.md); no code pulled |
| COLMAP / pycolmap | BSD-3-Clause | yes | WIRED 2026-10-07 — `forge3d/scan/stage.py` (hard GPU gate, loud failure); docs/SCAN_PATH.md |
| Real-ESRGAN x2 weights (`_vendor/realesrgan/models/RealESRGAN_x2.pth`, official v0.2.1 release) | BSD-2-Clause (xinntao/Real-ESRGAN) | yes | texture upscale stage (`pipelines/upscale.py`); weights downloaded 2026-10-07 from the official release, never committed |
| CC0 asset library (`forge3d/assets/cc0/`, fetched via `forge3d/assets/fetch.py` → `cc0_manifest.json`) | CC0-1.0 (Poly Haven, ambientCG — blanket; verified live 2026-10-07, see `docs/CC0_SOURCES.md`) | yes | shared providers-crew registry (`cc0_sources.py`); vertical stages wire it: `render.py --hdri` (Poly Haven `studio_small_09` 1k HDRI), `pipelines/materials.py` (Poly Haven `cotton_jersey` 1k PBR set). md5-verified pulls only. |
| RRDBNet arch (`_vendor/realesrgan/rrdbnet_arch.py`, vendored from xinntao/BasicSR) | Apache-2.0 | yes | dependency-free inference copy (registry replaced with no-op shim); full license text in `_vendor/realesrgan/LICENSE.txt` |
| realesrgan-ncnn-vulkan binary (`~/workspace/api-wiring/bin/`) | BSD-3-Clause (nihui) | yes | DOCUMENTED ONLY — requires Vulkan GPU, which the free runner lacks (proven 2026-10-07: `vkCreateInstance failed -9`); torch path used instead |
| Bannon `tools/generative/mesh/lod_chain.py` (port source for `pipelines/lod.py`) | Proprietary — Copyright (c) 2026 mhvnsnt, All Rights Reserved | intra-owner port | ported 2026-10-07 at owner direction (same copyright holder); Forge3D adds a headless-Blender decimate backend so LODs build with zero pip installs |

## CC0 / public-domain 3D asset sources (verified live 2026-10-07)

Owner rule: CC0 / public domain ONLY — no NC, no SA. Full verification log:
docs/CC0_SOURCES.md. Registry: `forge3d/assets/cc0_sources.py`; fetcher with
sha256 provenance manifests: `forge3d/assets/fetch.py`.

| Component | License | Commercial use | Notes |
|---|---|---|---|
| Poly Haven (textures/HDRI/models) | CC0-1.0 (blanket, verified at polyhaven.com/license) | yes | keyless file API; direct dl.polyhaven.org downloads (API ToS: commercial API use needs sponsorship) |
| ambientCG (PBR materials/models/HDRI) | CC0-1.0 (blanket, verified at docs.ambientcg.com/license) | yes | keyless catalog API + direct zip downloads; live-tested 2026-10-07 (Wood096 PBR set) |
| Quaternius (low-poly packs, animation library) | CC0 (per pack page, verified live) | yes | manual/page-scrape zips; rigged characters + 250+ anim clips |
| Kenney (3D kits, 2D, UI, audio) | CC0 (per asset page, verified live) | yes | page-scrape zips; city kits for urban-district dressing |
| KayKit (low-poly characters/kits) | CC0-1.0 (GitHub org LICENSE) | yes, except owner law bans KK chibi in AshLane | prototyping/tooling only |
| cgbookcase / TextureCan (PBR textures) | CC0 (per site terms, secondary-verified) | yes | recheck terms before first bulk pull |
| NASA 3D Resources | US federal public domain | yes | skip contractor-credited entries |
| Poly Pizza / Khronos glTF-Sample-Models / Smithsonian 3D | per-asset (CC0 or CC-BY / CC0-designated only) | per-asset check required | NEVER auto-fetch blind; CC-BY needs attribution |
| Cloudflare Workers AI (SDXL text-to-image) | service-terms; SDXL: Stability AI Community License | check terms before shipping | key-ready provider `cloudflare-workers-ai`; free 10K Neurons/day, no card; key via free account (owner signup) |

## Parametric body models — license verdicts (2026-10-06)

| Model | License | Commercial-safe? | Forge3D decision |
|---|---|---|---|
| google/GNM head | Apache-2.0 | **yes** | WIRED — identity/expression parametric head |
| SMPL / SMPL-X / FLAME / STAR (MPI) | Max Planck non-commercial research only | **NO** | research reference only; weights never downloaded, outputs never derived |
| GHUM / GHUML (Google) | request-form gated | **NO (gated)** | reference only |
| Body morphs (`forge3d/body/morphs.py`) | Forge3D-original | yes | authored deformation fields, no statistical model, no tainted data |

| Bannon `tools/generative/motion/procedural_moves.py` + `common/glb_anim.py` | Copyright (c) 2026 mhvnsnt, All Rights Reserved — intra-owner reuse, same copyright holder | yes | imported in-place via `forge3d/animation/pose.py` (`FORGE3D_BANNON_GENERATIVE` env or `~/workspace/bannon-repair/tools/generative` default); NO code copied into the Forge3D tree |

## Hard no-gos (never wired as providers)
- Zero123++ weights — CC-BY-NC 4.0 (non-commercial). Code is Apache-2.0; weights are the blocker. Research/R&D only, quarantined from shipped builds.
- Hunyuan3D-2/2.1 full weights — territory exclusion, 1M MAU gate, no-training-use clause (same Tencent license family as Paint; Paint is the narrower, texture-only pull)
- nvdiffrast-dependent TRELLIS v1 pipeline — NVIDIA non-commercial source license (use TRELLIS.2/Hi3DGen instead)

## Quarantine policy
- `quarantine/` holds any GPL/AGPL-licensed code. NOTHING in `forge3d/` may import from it.
- Non-commercial-licensed models are research-only providers, clearly marked, never in the default `auto` path for money work.
| SwinIR (JingyunLiang/SwinIR — network vendored in gitignored `forge3d/pipelines/_vendor/`, weights host-local `~/.forge3d/weights/swinir/`) | Apache-2.0 (verified 2026-10-07 via GitHub API) | yes | `forge3d/pipelines/swinir.py` — SwinIR-S x4 CPU texture SR; timm shim avoids torchvision chain |
| xatlas (jpcy/xatlas — pip wheel) | MIT (verified 2026-10-07) | yes | `forge3d/pipelines/xatlas_uv.py` — auto-UV rewrite |
| manifold3d (elalish/manifold — pip) | Apache-2.0 (verified 2026-10-07) | yes | EVALUATED, not wired: `Manifold(Mesh)` ctor returns NotManifold/empty on trellis triangle soup in current bindings (no MeshGL soup-repair path) — trimesh weld remains the repair route |
| QUALITY100 wave-1 catalog (114 entries: 57 queued permissive, 22 GPL quarantine, 13 paid note-only, 12 research-only, 8 unverified-blocked, 2 wired) | mixed — see `docs/QUALITY100.md` per-entry | per entry | full license manifest in docs/QUALITY100.md "License red-flag summary"; wave-2 queue prioritized by impact |
