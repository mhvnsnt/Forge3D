# Open-Source Image-to-3D / Text-to-3D Model Verification (2026-10-06)

Verified via live web search on 2026-10-06. Training knowledge NOT trusted for licenses.

## Model-by-model findings

### 1. TripoSR (Stability AI × Tripo AI)
- **License:** MIT (code + weights). Commercial-safe.
- **Hardware:** ~6 GB VRAM minimum (half-precision); ~0.5s on A100, ~5–15s on RTX 3060. CPU-only works: ~30–60s to 2–10 min per asset.
- **Input:** single image → 3D (feed-forward LRM, no text).
- **Output:** mesh (OBJ/GLB) with baked vertex/projection texture; ~100K polys. No UV-unwrap (vertex colors in some wrappers); normals can flip.
- **Source:** https://github.com/VAST-AI-Research/TripoSR
- **Verdict:** the low-hardware fallback, not the quality pick.

### 2. TRELLIS (Microsoft, CVPR'25 Spotlight)
- **License:** MIT (code + weights) — BUT depends on NVIDIA nvdiffrast (NVIDIA non-commercial source license) in the v1 pipeline. Commercial deploys should swap the rasterizer or check terms.
- **Hardware:** ~16 GB VRAM (v1). CPU: no.
- **Input:** text-to-3D AND image-to-3D (structured SLAT latents).
- **Output:** mesh + texture, Gaussian splat export too.
- **Source:** https://github.com/microsoft/TRELLIS

### 2b. TRELLIS.2 (Microsoft, late 2025) — NEW, flag this
- **License:** MIT (code + weights); v2 removes nvdiffrast/kaolin deps (field-free O-Voxel). Clean commercial license.
- **Hardware:** 24 GB VRAM recommended (16 GB fp16/low-res path exists). Linux-only custom CUDA ops. CPU: no.
- **Input:** image (and text) → 3D, accepts up to ~16 multi-views as conditioning.
- **Output:** PBR-textured mesh (albedo/rough/metal/normal) up to 1536³ effective res; dedicated texturing stage.
- **Quality:** community head-to-heads through 2026 consistently rank TRELLIS.2 #1 (one published comparison: 68% preference vs 24% Hunyuan3D).
- **Sources:** https://github.com/microsoft/TRELLIS.2 , https://huggingface.co/microsoft/TRELLIS.2-4B
- **Verdict:** best quality + cleanest license, but needs serious GPU. NOT a free-tier-GPU model.

### 3. Shap-E (OpenAI)
- **License:** MIT. Commercial-safe.
- **Hardware:** small (~2–4 GB weights); runs on GPU, hours on CPU. GPU recommended.
- **Input:** text-to-3D and image-to-3D (CLIP-conditioned latent diffusion → implicit function).
- **Output:** implicit function decoded to (low-quality) textured mesh.
- **Quality tier:** 2023-era; outclassed by everything above for character fidelity. 2026 use = education/prototyping only.
- **Source:** https://github.com/openai/shap-e

### 4. Point-E (OpenAI)
- **License:** MIT. Commercial-safe.
- **Hardware:** very light (V100 1–2 min per asset; 2022-era model, small).
- **Input:** text-to-image-to-3D, image-to-point-cloud.
- **Output:** point cloud (4096 pts), optional SDF→mesh conversion — blocky, low detail.
- **Verdict:** obsolete as a character generator; useful only as a fast baseline.
- **Source:** https://github.com/openai/point-e

### 5. InstantMesh (TencentARC)
- **License:** Apache-2.0 (code + weights). Commercial-safe. (Some third-party notes say MIT — the official repo license is Apache-2.0; both are permissive.)
- **Hardware:** ~12–16 GB VRAM (large variant); Zero123++ multi-view stage is the heavy part. CPU: impractical.
- **Input:** single image → 6 sparse views (Zero123++ inside) → LRM reconstruction.
- **Output:** textured mesh (OBJ vertex-color default, texture-map export with --export_texmap). Not PBR-native.
- **Source:** https://github.com/TencentARC/InstantMesh

### 6. Zero123++
- **License:** code Apache-2.0, **weights CC-BY-NC 4.0 (non-commercial)**. ⚠️ Cannot be used in a commercial product pipeline; outputs themselves are free to use.
- **Input:** single image → 6 consistent multi-views (2×3 tile grid).
- **Output:** images only (needs downstream reconstructor like InstantMesh/CRM).
- **Source:** https://github.com/SUDO-AI-3D/zero123plus

