# QUALITY100 — Wave 1: 100 pulls attacking the losing dimensions

**Standing directive:** the scorecard dimensions we don't win (TEXTURE
RESOLUTION, NATIVE DETAIL, plus mesh/topology) get CONTINUOUS pulling —
wave after wave. This document is **wave 1**. Every wave must move a
losing cell on `docs/TRIPO_SCORECARD.md`.

**Base:** `docs/RESOURCE_CATALOG.md` (184 entries) — its texture/mesh/
topology subset is the starting base; everything below marked 🆕 is a new
find from wave-1 research. Licenses verified from source per entry
(GitHub API license endpoint or raw LICENSE/README); never guessed.
🚫 = research-lane only (NC/restrictive). ❓ = unverified, do not wire.
⛔ = GPL/AGPL quarantine — document only, never ship in the tree.

## Wave-1 wired stages (proven, committed)

| Stage | File | Gap closed | Proof |
|---|---|---|---|
| SwinIR-S x4 texture SR | `forge3d/pipelines/swinir.py` | texture-res | `docs/stage-evidence/quality100/trellis2-concept2-high.swinir.{glb,json}` |
| xatlas auto-UV | `forge3d/pipelines/xatlas_uv.py` | texture-res/topology | `docs/stage-evidence/quality100/trellis2-concept2-high.xatlas.{glb,json}` |
| Micro-detail + detail normals | `forge3d/pipelines/detail.py` | native-detail | `docs/stage-evidence/quality100/trellis2-concept2-high.detail.{glb,json,png}` |
| AO bake (Blender Cycles) | `forge3d/pipelines/ao_bake.py` | native-detail | `docs/stage-evidence/quality100/trellis2-concept2-high.ao.{glb,png,json}` |
| Bump-to-geometry displacement | `forge3d/pipelines/displace.py` | native-detail | `docs/stage-evidence/quality100/trellis2-concept2-high.displace.{glb,json}` |

Sibling quality lane already owns (do NOT duplicate): remesh shootout,
speckle dilation, trimesh watertight weld, retexture, geometry normal maps,
Real-ESRGAN upscale, LOD chain, CC0 materials.

---

## 1. Texture upscaling / super-resolution (17) 🆕

### SUPIR 🚫
- **What:** SDXL-based photo-realistic restoration, tiled VAE — 4K maps in one pass.
- **URL:** https://github.com/Fanghua-Yu/SUPIR
- **License:** SUPIR Software License Agreement (custom, SupPixel Pty Ltd — raw LICENSE via license API) → RESEARCH ONLY
- **Free tier:** Self-hosted, ~24GB VRAM, no API
- **Impact:** 5/5 · **Difficulty:** 4/5
- **Notes:** Quality ceiling for the texture stage; benchmark/reference until license clarified.

### DiffBIR
- **What:** Two-stage blind restoration: SwinIR/BSRNet degradation removal + IRControlNet generative detail.
- **URL:** https://github.com/XPixelGroup/DiffBIR
- **License:** Apache-2.0 (GitHub API license endpoint)
- **Free tier:** Self-hosted; weights auto-download, tiled sampling for low VRAM
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Top wire candidate: permissive license, battle-tested, tiled inference = 4K UV textures on consumer GPU.

### OSEDiff
- **What:** One-step diffusion SR on SD2.1 via variational score distillation.
- **URL:** https://github.com/cswry/OSEDiff
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted; single forward pass
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Speed pick for the upscale stage; one step = cheap 4x on baked maps.

### SeeSR
- **What:** Semantics-aware SR; degradation-aware prompt extractor keeps generated detail semantically correct.
- **URL:** https://github.com/cswry/SeeSR
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Semantic prompts reduce wrong-guess artifacts on character textures (tattoos, fabric patterns).

### TSD-SR
- **What:** One-step SR via target score distillation from SD3-medium (CVPR 2025).
- **URL:** https://github.com/Microtreei/TSD-SR
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted; needs SD3-medium weights
- **Impact:** 4/5 · **Difficulty:** 4/5
- **Notes:** Newest DiT-backbone one-step SR; heavier setup (LoRA + embedding + SD3 weights).

### CCSR
- **What:** Content-consistent SR: diffusion rebuilds structure in 1–2 steps, GAN-finetuned VAE decoder adds deterministic detail.
- **URL:** https://github.com/csslc/CCSR
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Near-identical output every run (no diffusion lottery) — critical for a reproducible asset pipeline.

### CTMSR
- **What:** Distillation-free one-step SR via consistency trajectory matching; no teacher model needed (ICCV 2025).
- **URL:** https://github.com/CVL-UESTC/CTMSR
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** MIT + zero teacher dependency = cleanest to wire.

