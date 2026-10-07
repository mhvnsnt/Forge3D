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

## 4. Mesh quality (10) 🆕

### ACVD
- **What:** Isotropic surface remeshing via discrete Voronoi clustering — detail-even triangle redistribution.
- **URL:** https://github.com/valette/ACVD
- **License:** CeCILL-B (French BSD-style permissive — raw LICENSE.txt)
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** CLI-oriented C++; needs a Python/CLI wrapper for pipeline use.

### PyMeshLab ⛔
- **What:** Python bindings to the full MeshLab filter set: Taubin/Laplacian/HC smoothing, isotropic remeshing, quadric simplification, AO + vertex-attribute-to-texture baking.
- **URL:** https://github.com/cnr-isti-vclab/PyMeshLab
- **License:** GPL-3.0 (GitHub API) → QUARANTINE — worker process only, never linked into MIT core
- **Free tier:** `pip install pymeshlab`, no limits
- **Impact:** 5/5 · **Difficulty:** 2/5
- **Notes:** Single highest-leverage mesh-quality pickup — quarantine as external process.

### meshoptimizer
- **What:** Industry-standard mesh simplification, vertex-cache/fetch optimization, LOD generation.
- **URL:** https://github.com/zeux/meshoptimizer
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Clean C API; trivial to bind. Complements fast-simplification.

### geometry-central
- **What:** Discrete differential geometry toolkit; intrinsic Delaunay remeshing that preserves detail while fixing triangle quality.
- **URL:** https://github.com/nmwsharp/geometry-central
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Intrinsic (not extrinsic) remeshing is the detail-preserving choice.

### CinoLib
- **What:** Header-only C++ mesh processing: isotropic remeshing, smoothing/denoising, harmonic maps, mesh repair.
- **URL:** https://github.com/mlivesu/cinolib
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, no limits
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Header-only = easy vendoring.

### gpytoolbox ⛔
- **What:** Python geometry-processing prototyping kit (smoothing, remeshing, decimation, deformation).
- **URL:** https://github.com/sgsellan/gpytoolbox
- **License:** GPL-3.0 (GitHub API) → QUARANTINE — offline R&D only
- **Free tier:** `pip install gpytoolbox`
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** Prototype here, port winners to MIT code.

### libigl Python bindings ⛔
- **What:** Python bindings for libigl algorithms. ACTIVE (pushed 2026-09).
- **URL:** https://github.com/libigl/libigl-python-bindings
- **License:** GPL-3.0 (GitHub API) → QUARANTINE — license trap: core libigl is MPL-2.0 but the *bindings* are GPL-3.0
- **Free tier:** pip, no limits
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** External-process quarantine only.

### fTetWild
- **What:** Robust tetrahedral meshing from messy triangle soups.
- **URL:** https://github.com/wildmeshing/fTetWild
- **License:** MPL-2.0 (GitHub API)
- **Free tier:** Self-hosted, no limits
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Robustness story valuable for auto-ingest of user meshes.

### Mmg
- **What:** Industrial anisotropic/isotropic remesher; adapts triangle density to curvature = detail where it matters.
- **URL:** https://github.com/MmgTools/mmg
- **License:** LGPL-3.0-or-later (raw LICENSE) → external binary only, don't static-link
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Closest open-source answer to "Tripo keeps detail in the face, drops it on flat areas."

### L0Mesh ❓
- **What:** C++ "Mesh Denoising via L0 Minimization" (He & Schaefer) — feature-preserving denoise.
- **URL:** https://github.com/li-yiqing/L0Mesh
- **License:** UNVERIFIED (no LICENSE file) → DO NOT SHIP
- **Free tier:** Self-hosted
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Research lane only until license clarified.

---

## 5. Topology / retopology (9) 🆕

### Instant Meshes
- **What:** Interactive field-aligned quad-dominant remeshing (the paper implementation).
- **URL:** https://github.com/wjakob/instant-meshes
- **License:** BSD-3-Clause (raw LICENSE.txt — GitHub API said NOASSERTION, file is unambiguous)
- **Free tier:** Self-hosted, no limits
- **Impact:** 5/5 · **Difficulty:** 3/5
- **Notes:** The topology-gap closer. Permissive license = pipeline-safe. CLI-able.