### 7. Stable Fast 3D / SF3D (Stability AI) — re-verified
- **License:** **Stability AI Community License — NOT non-commercial-only, and NOT MIT.** Free for research, non-commercial, AND commercial use by entities under **$1M annual revenue**. Above $1M → Enterprise license required. Gated HF checkpoint (must accept license).
- **Hardware:** ~7–9 GB VRAM; 0.5s on A100-class. CPU: no (no CPU support).
- **Input:** single image → 3D.
- **Output:** GLB with UV-unwrapped mesh + albedo/normal/metallic-roughness (de-lit). Quality = TripoSR successor, below TRELLIS/Hunyuan.
- **Source:** https://github.com/Stability-AI/stable-fast-3d , https://huggingface.co/stabilityai/stable-fast-3d
- **Commercial verdict:** SAFE for us (well under $1M revenue). Good game-ready topology.

### 8. Hunyuan3D-2 / 2.1 (Tencent) — NOT Apache-2.0
- **License:** **Tencent Hunyuan 3D Community License (2.1)** — NOT permissive. Restrictions: (a) **territory exclusion: EU, UK, South Korea — prohibited there**; (b) **>1M MAU → must request separate license from Tencent**; (c) must ship Notice + "Powered by Tencent Hunyuan" attribution; (d) **may not use outputs to train other AI models**. Outputs belong to the user.
- **Hardware (2.1):** ~10 GB VRAM shape-only, ~21 GB texture stage, **~29 GB full pipeline**. NF4/FP8 + CPU offload can bound peak to ~13.4 GB with <1.5% quality drop; low-VRAM builds target 8 GB (shape only). CPU: impractical.
- **Input:** image-to-3D and text-to-3D (2.1). 2mv variant takes labeled multi-views.
- **Output:** PBR-textured GLB (albedo + metallic-roughness + geometry, 200–500K tris). Best open PBR paint of the 2.x line.
- **Sources:** https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 , https://github.com/Tencent-Hunyuan/Hunyuan3D-2
- **Commercial verdict:** usable in US/GA (Tennessee/Georgia fine) under 1M MAU, but the EU/UK/SK exclusion and Tencent brand-attribution make it a licensed-tier option, NOT clean open source.

### 9. Hunyuan3D-Paint (texture generation)
- **License:** ships under the same Tencent Hunyuan 3D Community License family (texture stage of the 2.x pipeline; 1.3B model). Same territory/MAU restrictions.
- **What it does:** textures YOUR existing mesh from a reference image → PBR maps (albedo, metallic-roughness), 4096² UV bake. This is the most useful piece — bake textures onto any generated/rigged mesh.
- **Note:** Hunyuan3D-Paint v2.5 exists in the -2.1 line (Paint-PBR 2.8B).

### 10/14. SPAR3D = Stable Point Aware 3D (Stability AI, CVPR 2025) — same model
- Repo https://github.com/Stability-AI/stable-point-aware-3d IS SPAR3D ("SPAR3D: Stable Point-Aware Reconstruction of 3D Objects from Single Images", arXiv 2501.04689). Two-stage: point-cloud diffusion → mesh conditioned on point cloud + image.
- **License:** **Stability AI Community License** (same as SF3D: free under $1M revenue).
- **Hardware:** ~16 GB VRAM reported; 0.7s inference on GPU. CPU: no.
- **Input:** single image → 3D; editable point-cloud intermediate (delete/duplicate/stretch/recolor).
- **Output:** detailed mesh, improved backside vs SF3D.
- **Commercial verdict:** SAFE under $1M revenue.

### 11. Unique3D (Tsinghua/AiuniAI)
- **License:** MIT. Commercial-safe.
- **Hardware:** multi-view diffusion + ISOMER reconstruction, ~30s on GPU; ~12–16 GB class. CPU: impractical.
- **Input:** single image → 6-view diffusion → high-fidelity textured mesh with normals.
- **Output:** textured mesh, fine detail (buttons, straps) preserved — strong for hero props/characters.
- **Source:** https://github.com/AiuniAI/Unique3D

### 12. CRM — Convolutional Reconstruction Model (Tsinghua, thu-ml/CRM)
- **License:** MIT. Commercial-safe.
- **Hardware:** modest (10s generation on a single GPU; ~8–12 GB class). CPU: possible but slow.
- **Input:** single image → 3D (convolutional, feed-forward).
- **Output:** textured mesh in 10 seconds.
- **Source:** https://github.com/thu-ml/CRM
- **Note:** 2024-era; quality below current leaders but fast and permissive.

### 13. LGM — Large Multi-view Gaussian Model (3DTopia/ashawkey)
- **License:** MIT. Commercial-safe.
- **Hardware:** ~3B params; fast (~5s on 4090), lower VRAM than diffusion. CPU: impractical.
- **Input:** 1–4 multi-view images (can synthesize views first with Zero123++/SV3D).
- **Output:** **Gaussian splat**, not a mesh (mesh extraction is best-effort post-process).
- **Source:** https://github.com/3DTopia/LGM
- **Verdict:** wrong output type for character meshes unless the pipeline adopts splats.