### PiSA-SR
- **What:** Dual-LoRA SR with separate pixel-level and semantic-level strength knobs (CVPR 2025).
- **URL:** https://github.com/csslc/PiSA-SR
- **License:** Apache-2.0 (README states it; API license field empty)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Adjustable fidelity/realism tradeoff — dial detail aggressiveness per asset.

### VOSR
- **What:** Vision-only generative SR, no text encoder; DiT one-step variant with VAE tiling (CVPR 2026).
- **URL:** https://github.com/cswry/VOSR
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted; VAE tiling for large images
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Vision-only = no prompt-engineering failure modes on texture maps.

### Real-ESRGAN v3
- **What:** RealESRGANv3 architecture + v3 general models: faster, cleaner GAN upscaling.
- **URL:** https://github.com/xinntao/Real-ESRGAN
- **License:** BSD-3-Clause (GitHub API)
- **Free tier:** Self-hosted; runs on CPU
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** v3 models are the current best GAN option — near-free quality bump on the existing upscale step.

### RealWebPhoto v4
- **What:** Community 4x models (DAT-2/ATD/DRCT/RGT backbones) trained on web-photo degradations.
- **URL:** https://openmodeldb.info/models/4x-RealWebPhoto-v4-dat2
- **License:** CC-BY-4.0 (OpenModelDB model page)
- **Free tier:** Weights-only; runs in Real-ESRGAN/neosr/chaiNNer pipelines
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Degradation mix matches texture-source photos better than generic Real-ESRGAN.

### FeMaSR 🚫
- **What:** VQGAN feature-matching blind SR — realistic texture restoration via implicit HR prior.
- **URL:** https://github.com/chaofengc/FeMaSR
- **License:** CC BY-NC-SA 4.0 (raw LICENSE) → RESEARCH ONLY
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Strong texture realism; NC blocks commercial wiring — benchmark/reference only.

### LDL
- **What:** Locally-discriminative loss: trains GAN-SR to emit realistic detail while suppressing artifacts.
- **URL:** https://github.com/csjliang/LDL
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Training-time loss, zero inference cost
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Useful when fine-tuning our own texture upscaler — artifact suppression is the #1 texture-SR failure.

### StructSR
- **What:** Real-world SR that explicitly refuses spurious/hallucinated details.
- **URL:** https://github.com/LYCEXE/StructSR
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Anti-hallucination SR — fidelity anchor against diffusion SR's guessing.

### Swin2SR
- **What:** SwinV2 transformer for compressed-image SR/restoration.
- **URL:** https://github.com/mv-lab/swin2sr
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Strong on compressed inputs (exported game textures).

### RealBasicVSR
- **What:** Real-world video SR with long-term temporal propagation.
- **URL:** https://github.com/ckkelvinchan/RealBasicVSR
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** For texture SEQUENCES (turntable captures, multi-view sets) — temporal consistency across frames.

### DFOSD ❓
- **What:** Distillation-free one-step diffusion SR with noise-aware discriminator + edge-aware DISTS loss.
- **URL:** https://github.com/JianzeLi-114/DFOSD
- **License:** UNVERIFIED (no license file; README silent) → DO NOT WIRE
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Interesting loss design, but no license = benchmark only until clarified.

---

## 2. Texture synthesis / generation (11) 🆕

### MatFuse
- **What:** Controllable SVBRDF generation with diffusion — text/palette/sketch/image conditioning + map-level inpainting edit.
- **URL:** https://github.com/code-sy95/matgen
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 5/5 · **Difficulty:** 4/5
- **Notes:** Highest-value texture-side find: generates diffuse/normal/roughness/specular TOGETHER — full PBR stack vs Tripo's baked materials.

### SurfaceNet
- **What:** Single photo → full SVBRDF (diffuse/normal/roughness/specular) via patch-based GAN.
- **URL:** https://github.com/perceivelab/surfacenet
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Photo-to-PBR: shoot real fabric/metal/leather → game-ready maps.

### Material Anything
- **What:** Diffusion PBR estimation for any 3D object: per-view estimate → UV unwrap → material refiner.
- **URL:** https://github.com/3DTopia/MaterialAnything
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 5/5 · **Difficulty:** 4/5
- **Notes:** Direct pipeline fit: takes a textured mesh, outputs refined UV-space PBR — exactly the Forge3D texture stage's input.

### SinGAN
- **What:** Learns a generative model from a SINGLE texture image; synthesizes variations and expansions.
- **URL:** https://github.com/tamarott/SinGAN
- **License:** MIT (raw LICENSE.txt)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Single-image texture expansion: turn one 512px swatch into infinite tileable variation.

### ConSinGAN
- **What:** Faster single-image GAN via concurrent multi-stage training.
- **URL:** https://github.com/tohinz/ConSinGAN
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted; trains in minutes
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** SinGAN-quality synthesis fast enough for per-asset use.