### QuadriFlow
- **What:** Scalable, robust automatic quadrangulation (the "instant-meshes successor" paper code).
- **URL:** https://github.com/hjwdzh/QuadriFlow
- **License:** BSD-3-Clause-style (raw LICENSE.txt; README says MIT — either way permissive)
- **Free tier:** Self-hosted, no limits
- **Impact:** 5/5 · **Difficulty:** 3/5
- **Notes:** Enable `BUILD_FREE_LICENSE=ON` in CMake (Eigen's sparse Cholesky piece is LGPL). Best batch-mode auto-retopo candidate. NOTE: Blender 4.2 does NOT bundle Quadriflow (removed in 4.0) — build standalone.

### QuadWild ⛔
- **What:** Feature-line-driven quad remeshing — preserves sharp character features (armor edges, jawlines).
- **URL:** https://github.com/nicopietroni/quadwild
- **License:** GPL-3.0 (GitHub API) → QUARANTINE
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** External-process quarantine; Python bindings also GPL.

### RetopoFlow ⛔
- **What:** Full artist retopology suite for Blender (Contours/Polystrips/Strokes).
- **URL:** https://github.com/CGCookie/retopoflow
- **License:** GPL-3.0-or-later (raw RetopoFlow.LICENSE) → QUARANTINE
- **Free tier:** Free, open-source
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Manual-retopo path when auto methods fail on hero characters. Study the stroke UX; reimplement ideas in vanilla bpy.

### Tissue ⛔
- **What:** Blender addon: tessellation, dual-mesh, UV-to-mesh computational-design toolkit.
- **URL:** https://github.com/alessandro-zomparelli/tissue
- **License:** GPL-2.0-or-later (SPDX header) → QUARANTINE
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Tessellate/dual-mesh operators useful for pattern-based topology (armor, cloth).

### PolyQuilt ⛔
- **What:** Blender low-poly/retopo modeling addon (draw quads on high-poly surface).
- **URL:** https://github.com/sakana3/PolyQuilt
- **License:** GPL-3.0 (GPL header) → QUARANTINE
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Artist-facing; lightweight manual retopo.

### Mira Tools
- **What:** Blender modeling/retopo toolkit (loop tools, curve-guided modeling).
- **URL:** https://github.com/mifth/mifthtools
- **License:** BSD-3-Clause (GitHub API) — rare permissive Blender addon, no quarantine needed
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Retopo aids shippable without GPL concerns.

### Exoside QuadRemesher (paid, note only)
- **What:** One-click automatic quad remesher (Blender/Maya/Max/Houdini/C4D/Modo).
- **URL:** https://www.exoside.com/quadremesher/
- **License:** Proprietary, PAID (~$120 perpetual; trial available)
- **Free tier:** 30-day trial
- **Impact:** 5/5 · **Difficulty:** 1/5
- **Notes:** The commercial quality bar; useful as reference output for before/after comparisons.

### quadriflow PyPI (does not exist)
- **What:** FINDING: no maintained `quadriflow` pip package (PyPI 404, checked 2026-10-07).
- **URL:** n/a
- **License:** n/a
- **Free tier:** —
- **Impact:** — · **Difficulty:** —
- **Notes:** Build hjwdzh/QuadriFlow from source; do not chase a pip package.

---

## 6. UV (9) 🆕

### thekla_atlas
- **What:** Charting + packing texture-atlas generator in one small C library.
- **URL:** https://github.com/Thekla/thekla_atlas
- **License:** MIT (raw LICENSE + GitHub API)
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Single-file-ish, easy to embed.

### UVAtlas (Microsoft)
- **What:** Isochart texture atlas: partition + parameterize + pack (DirectX heritage).
- **URL:** https://github.com/microsoft/UVAtlas
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, no limits
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** ARCHIVED repo (read-only) — code stable/final, safe to vendor, no upstream fixes.

### rectpack
- **What:** 2D rectangle-packing library (Python) — pack UV islands into texture space.
- **URL:** https://github.com/secnot/rectpack
- **License:** Apache-2.0 (GitHub API + PyPI)
- **Free tier:** `pip install rectpack`
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** The *packing* half of the pipeline; pair with any unwrapper.

### Magic UV ⛔
- **What:** Blender UV manipulation toolkit (align, pack, transfer, texel-density).
- **URL:** https://github.com/nutti/Magic-UV
- **License:** GPL-2.0-or-later (raw LICENSE) → QUARANTINE (Blender-side only)
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Mine for operator ideas; reimplement in vanilla bpy.

### TexTools ⛔
- **What:** UV + texture toolset for Blender (island tools, texel density, baking helpers, ID maps).
- **URL:** https://github.com/SavMartin/TexTools-Blender
- **License:** GPL-3.0 (raw LICENSE.txt) → QUARANTINE
- **Free tier:** Free
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Strongest free Blender UV/texture toolkit; texel-density workflow is the key idea to reimplement.

### UvSquares ⛔
- **What:** Reshape UV quad selections into grids (straighten UVs).
- **URL:** https://github.com/Radivarig/UvSquares
- **License:** GPL-2.0 (GitHub API) → QUARANTINE
- **Free tier:** Free
- **Impact:** 2/5 · **Difficulty:** 1/5
- **Notes:** Straight UVs = cleaner bakes; easy to reimplement.

### UniV ⛔
- **What:** Modern free Blender UV addon (selection/transform/sync operators).
- **URL:** https://extensions.blender.org/add-ons/univ/
- **License:** GPL-3.0-or-later (extensions.blender.org badge) → QUARANTINE
- **Free tier:** Free via Blender Extensions
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Newer Magic UV alternative.

### Zen UV (paid, note only)
- **What:** Pro Blender UV pipeline: Zen Unwrap, seam groups, texel density, island stacking.
- **URL:** https://www.superhivemarket.com/products/zen-uv
- **License:** Proprietary, PAID ($24–39)
- **Free tier:** None
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Reference for what a pro UV workflow looks like.

### Headus UVLayout (paid, note only)
- **What:** Standalone low-distortion UV unwrapper — the industry unwrap standard.
- **URL:** https://www.uvlayout.com/
- **License:** Proprietary, PAID (~$100 student / ~$300 pro)
- **Free tier:** Demo
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Quality bar for unwrap distortion.

---

## 7. Normal / displacement / AO / cavity baking (12) 🆕

### MikkTSpace
- **What:** THE standard tangent-space basis used by bakers everywhere for consistent normal maps.
- **URL:** https://github.com/mmikk/MikkTSpace
- **License:** zlib-style permissive (raw mikktspace.h header — "for any purpose, including commercial")
- **Free tier:** Two drop-in files, no limits
- **Impact:** 5/5 · **Difficulty:** 1/5
- **Notes:** Non-negotiable for correct normal maps — Blender, xNormal, Substance all standardize on this. Wire first.

### three-gpu-baker
- **What:** Progressive diffuse lightmap + AO baker for Three.js (TypeScript, WebGPU); imports GLB/OBJ, exports lightmap UV atlas.
- **URL:** https://github.com/hoodgail/three-gpu-baker
- **License:** MIT (GitHub API)
- **Free tier:** `npm install three-gpu-baker`, no limits
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Browser-native baking fits the PWA pipeline (bake AO/lightmaps client-side).

### Laigter ⛔
- **What:** Automatic normal-map generator (sprite/2D focused).
- **URL:** https://github.com/azagaya/laigter
- **License:** GPL-3.0 (GitHub API) → QUARANTINE
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Marginal for 3D characters; useful for UI/decal normal maps.

### AwesomeBump ⛔
- **What:** GPU normal/height/specular/AO generation from a single image.
- **URL:** https://github.com/kmkolasinski/AwesomeBump
- **License:** GPL-3.0 (GitHub API) → QUARANTINE
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Image→maps path for detail synthesis.

### Materialize ⛔
- **What:** Convert images to full PBR materials (normal, height, AO, roughness, metallic).
- **URL:** https://github.com/BoundingBoxSoftware/Materialize
- **License:** GPL-3.0 (GitHub API) → QUARANTINE (correction: it IS open source, not just freeware)
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Offline authoring reference only.

### EZ Baker ⛔
- **What:** Blender addon orchestrating bakes across backends with bake groups.
- **URL:** https://github.com/eastingroup/ez_baker
- **License:** GPL-3.0 (GitHub API) → QUARANTINE
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Aging (2022); the multi-backend bake-group architecture is the pattern to copy.

### pybaker ❓
- **What:** Minimal Python vertex-attribute→texture baker.
- **URL:** https://github.com/LuniumLuk/pybaker
- **License:** UNVERIFIED (no license file) → DO NOT SHIP
- **Free tier:** pip-installable from source
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** Reimplement or get license before shipping.

### Blender built-in baking ⛔
- **What:** Cycles multires/normal/AO/cavity/displacement bakes, cage + selected-to-active.
- **URL:** https://github.com/blender/blender
- **License:** GPL-2.0-or-later → QUARANTINE (scripting our own usage via bpy is always safe)
- **Free tier:** Free, no limits
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** The free baseline everything else is measured against; scriptable headless.

### Handplane Baker (freeware, external step)
- **What:** Production baker: AO, cavity, curvature, tangent/object normal, height, vertex color, material IDs.
- **URL:** https://www.handplane3d.com/
- **License:** Proprietary FREEWARE (free download, Windows)
- **Free tier:** Free download
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Usable as an external bake step today at $0; no source to wire.

### Knald (paid, note only)
- **What:** GPU "bake-quality" texture generation: normal/displacement/AO/concavity.
- **URL:** https://www.knaldtech.com/
- **License:** Proprietary, PAID (~$100–200)
- **Free tier:** Demo
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Note only.

### Marmoset Toolbag (paid, note only)
- **What:** Industry-standard real-time baker + presentation.
- **URL:** https://marmoset.co/toolbag/
- **License:** Proprietary, PAID
- **Free tier:** Trial
- **Impact:** 5/5 · **Difficulty:** 1/5
- **Notes:** The bake-quality bar; note only.

### Substance 3D Painter (paid, note only)
- **What:** Adobe's texture-authoring/baking suite.
- **URL:** https://www.adobe.com/products/substance3d-painter.html
- **License:** Proprietary, PAID (subscription)
- **Free tier:** Trial
- **Impact:** 5/5 · **Difficulty:** 1/5
- **Notes:** Ecosystem ceiling; not actionable at $0 budget.

---

## 8. Multi-view consistency (8) 🆕

### Paint-it
- **What:** Text-to-texture via deep convolutional texture-map optimization + physically-based rendering (DC-PBR); disentangled PBR maps.
- **URL:** https://github.com/kaist-ami/Paint-it
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, needs GPU
- **Impact:** 4/5 · **Difficulty:** 4/5
- **Notes:** PBR output (albedo/roughness/normal) fits Forge3D's relightable pipeline.

### FlashTex
- **What:** Fast relightable mesh texturing with LightControlNet — separates illumination from albedo.
- **URL:** https://github.com/Roblox/FlashTex
- **License:** Apache-2.0 (LICENSE file head)
- **Free tier:** Self-hosted, GPU
- **Impact:** 4/5 · **Difficulty:** 4/5
- **Notes:** Directly attacks the baked-lighting defect; Roblox research, game-industry relevance high.

### TexPainter
- **What:** Generative mesh texturing with multi-view consistency via modified multi-DDIM enforcing cross-view agreement per denoising step.
- **URL:** https://github.com/Quantuman134/TexPainter
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, GPU
- **Impact:** 3/5 · **Difficulty:** 4/5
- **Notes:** SyncMVD-alternative texture-space diffusion.

### Make-it-Real
- **What:** LMM-guided realistic PBR material painting for 3D objects.
- **URL:** https://github.com/Aleafy/Make_it_Real
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, GPU + LMM
- **Impact:** 3/5 · **Difficulty:** 4/5
- **Notes:** Could ground texture semantics to the owner's art references.

### CaPa
- **What:** Carve-n-Paint: decouples geometry and texture synthesis; spatially-decoupled attention paints up to 4K textures in <30s + 3D-aware occlusion inpainting.
- **URL:** https://github.com/ncsoft/CaPa
- **License:** BSD-3-Clause (GitHub API + LICENSE head; README footer "© NCSOFT" loses to the LICENSE file)
- **Free tier:** Self-hosted, GPU
- **Impact:** 5/5 · **Difficulty:** 3/5
- **Notes:** NCSOFT's production Varco 3D tech; 4K-in-30s is the closest open thing to Tripo's texture speed/quality.

### Fantasia3D
- **What:** Disentangled geometry/appearance text-to-3D; BRDF-based appearance modeling yields clean PBR textures.
- **URL:** https://github.com/Gorilla-Lab-SCUT/Fantasia3D
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted, heavy GPU
- **Impact:** 3/5 · **Difficulty:** 5/5
- **Notes:** Full text-to-3D system — heavier lift than a pure texturing stage.

### Generative Repainting of 3D Assets 🚫
- **What:** Generative repainting of existing 3D assets — re-texture without regen.
- **URL:** https://github.com/kongdai123/repainting_3d_assets
- **License:** CC BY-NC-SA 4.0 (LICENSE head) → RESEARCH ONLY
- **Free tier:** Self-hosted, GPU
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** NC bars shipping; the repaint/refine technique is applicable as reference.

### TANGO ❓
- **What:** Text-driven photorealistic 3D stylization via lighting decomposition.
- **URL:** https://github.com/Gorilla-Lab-SCUT/tango
- **License:** UNVERIFIED (no license file) → DO NOT USE without permission
- **Free tier:** Self-hosted, GPU
- **Impact:** 2/5 · **Difficulty:** 3/5
- **Notes:** Lighting-decomposition idea is the valuable part; code can't be used.

---

## 9. Scan / reconstruction detail preservation (13) 🆕

### threestudio
- **What:** Unified text-to-3D framework (SDS-based) with exportable geometry+texture refinement stages.
- **URL:** https://github.com/threestudio-project/threestudio
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted, heavy GPU
- **Impact:** 4/5 · **Difficulty:** 4/5
- **Notes:** Best testbed for bolting detail stages on.

### Neuralangelo 🚫
- **What:** NVIDIA neural SDF reconstruction with numerical gradients + coarse-to-fine hash grids — recovers fine surface detail from multi-view.
- **URL:** https://github.com/NVlabs/neuralangelo
- **License:** NVIDIA Source Code License-NC (LICENSE.md head) → RESEARCH ONLY
- **Free tier:** Self-hosted, heavy GPU
- **Impact:** 4/5 · **Difficulty:** 5/5
- **Notes:** The detail-reconstruction reference to beat; study its hash-grid detail schedule.

### DN-Splatter
- **What:** Depth-and-normal regularized 3D Gaussian Splatting — surface-aligned Gaussians that mesh far more cleanly.
- **URL:** https://github.com/maturk/dn-splatter
- **License:** Apache-2.0 (GitHub API)
- **Free tier:** Self-hosted, GPU
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Practical pick for the "scan → clean mesh" path.

### PyTorch3D
- **What:** Meta's differentiable rendering + 3D ops: marching cubes/tetrahedra, mesh subdivision, UV texturing ops, chamfer losses.
- **URL:** https://github.com/facebookresearch/pytorch3d
- **License:** BSD (LICENSE head — Meta Platforms, Inc.)
- **Free tier:** Self-hosted (pip)
- **Impact:** 4/5 · **Difficulty:** 3/5
- **Notes:** Permissive workhorse for any differentiable mesh-extraction/detail stage we build.

### nvdiffrec 🚫
- **What:** Image-based 3D reconstruction with DMTet topology — joint geometry/material optimization.
- **URL:** https://github.com/NVlabs/nvdiffrec
- **License:** NVIDIA Source Code License-NC → RESEARCH ONLY
- **Free tier:** Self-hosted, GPU
- **Impact:** 3/5 · **Difficulty:** 4/5
- **Notes:** DMTet is the topology-relevant piece; NC means reimplement, don't ship.

### FlexiCubes
- **What:** Flexible differentiable isosurface extraction — learnable vertex/weight parameters on dual marching cubes, better topology than vanilla MC.
- **URL:** https://github.com/nv-tlabs/FlexiCubes
- **License:** Apache-2.0 (GitHub API) — use the STANDALONE repo; Kaolin's copy sits under kaolin.non_commercial
- **Free tier:** Self-hosted (pip)
- **Impact:** 5/5 · **Difficulty:** 3/5
- **Notes:** Highest-impact topology entry; the topology gap's best permissive-license tool.

### Kaolin
- **What:** NVIDIA's 3D deep-learning library: differentiable rendering, DMTet, mesh ops, point clouds.
- **URL:** https://github.com/NVIDIAGameWorks/kaolin
- **License:** Apache-2.0 (GitHub API) BUT FlexiCubes inside sits under kaolin.non_commercial → mixed; prefer standalone FlexiCubes + PyTorch3D
- **Free tier:** Self-hosted (pip)
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Useful library with a license wrinkle to respect.

### torch-ngp
- **What:** Clean PyTorch reimplementation of Instant-NGP with marching-cubes mesh export from trained NeRFs.
- **URL:** https://github.com/ashawkey/torch-ngp
- **License:** MIT (GitHub API)
- **Free tier:** Self-hosted, GPU
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** MIT-licensed NeRF→mesh path without touching NVIDIA's NC Instant-NGP code.

### GOF (Gaussian Opacity Fields) 🚫
- **What:** Direct level-set mesh extraction from 3D Gaussians via adaptive marching tetrahedra — detail-preserving, compact.
- **URL:** https://github.com/autonomousvision/gaussian-opacity-fields
- **License:** Inria Gaussian-Splatting License (research only) → RESEARCH ONLY
- **Free tier:** Self-hosted, GPU
- **Impact:** 4/5 · **Difficulty:** 4/5
- **Notes:** Best-in-class 3DGS→mesh geometry; NC means study-and-reimplement.

### SOF (Sorted Opacity Fields) 🚫
- **What:** Successor to GOF: ~10x faster extraction, better unbounded scenes + detail preservation.
- **URL:** https://github.com/r4dl/SOF
- **License:** Inria Gaussian-Splatting License → RESEARCH ONLY
- **Free tier:** Self-hosted, GPU
- **Impact:** 3/5 · **Difficulty:** 4/5
- **Notes:** Newer, tiny repo — watch, don't build on yet.

### PGSR 🚫
- **What:** Planar-based 3D Gaussians enforcing cross-view appearance+geometry consistency.
- **URL:** https://github.com/zju3dv/PGSR
- **License:** Research/educational/non-profit only → NON-COMMERCIAL
- **Free tier:** Self-hosted, GPU
- **Impact:** 3/5 · **Difficulty:** 4/5
- **Notes:** The cross-view consistency regularization is the transferable idea.

### Gaussian Surfels ❓
- **What:** Disk-like (2D) Gaussians with normal consistency for surface modeling.
- **URL:** https://github.com/turandai/gaussian_surfels
- **License:** UNVERIFIED (no license file) → reference only
- **Free tier:** Self-hosted, GPU
- **Impact:** 2/5 · **Difficulty:** 4/5
- **Notes:** Technique reference only.

### GS2Mesh ❓
- **What:** Pre-trained stereo model as geometric prior to extract smooth meshes from noisy Gaussian clouds.
- **URL:** https://github.com/yanivw12/gs2mesh
- **License:** UNVERIFIED (no license file) → reference only
- **Free tier:** Self-hosted, GPU
- **Impact:** 2/5 · **Difficulty:** 4/5
- **Notes:** The "stereo prior cleans noisy Gaussians" idea is portable; code is not.

---

## 10. Blender add-ons & vanilla tools (15) 🆕

> All Blender add-ons are GPL by ecosystem → QUARANTINE (document-only).
> Vanilla Blender 4.2 tools are always safe to script via bpy.

### RetopoFlow ⛔
- **What:** Premier Blender retopology suite (Contours/PolyStrips/PolyPen/Strokes).
- **URL:** https://github.com/CGCookie/retopoflow
- **License:** GPL → QUARANTINE
- **Free tier:** Source free; v3 also sold commercially
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Study the stroke UX; reimplement ideas in vanilla bpy.

### TexTools ⛔
- **What:** Professional UV + texture toolset: texel-density tools, UV channels, baking helpers.
- **URL:** https://github.com/franMarz/TexTools-Blender
- **License:** GPL-3.0 → QUARANTINE
- **Free tier:** Free
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Texel-density workflow is the key idea to reimplement.

### UV Squares ⛔
- **What:** Reshape UV islands to grid / straighten UVs.
- **URL:** https://github.com/Radivarig/UvSquares
- **License:** GPL-2.0 → QUARANTINE
- **Free tier:** Free
- **Impact:** 2/5 · **Difficulty:** 2/5
- **Notes:** Easy to reimplement in vanilla bpy.

### Magic UV ⛔
- **What:** UV manipulation toolkit (copy/paste UVs, align, world-scale UVs).
- **URL:** https://github.com/nutti/Magic-UV
- **License:** GPL-2.0 → QUARANTINE
- **Free tier:** Free
- **Impact:** 2/5 · **Difficulty:** 2/5
- **Notes:** Mine for operator ideas.

### Layer Painter ⛔
- **What:** Substance-style layer stack for PBR material painting inside Blender.
- **URL:** https://github.com/joshuaKnauber/layer_painter
- **License:** GPL-3.0 → QUARANTINE
- **Free tier:** Free
- **Impact:** 3/5 · **Difficulty:** 3/5
- **Notes:** Layer-stack UX is the reference design for in-Blender texture editing.

### MESHmachine (paid, note only)
- **What:** Hard-surface mesh modeling: chamfer↔fillet, normal transfers, boolean cleanup.
- **URL:** https://machin3.io/MESHmachine/
- **License:** Paid commercial
- **Free tier:** None
- **Impact:** 3/5 · **Difficulty:** 2/5
- **Notes:** Normal-transfer tools are the gold standard for detail preservation.

### Quad Remesher (paid, note only)
- **What:** ZRemesher-class one-click auto-retopology.
- **URL:** https://exoside.com/quadremesher/
- **License:** Paid commercial ($59.90 indie / $109.90 pro)
- **Free tier:** Trial only
- **Impact:** 5/5 · **Difficulty:** 1/5
- **Notes:** The topology gold standard — benchmark target.

### Zen UV (paid, note only)
- **What:** Full UV pipeline: Zen Unwrap, texel density, island stacking, trim sheets.
- **URL:** https://superhivemarket.com/products/zen-uv
- **License:** Paid ($24–39)
- **Free tier:** None
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** Fastest UV-quality win for manual work (buy).

### Bake Wrangler (paid, note only)
- **What:** Node-based baking: curvature/cavity/thickness/bevel/ID maps, UDIM, batch + background.
- **URL:** https://gum.co/bake-wrangler
- **License:** Paid commercial
- **Free tier:** None
- **Impact:** 4/5 · **Difficulty:** 1/5
- **Notes:** Reimplement the pass checklist (curvature/cavity/thickness/ID) in vanilla bpy.

### SpeedRetopo (paid, note only)
- **What:** Fast manual retopo kit (grease-pencil strokes → shrinkwrapped quads).
- **URL:** https://superhivemarket.com/products/speedretopo
- **License:** Paid $7.50 (listing states GPL)
- **Free tier:** None
- **Impact:** 2/5 · **Difficulty:** 1/5
- **Notes:** Thin wrapper over vanilla tools — reproducible in vanilla bpy for free.

### SimplyBake (paid, note only)
- **What:** One-click PBR + Cycles bake-mode baking with presets and background queue.
- **URL:** Blender Market ("SimpleBake")
- **License:** Paid commercial
- **Free tier:** None
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** Defines the target bake-pass checklist.

### Multires + Dyntopo (vanilla Blender)
- **What:** Non-destructive subdivision levels for sculpting detail layers; dynamic tessellation under the brush.
- **URL:** https://docs.blender.org (Adaptive Sculpting manual)
- **License:** Vanilla Blender — bpy-scripting our own usage always safe
- **Free tier:** Built-in
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Standard detail-sculpting workflow; detail lives on higher levels, clean base preserved.

### Shrinkwrap retopo workflow (vanilla Blender)
- **What:** Project a clean low-poly cage onto the high-poly surface; standard manual-retopo backbone.
- **URL:** https://docs.blender.org/manual/en/4.2/modeling/modifiers/deform/shrinkwrap.html
- **License:** Vanilla Blender — safe to script
- **Free tier:** Built-in
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Core of any automated retopo pass we build.

### Data Transfer modifier (vanilla Blender)
- **What:** Transfers UV maps, vertex colors, custom normals, vertex groups between meshes.
- **URL:** https://docs.blender.org (Data Transfer Modifier manual)
- **License:** Vanilla Blender — safe to script
- **Free tier:** Built-in
- **Impact:** 4/5 · **Difficulty:** 2/5
- **Notes:** Detail-preservation bridge — bake high-poly detail onto retopo'd low-poly.

### Remesh modifier Voxel/Blocks/Smooth/Sharp (vanilla Blender)
- **What:** Generates new manifold topology from input; Voxel mode produces watertight meshes.
- **URL:** https://docs.blender.org/manual/en/4.2/modeling/modifiers/generate/remesh.html
- **License:** Vanilla Blender — safe to script
- **Free tier:** Built-in
- **Impact:** 3/5 · **Difficulty:** 1/5
- **Notes:** Voxel remesh = free watertight pass. NOTE: Quadriflow is NOT in Blender 4.2 (removed in 4.0).

---

## Wave-2 queue (priority backlog for the next wave)

1. **MikkTSpace** — drop-in tangent basis for correct normal maps (impact 5, difficulty 1).
2. **DiffBIR / OSEDiff / CCSR** — Apache diffusion SR for the texture stage (GPU lane).
3. **CaPa** — 4K-in-30s paint stage (BSD-3, GPU lane).
4. **Instant Meshes** — BSD-3 quad remesh CLI wrapper.
5. **QuadriFlow** — BSD-3 batch auto-retopo (`BUILD_FREE_LICENSE=ON`).
6. **FlexiCubes standalone** — Apache-2.0 differentiable extraction.
7. **MatFuse / Material Anything** — MIT full-PBR synthesis (GPU lane).
8. **FlashTex** — Apache-2.0 relightable texturing (GPU lane).
9. **LaMa** — Apache-2.0 inpainting for seam/completion repair.
10. **StableNormal** — Apache-2.0 sharp normals → detail synthesis.
11. **meshoptimizer / geometry-central / ACVD / Mmg** — remesh backends.
12. **three-gpu-baker** — MIT browser-native baking for the PWA.
13. **PyMeshLab worker-process** — GPL-quarantined Taubin/remesh/AO stage.
14. **Real-ESRGAN v3 weights** — drop-in upgrade to existing upscale stage.
15. **Bake-pass checklist** (curvature/cavity/thickness/ID) in vanilla bpy.

## License red-flag summary (wave 1)

- **GPL/AGPL quarantine (never in shipped tree):** PyMeshLab, gpytoolbox, libigl-python-bindings, QuadWild, RetopoFlow, Tissue, PolyQuilt, Magic UV, TexTools, UvSquares, UniV, Laigter, AwesomeBump, Materialize, EZ Baker, DeepBump, APISR, Blender itself (scripting use is fine).
- **NC / research-only (research lane):** SUPIR (custom), FeMaSR, StableSR/ResShift/InvSR/SinSR (S-Lab 1.0), DeepFillv2, EdgeConnect, DSINE, Omnidata, Neuralangelo, nvdiffrec, GOF, SOF, PGSR, Generative Repainting 3D Assets, Text2Tex, CodeFormer, ManifoldPlus, DUST3R, MASt3R, VGGT.
- **Unverified (do not wire):** DFOSD, MultiDiffusion, RePaint, L0Mesh, pybaker, Gaussian Surfels, GS2Mesh, MaterialGAN, TANGO.
- **Paid (note only):** Exoside QuadRemesher, ZRemesher, Zen UV, Headus UVLayout, Knald, Marmoset Toolbag, Substance 3D Painter, MESHmachine, Bake Wrangler, SpeedRetopo, SimplyBake, RizomUV.
- **License corrections this wave:** OpenVDB = Apache-2.0 (not MPL); Materialize = GPL-3.0 (open source, not freeware); Blender 4.2 has NO Quadriflow modifier; Kaolin's FlexiCubes copy is NC (use standalone repo); CaPa README footer "© NCSOFT" loses to its BSD-3 LICENSE file.

## Entry count

- Categories 1–3 (texture SR / synthesis / detail): 37 entries
- Categories 4–7 (mesh / topology / UV / baking): 40 entries
- Categories 8–10 (multiview / scan / Blender): 36 entries
- **Wave-1 total: 113 new entries**, all license-verified from source.