## NEW 2026 models you missed (late 2025 / 2026)

1. **TRELLIS.2 (Microsoft, Dec 2025)** — MIT, PBR to 4K, current open SOTA. 24 GB VRAM. See 2b.
2. **TripoSG (VAST AI / Tripo, 2025)** — MIT, 1.5B shape-generation model, **8–12 GB VRAM**, watertight manifold meshes, geometry-only (bake textures separately). The best MIT-licensed low-VRAM option after TripoSR. https://github.com/VAST-AI-Research/TripoSG
3. **Hi3DGen / Stable3DGen (Stable-X, 2025)** — MIT, TRELLIS fork with normal-bridging, **removed nvdiffrast/kaolin deps → commercially cleaner than upstream TRELLIS**, best raw geometric detail of 2025 class. Geometry-only (no integrated texture). https://github.com/Stable-X/Hi3DGen
4. **Step1X-3D (StepFun, 2025)** — **Apache-2.0**, high-fidelity controllable textured 3D assets, text/image → 3D. https://github.com/Yuan-ManX/Step1X-3D
5. **TripoSplat (VAST AI, June 2026)** — MIT, single image → 3D Gaussians (splat output). https://github.com/VAST-AI-Research/TripoSplat
6. **GRM (Microsoft, 2026)** — MIT, multi-view → Gaussian splat, 2–4 views. https://github.com/microsoft/GRM
7. **Meta SAM 3D / AssetGen 2.0** — SAM-license / internal; not generally available (AssetGen 2.0 is Meta-internal for Horizon worlds).
8. **CSM acquired by Alphabet/Google (Jan 2026)** — verify CSM API endpoints before depending on them.
9. Also on the horizon: Pixal3D (Tencent, MIT 2026), PartCrafter (NeurIPS 2025, part-aware image-to-3D).

## Ranked verdict: best free/open single-image → textured character mesh on limited hardware

Constraints: free-tier GPU or CPU, clean-enough commercial license, textured output.

| Rank | Model | License | Min VRAM | Why |
|---|---|---|---|---|
| **#1** | **Stable Fast 3D (SF3D)** | Stability AI Community License (free < $1M revenue — safe for us) | ~7–9 GB | Textured GLB with proper UV unwrapping + de-lit albedo/normal/PBR scalars out of the box, sub-second on GPU, game-ready topology. Best quality-per-VRAM among textured models that fit free-tier GPUs (Colab T4 16GB, RTX 3060). |
| #2 | TripoSG | MIT | 8–12 GB | Clean MIT license (no revenue cap), watertight manifold geometry, better shape quality than TripoSR — but geometry-only, so texture must be baked separately (e.g. via Hunyuan3D-Paint stage or Blender). |
| #3 | TripoSR | MIT | ~6 GB | Runs on the weakest hardware incl. CPU (~1–2 min), MIT — but 2024-era quality, no UV unwrap, normals flip. Prototype/draft tier. |
| #4 | Unique3D | MIT | 12–16 GB | MIT + best texture detail in the permissive class; needs more VRAM, ~30s per asset. Hero-asset candidate if you have 16 GB. |
| (hero) | TRELLIS.2 | MIT | 24 GB (16 GB fp16) | Absolute quality + license king — but does NOT fit free-tier GPUs; run it on a rented/Colab-Pro GPU or as an API. |
| (hero, gated) | Hunyuan3D-2.1 | Tencent Community (EU/UK/SK excluded, 1M MAU cap) | 29 GB (13.4 GB quantized) | Best open PBR paint; use only if you accept the territory restriction + attribution. Its **Paint stage is worth pulling** to texture meshes from other generators. |

**Bottom line:** For Forge3D on limited hardware, wire **SF3D as the default image→textured-character-mesh backend** (commercial-safe under the $1M cap, fits a T4/3060), **TripoSG as the MIT-clean shape fallback** (license bulletproof forever), and pull **Hunyuan3D-Paint** as a texture-refinement stage. Keep **TRELLIS.2** as the hero-asset backend for runs with a real GPU.

## Hard no-go's (for this project)
- Zero123++ weights: CC-BY-NC 4.0 — no commercial pipeline use.
- Hunyuan3D-2/2.1 weights: territory exclusion (EU/UK/SK), 1M MAU gate, "Powered by Tencent Hunyuan" attribution, no-training-use clause — not Apache-2.0.
- LGM/TripoSplat/GRM: splat output, not character meshes.

## License-policy note (per standing rule)
Prototype freely; before ship: GPL/AGPL quarantine + license manifest. Relevant here: nvdiffrast (TRELLIS v1 dep, non-commercial) is already removed in TRELLIS.2/Hi3DGen — prefer those two if TRELLIS-family code ships.