### LaMa
- **What:** Large-mask inpainting with Fourier convolutions; resolution-robust.
- **URL:** https://github.com/advimman/lama
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** UV seam repair, texture completion, hole-filling on baked maps — bread-and-butter texture cleanup.

### DeepFillv2 🚫
- **What:** Gated-convolution free-form inpainting.
- **URL:** https://github.com/JiahuiYu/generative_inpainting
- **License:** CC BY-NC (README badge) → RESEARCH ONLY
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** NC blocks wiring — LaMa covers the need permissively.

### MultiDiffusion ❓
- **What:** Fuses diffusion paths for controlled generation incl. panorama/tileable outputs.
- **URL:** https://github.com/omerbt/MultiDiffusion
- **License:** UNVERIFIED → DO NOT WIRE
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Method reference for seamless diffusion textures; wire only if license clarified.

### Material Maker
- **What:** Procedural PBR texture authoring + 3D model painting tool (Godot-based node graphs).
- **URL:** https://github.com/RodZill4/material-maker
- **License:** MIT (GitHub API)
- **Free tier:** Free desktop app
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Permissive Substance-Designer-class tool; exportable PBR sets feed the pipeline.

### EdgeConnect 🚫
- **What:** Structure-guided inpainting via edge prediction.
- **URL:** https://github.com/knazeri/edge-connect
- **License:** CC BY-NC 4.0 (raw LICENSE.md) → RESEARCH ONLY
- **Free tier:** Self-hosted
- **Impact:** 2/5 · **Difficulty:** 3/5
- **Notes:** Older; LaMa supersedes it permissively — listed for completeness.

### RePaint ❓
- **What:** Diffusion-based inpainting (unconditional DDPM repurposed).
- **URL:** https://github.com/andreas128/RePaint
- **License:** UNVERIFIED → DO NOT WIRE
- **Free tier:** Self-hosted; slow (~250 steps)
- **Impact:** 2/5 · **Difficulty:** 3/5
- **Notes:** Method reference only; LaMa is the wire candidate.

---

## 3. Detail synthesis (9) 🆕

### DeepBump ⛔
- **What:** Blender addon: albedo→normal, normal→height/displacement, normal→curvature, plus upscale.
- **URL:** https://github.com/HugoTini/DeepBump
- **License:** GPL-3.0 (GitHub API) → QUARANTINE
- **Free tier:** Free Blender addon
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Does exactly the detail-synthesis job but GPL = quarantine; use as reference for clean-room reimplementation (our detail.py covers albedo→normal already).

### GeoWizard
- **What:** Diffusion-based monocular depth + normal estimation.
- **URL:** https://github.com/fuxiao0719/geowizard
- **License:** CC BY 4.0 (README) — attribution only
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Depth+normal from a single render → displacement + normal detail synthesis.

### Marigold
- **What:** Repurposed diffusion for monocular depth.
- **URL:** https://github.com/prs-eth/Marigold
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** High-quality depth → displacement maps; depth-conditioned detail synthesis.

### StableNormal
- **What:** Diffusion normal estimation with reduced variance ("stable and sharp"), incl. 10x turbo variant.
- **URL:** https://github.com/Stable-X/StableNormal
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted; torch.hub one-liner
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Sharp normals from albedo renders → high-frequency surface detail; turbo variant is fast.

### DSINE 🚫
- **What:** Surface normal estimation rethinking inductive biases.
- **URL:** https://github.com/baegwangbin/DSINE
- **License:** Custom Imperial College license (non-transferable, non-sublicensable) → RESEARCH ONLY
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Strong normals, but bespoke restrictive license — benchmark only.

### Depth Anything V2
- **What:** Foundation monocular depth model.
- **URL:** https://github.com/DepthAnything/Depth-Anything-V2
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Robust depth → displacement for micro-surface relief; widely deployed.

### ZoeDepth
- **What:** Metric depth from a single image.
- **URL:** https://github.com/isl-org/ZoeDepth
- **License:** MIT (GitHub API; repo archived but functional)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Metric (absolute-scale) depth = physically-scaled displacement maps.

### MiDaS
- **What:** Robust relative monocular depth estimation.
- **URL:** https://github.com/isl-org/MiDaS
- **License:** MIT (GitHub API; archived)
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** Baseline depth estimator; v3.1 still solid for displacement.

### Omnidata 🚫
- **What:** Multi-task mid-level vision: normals, depth, curvature models from 3D scans.
- **URL:** https://github.com/EPFL-VILAB/omnidata
- **License:** Research/non-commercial (dataset EULA; code license ambiguous) → RESEARCH ONLY
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Normal+curvature models useful for detail synthesis; murky license = research lane.

---

## 4–10. (pending legs B/C — geometry, multiview, scan, Blender addons)

*Research in flight; this section fills in on wave-1 completion.*
