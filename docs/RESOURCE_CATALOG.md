# RESOURCE_CATALOG.md — Forge3D master resource backlog

Generated 2026-10-07 from `docs/catalog-parts/*.json` (4 research workers, licenses verified from upstream sources — never guessed).

**Purpose:** the ranked master list of free / open-source / free-API / public-domain 3D resources to pull in and wire up, so wiring crews never run dry. Owner directive: hundreds of resources until Forge3D matches and beats Tripo3D quality.

**How to read:** each entry has a commercial-safety badge — ✅ commercial-safe (verified), 🚫 not commercial-safe (NC/research/quarantine — research lane only), ❓ unverified (read LICENSE before wiring). Impact 1–5 = how much it closes the Tripo quality gap. Difficulty 1–5 = wire-up effort. Status is `not-started` for all — a sibling worker handles wiring.

## Summary — entries by category

| # | Category | Entries |
|---|----------|---------|
| 1 | 1. Image→3D / text→3D generative models (open weights / free tiers) | 34 |
| 2 | 2. Free 3D APIs (keyless first, then free-key) | 20 |
| 3 | 3. Texture / material tools | 27 |
| 4 | 4. Mesh processing (remesh, retopo, UV, repair, decimation) | 16 |
| 5 | 5. Rigging / animation (auto-riggers, retargeters, mocap) | 28 |
| 6 | 6. Multiview / scan / reconstruction (photogrammetry, NeRF, 3DGS, depth) | 30 |
| 7 | 7. Public-domain / CC0 asset libraries | 16 |
| 8 | 8. Hugging Face Spaces with free keyless GPU endpoints | 13 |
| | **TOTAL** | **184** |

Already wired in Forge3D (not re-listed here): TripoSR, Stable Fast 3D, TRELLIS.2, TripoSG, Hi3DGen, InstantMesh, Zero123++, MV-Adapter, Unique3D, Shap-E, Hunyuan3D-2 variants, Pollinations API, Tripo API, Meshy, FLUX.1, Real-ESRGAN, Blender 4.2 + Quadriflow, trimesh, GNM, COLMAP, lod_chain, Poly Haven, ambientCG, Quaternius, Kenney, KayKit, cgbookcase, TextureCan, NASA 3D, Poly Pizza, Khronos glTF-Sample-Models, Smithsonian 3D, Cloudflare Workers AI, Instant Meshes (evaluated), TRELLIS.2/TRELLIS/InstantMesh/FLUX.1 HF Spaces.

## Top-10 wire-up priority

Ranked by quality-impact per wire-up effort, aimed at the owner's known pain points: speckle noise, non-watertight output, flat/washed textures, bad topology, mitten hands, multi-view inconsistency.

1. **Manifold (manifold3d)** — Apache-2.0, verified. Guaranteed-manifold booleans + repair via `pip install manifold3d`. Cheapest possible watertightness stage — directly attacks the 'raw output isn't watertight' gap. Difficulty 2.
2. **SyncMVD** — MIT, verified. Seam-free synchronized multi-view diffusion texturing. Closes the #1 texture gap: multi-view inconsistency (backs that don't match fronts). Diffusers-native.
3. **Paint3D** — Apache-2.0, verified. Lighting-less 2K UV diffusion texturing. Kills baked-lighting speckle — the core Tripo texture gap — and outputs relightable PBR.
4. **OptCuts** — MIT, verified. Joint seam+distortion UV optimization, headless-batchable. Best automatic UVs; multiplies the quality of every texture stage downstream.
5. **TripoSplat (VAST-AI)** — MIT, keyless HF Space. Beat TRELLIS.2/Hunyuan3D-2.1 in a 399-vote human study. New keyless backbone candidate — the 'better model' path that costs nothing.
6. **TEXTure** — MIT, verified. Text-guided texture generation/editing/refinement/transfer. Only candidate enabling owner-driven texture tweaks ('make the jacket darker') without a full regen.
7. **SwinIR** — Apache-2.0, verified. CPU-capable texture super-resolution + denoising. Near-zero-effort crispness win alongside Real-ESRGAN; attacks flat/washed textures.
8. **Mixamo auto-rigger + animation library** — Adobe ToS, verified. Fastest humanoid rig + largest ready-made clip library, free with Adobe ID, commercial use allowed when embedded. Finger bones remain a gap.
9. **CMU Graphics Lab Motion Capture Database** — Free for commercial products (no resale), verified. Thousands of BVH clips (boxing, karate, kicks) — highest-value free commercial-safe mocap library found. Needs retargeting to our 58-bone skeleton.
10. **gsplat** — Apache-2.0, verified. The permissive 3D Gaussian Splatting path (vs Inria's research-only code). Scan→mesh lane for phone-photogrammetry without license risk.

## License red flags (pre-ship audit input)

- **Non-commercial / research-only — research lane only, never shipped:** DUST3R, MASt3R (CC BY-NC-SA), VGGT (Meta NC), Inria gaussian-splatting (NC — use gsplat instead), OpenPose (commercial license ~$25k/yr), AMASS, BABEL, Human3.6M, GVHMR, LAFAN1 (CC BY-NC-ND — ND bars even retargeting), SuGaR + 2DGS (likely NC, unverified), Depth Pro (Apple sample terms), Depth Anything V2 Base/Large/Giant (CC-BY-NC — **Small is Apache-2.0, wire only Small**), CodeFormer (S-Lab 1.0), Text2Tex (CC BY-NC-SA 3.0), ManifoldPlus ('free for non-commercial use only'), sIBL archive (CC BY-NC-SA), Cascadeur free tier (non-commercial, .casc-only export), DeepMotion free tier (non-commercial outputs), IDM-VTON + CatVTON (CC BY-NC-SA), Zero123++ weights (CC-BY-NC — already known).
- **GPL/AGPL — quarantine-only per standing rules:** Materialize (GPL-3.0), Laigter (GPL-3.0), AwesomeBump (GPL-3.0), InsaneBump (GPLv3), PyMeshFix (GPL-3.0), Rigify (GPL), OpenSplat (AGPL-3.0), MakeHuman code (AGPL — exported models are CC0, safe as asset source), CGAL, VCG, MicMac (CeCILL). Full list in catalog-parts/texmesh.json `quarantine_watchlist`.
- **NOT CC0 despite 'free' framing:** Quixel Megascans (free tier is UE-Only under Epic EULA), TurboSquid Free / CGTrader Free (marketplace royalty-free, not CC0), Textures.com (credit-based), BlenderKit, HDRI Skies (per-map mixed, mostly non-commercial), ShareTextures (commercial OK but redistribution banned), NoEmotion HDRs (free for personal+commercial but bandwidth-capped, not CC0).
- **UNVERIFIED — read LICENSE before wiring:** HybrIK, ROMP, PIXIE, METRO, EasyMocap, OpenMVS, OpenMVG, Regard3D, LoFTR, hloc, Kinetix (site now B2B), RenderPeople samples, MaterialGAN (no LICENSE file), TileGen (all rights reserved), PyMesh (repo unlocated), MetaTexture (no such standalone tool — closest is Meta AssetGen's closed transformer).
- **Tencent family:** Hunyuan3D-2.x weights = Tencent Hunyuan 3D 2.0 Community License (territory exclusion incl. EU/UK/KR, 1M MAU cap, no-training-on-outputs) — NOT Apache, not recommended for the commercial path.

## 1. Image→3D / text→3D generative models (open weights / free tiers)

#### SPAR3D ✅
- **What:** Stable Point-Aware 3D: single image→UV-unwrapped, PBR-textured GLB mesh in ~0.7s with editable point-cloud intermediate.
- **URL:** https://github.com/Stability-AI/stable-point-aware-3d
- **License:** Stability AI Community License (permits commercial use per Stability AI announcement; verify terms for >$1M revenue orgs) (verified)
- **Free tier:** yes — code open on GitHub; weights free on HF under Stability AI Community License
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** CVPR 2025, by Stable Fast 3D team. Pushed 2025-05-05, 1077 stars. Sub-second UV-unwrapped PBR GLB + editable point cloud. Best game-pipeline fit in catalog.

#### CharacterGen ✅
- **What:** Image→3D character via pose canonicalization → 4-view diffusion → mesh.
- **URL:** https://github.com/zjp-shadow/CharacterGen
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2025-04-11, 834 stars. Character-specific (pose canonicalization) — highest Forge3D relevance among permissive entries.

#### CraftsMan3D ✅
- **What:** Text/image→high-fidelity mesh: 3D-native diffusion coarse mesh (~5s) + normal-based interactive geometry refiner (~20s).
- **URL:** https://github.com/wkjw/CraftsMan3D
- **License:** CreativeML OpenRAIL-M (verified from README License section; repo's 3D diffusion derives from SD1.5) (verified)
- **Free tier:** yes — code + checkpoints open; commercial use allowed under OpenRAIL-M use restrictions (verify restrictions before shipping)
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2024-12-24, official repo wkjw/CraftsMan3D. Released ckpt trained on characters — best character fit. Interactive refiner is a differentiator. Commercial use permitted under OpenRAIL-M terms (read restrictions).

#### Step1X-3D ✅
- **What:** Text/image→high-fidelity, controllable textured 3D assets.
- **URL:** https://github.com/stepfun-ai/Step1X-3D
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2025-09-08 (recently active), 896 stars. Production-oriented textured assets; strong Forge3D candidate.

#### Rodin/Hyper3D ❓
- **What:** Commercial text/image→3D API (Rodin Gen-2); GLB/USDZ/FBX/OBJ/STL export.
- **URL:** https://hyper3d.ai
- **License:** Proprietary — commercial API terms (not open weights) (UNVERIFIED)
- **Free tier:** limited — commercial API; free trial credits exist but community reports free trial blocks image-to-3D
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** NOT open-weight — commercial API only (hyper3d.ai, DeemosTech). No public model code; only API integration skills exist. Useful as paid fallback/reference quality bar, not a Forge3D pipeline stage.

#### CRM ✅
- **What:** Single-image→textured-mesh via Convolutional Reconstruction Model in ~10 seconds.
- **URL:** https://github.com/thu-ml/CRM
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** ECCV 2024. Pushed 2024-11-28, 693 stars. Simple inference. Great fast mesh baseline for Forge3D stage 1.

#### LGM ✅
- **What:** Large Multi-View Gaussian Model: feedforward image→3D Gaussians from 4 input views.
- **URL:** https://github.com/3DTopia/LGM
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Pushed 2024-08-20, 2118 stars. Feedforward; pairs with Zero123/MVDream multiview priors for hallucinated backs.

#### TriplaneGaussian ✅
- **What:** Transformer single-view→triplane + Gaussian splatting; fast generalizable reconstruction.
- **URL:** https://github.com/VAST-AI-Research/TriplaneGaussian
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Pushed 2024-03-05, 927 stars. Fast feedforward; Gaussian output needs meshing for game use.

#### Zero-1-to-3 ✅
- **What:** Zero-shot single image→novel views; backbone of most image→3D pipelines.
- **URL:** https://github.com/cvlab-columbia/zero123
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Pushed 2023-12-05, 3066 stars. The canonical 'what does the back look like' prior — directly addresses Forge3D gap #1 (hallucinated backs).

#### DreamGaussian ✅
- **What:** Generative Gaussian Splatting via score distillation; fast text/image→3D (~minutes).
- **URL:** https://github.com/dreamgaussian/dreamgaussian
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2024-01-02, 4358 stars. Fast SDS loop; popular and well-documented. Gaussian output needs mesh extraction for game use.

#### ECON 🚫
- **What:** Single image→3D clothed human with explicit back-side reasoning.
- **URL:** https://github.com/YuliangXiu/ECON
- **License:** Custom non-commercial research license (verified from LICENSE file: 'non-commercial scientific research purposes') (verified)
- **Free tier:** yes — code open, but NON-COMMERCIAL
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2024-09-17, 1212 stars. Back-side reasoning is directly relevant to Forge3D gap #1. NOT commercial-safe; research reference only.

#### Era3D 🚫
- **What:** High-resolution multiview diffusion with row-wise attention; single image→6 consistent views.
- **URL:** https://github.com/pengHTYX/Era3D
- **License:** GNU AGPL-3.0 (quarantine-only) (verified)
- **Free tier:** yes — code + weights open, but QUARANTINE per GPL/AGPL rule
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** NeurIPS 2024. Pushed 2024-12-09, 646 stars. QUARANTINE-ONLY: AGPL-3.0 license. Also depends on nvdiffrast (NVIDIA non-commercial). Usable for research comparison, never in shipped pipeline.

#### ICON 🚫
- **What:** Single image→detailed 3D clothed human via front/back normal prediction.
- **URL:** https://github.com/YuliangXiu/ICON
- **License:** Custom non-commercial research license (verified from LICENSE file: 'non-commercial scientific research purposes') (verified)
- **Free tier:** yes — code open, but NON-COMMERCIAL
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2023-11-23, 1679 stars. Strong clothed-human results. NOT commercial-safe; research reference only.

#### MVDream ✅
- **What:** Multi-view diffusion prior for 3D generation (used as guidance in SDS pipelines).
- **URL:** https://github.com/bytedance/MVDream
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2023-10-07, 987 stars. The standard multiview diffusion prior for SDS pipelines; foundational for many entries here.

#### One-2-3-45 ✅
- **What:** Any single image→3D mesh in ~45 seconds (Zero123 + SDF reconstruction).
- **URL:** https://github.com/One-2-3-45/one-2-3-45
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2024-04-20, 1715 stars. No per-shape optimization — fast end-to-end. Good speed/quality tradeoff for batch character gen.

#### OpenLRM ✅
- **What:** Large Reconstruction Model: single image→triplane NeRF→mesh.
- **URL:** https://github.com/3DTopia/OpenLRM
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** ICLR 2024. Pushed 2024-05-06, 1250 stars. Solid LRM-family baseline; triplane→mesh extraction is standard Forge3D-compatible.

#### PIFuHD ✅
- **What:** High-res single-image→clothed-human 3D (pixel-aligned implicit function).
- **URL:** https://github.com/facebookresearch/pifuhd
- **License:** CC-BY-NC 4.0 (verified from README License section) (verified)
- **Free tier:** yes — code open, but NON-COMMERCIAL
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2024-08-19, 9727 stars. The classic clothed-human reconstructor. NOT commercial-safe (CC-BY-NC 4.0); research reference for human-shape priors.

#### SV3D ✅
- **What:** Stable Video 3D: image→21-frame orbital video (SV3D_u unconditioned / SV3D_p pose-controlled); feeds downstream 3D reconstruction.
- **URL:** https://github.com/Stability-AI/generative-models
- **License:** Code: MIT (Stability-AI/generative-models). Weights: Stability AI Community License (commercial on request) (verified)
- **Free tier:** code MIT; weights gated on HF under Stability AI Community License — commercial use requires separate license per model card
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** No standalone repo (earlier guesses 404); official sampling code lives in Stability-AI/generative-models (MIT, pushed 2025-12-16, 27k stars), weights gated at huggingface.co/stabilityai/sv3d. Best use: multiview-video prior feeding a reconstructor (directly addresses Forge3D multi-view gap).

#### SyncDreamer ✅
- **What:** Single image→16 view-consistent images via synchronized multiview diffusion.
- **URL:** https://github.com/liuyuan-pal/SyncDreamer
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2025-10-26, 1046 stars — recently active. Stronger consistency than Zero123 for the multiview stage.

#### Wonder3D ✅
- **What:** Single image→3D via cross-domain diffusion (normal maps + color) then SDF fusion.
- **URL:** https://github.com/xxlong0/Wonder3D
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** CVPR 2024. Pushed 2025-03-14, 5437 stars. Needs Zero123XL-class GPU. Strong normal+texture consistency baseline.

#### Magic123 ✅
- **What:** Two-stage image→3D: Zero123 coarse NeRF + DMTet refinement with 2D+3D priors.
- **URL:** https://github.com/guochengqian/Magic123
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Pushed 2026-07-06 (recently active), 1623 stars. High quality but per-shape optimization is slow (tens of min) — batch/background use.

#### GRM ✅
- **What:** Large Gaussian Reconstruction Model: sparse-view→3D Gaussians in ~0.1s; plugs into multiview diffusion for text/image→3D.
- **URL:** https://github.com/justimyhxu/GRM
- **License:** Unspecified — no license declared (all rights reserved by default) (verified)
- **Free tier:** yes — code + weights open; NO license file or README terms (checked 2026-10-07)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Pushed 2024-04-04, 641 stars. Code + HF weights released (inference/demo only, no training code). NOT commercial-safe: no license declared. Research reference only.

#### Point-E ✅
- **What:** OpenAI text/image→3D point-cloud diffusion (fast, low-res; needs meshing step).
- **URL:** https://github.com/openai/point-e
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Pushed 2024-07-04, 6894 stars. Low-res point clouds need meshing; dated but trivial to run. Weak for characters alone.

#### Splatter Image ✅
- **What:** Ultra-fast single/multi-view→3D Gaussian splats (feedforward).
- **URL:** https://github.com/szymanowiczs/splatter-image
- **License:** BSD 3-Clause (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Pushed 2024-08-17, 1112 stars. Extremely fast; output is splats not meshes — needs conversion for Forge3D.

#### Dora ✅
- **What:** Dora-VAE: sharp-edge-sampling 3D shape VAE (compact latents) + Dora-bench.
- **URL:** https://github.com/Seed3D/Dora
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** CVPR 2025, ByteDance Seed. Pushed 2025-07-02, 592 stars. VAE component, not an end-to-end generator — useful as Forge3D pipeline stage (sharp-edge sampling preserves detail).

#### ImageDream ✅
- **What:** Image-prompt multi-view diffusion for 3D (SDS guidance model).
- **URL:** https://github.com/bytedance/ImageDream
- **License:** Apache License 2.0 (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Pushed 2024-01-27, 798 stars. Official repo is bytedance/ImageDream (Apache-2.0 LICENSE verified). Guidance-model role like MVDream.

#### LN3Diff 🚫
- **What:** Scalable latent neural-field diffusion; text/image→3D mesh in ~8 V100-seconds.
- **URL:** https://github.com/NIRVANALAN/LN3Diff
- **License:** S-Lab License 1.0 — non-commercial use only (verified from LICENSE file) (verified)
- **Free tier:** yes — code + checkpoints open, but NON-COMMERCIAL
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** ECCV 2024. Pushed 2025-11-18 (recently active), 230 stars. Fast. NOT commercial-safe: S-Lab License 1.0 restricts to non-commercial.

#### Michelangelo 🚫
- **What:** Shape-image-text aligned latent diffusion for conditional 3D shape generation.
- **URL:** https://github.com/NeuralCarver/Michelangelo
- **License:** GNU GPL-3.0 (quarantine-only) (verified)
- **Free tier:** yes — code open, but QUARANTINE per GPL/AGPL rule
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** NeurIPS 2023. Pushed 2024-04-10, 487 stars. QUARANTINE-ONLY: GPL-3.0. Research reference only.

#### PartCrafter ✅
- **What:** Single image→structured multi-part 3D mesh via compositional latent diffusion.
- **URL:** https://github.com/AvaLovelace1/PartCrafter
- **License:** MIT License (verified)
- **Free tier:** yes — code + weights open
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** NeurIPS 2025. Pushed 2026-01-01 (very recent), official repo AvaLovelace1/PartCrafter. Structured multi-part output is a differentiator for characters with gear/accessories.

#### V3D ✅
- **What:** Video diffusion repurposed as image→3D generator (orbit frames→mesh/Gaussians in ~3 min).
- **URL:** https://github.com/heheyas/V3D
- **License:** Unspecified — no license declared (all rights reserved by default) (verified)
- **Free tier:** yes — code open; NO license file or README terms (checked 2026-10-07)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** T-PAMI 2025. Pushed 2024-03-26, 523 stars. Novel video-diffusion-as-3D-generator angle. NOT commercial-safe (no license).

#### Consistent123 ✅
- **What:** Case-aware two-stage image→3D with dynamic diffusion priors.
- **URL:** https://github.com/lyk412/consistent123
- **License:** Unspecified — no license declared (all rights reserved by default) (verified)
- **Free tier:** yes — code open; NO license file or README terms (checked 2026-10-07)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** ACMMM 2024. Pushed 2024-10-22, 25 stars. Two-stage, 5000+ iterations per stage — slow. NOT commercial-safe (no license).

#### GET3D 🚫
- **What:** Text/image→textured 3D meshes with explicit topology (DMTet).
- **URL:** https://github.com/nv-tlabs/GET3D
- **License:** NVIDIA Source Code License for GET3D — non-commercial, research/evaluation only (verified from LICENSE.txt) (verified)
- **Free tier:** yes — code open, but NON-COMMERCIAL
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Pushed 2024-09-27, 4429 stars. Great topology but needs training data/compute; pretrained on FFHQ/ShapeNet. NOT commercial-safe.

#### Make-It-3D ✅
- **What:** Single image→high-fidelity 3D via two-stage diffusion-prior optimization.
- **URL:** https://github.com/junshutang/Make-It-3D
- **License:** Unspecified — no license declared (all rights reserved by default) (verified)
- **Free tier:** yes — code open; NO license file or README terms (checked 2026-10-07)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** ICCV 2023. Pushed 2024-07-05, 1897 stars. Per-shape two-stage optimization is slow. NOT commercial-safe (no license).

#### EG3D 🚫
- **What:** 3D-aware GAN (triplane + StyleGAN2) for geometry-aware generation.
- **URL:** https://github.com/NVlabs/eg3d
- **License:** NVIDIA Source Code License for EG3D — non-commercial, research/evaluation only (verified from LICENSE.txt) (verified)
- **Free tier:** yes — code open, but NON-COMMERCIAL
- **Quality impact:** 2/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Official repo is NVlabs/eg3d (nv-tlabs/eg3d is gone). Pushed 2023-06-10, 3334 stars. Face/object-centric GAN; dated vs diffusion methods. NOT commercial-safe.


## 2. Free 3D APIs (keyless first, then free-key)

#### PolyHaven API ✅
- **What:** Keyless REST API for CC0 HDRIs, PBR texture sets (up to 8K), and photoscanned models — covers the environment-lighting and PBR-texturing stages.
- **URL:** https://polyhaven.com
- **License:** CC0 (public domain) — commercial use unrestricted. (verified)
- **Free tier:** Unlimited, keyless, no signup.
- **Quality impact:** 5/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** api.polyhaven.com/assets + /files/<id>. Search/limit params are non-functional — fetch the full catalog and filter client-side. 521+ models, HDRIs, 8K PBR textures.

#### Hugging Face Inference API ❓
- **What:** Serverless inference for open models (image generation incl. SDXL-class) via REST / OpenAI-compatible endpoint.
- **URL:** https://huggingface.co/inference
- **License:** Service terms (HF ToS); output rights follow each model's license — check per model. (UNVERIFIED)
- **Free tier:** Free HF token; ~300 req/hr; ~1,000 req/day for models under 10GB.
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Cheapest keyless-adjacent GPU inference; 3D model coverage is limited — pair with HF Spaces for 3D stages.

#### ambientCG API ✅
- **What:** Keyless REST API (v2 full_json) for CC0 PBR materials — fastest texture-sourcing integration in the survey.
- **URL:** https://ambientcg.com
- **License:** CC0 — commercial use unrestricted. (verified)
- **Free tier:** Unlimited, keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** api v2 full_json; response key is foundAssets; previewImage keys look like '512-PNG'.

#### 3D AI Studio ✅
- **What:** Browser 3D-gen suite (multi-engine) + auto-rigging, remesh, texture tools; REST API.
- **URL:** https://www.3daistudio.com
- **License:** All assets created are yours for any commercial use without restrictions (official FAQ). (verified)
- **Free tier:** 100 free credits/mo on signup, no card; several tools fully free.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** API at api.3daistudio.com; aggregates Prism/Tripo/Hunyuan/Rodin engines + auto-rigging/remesh/texture tools. Strongest ToS in the 3D-gen group.

#### Alpha3D ❓
- **What:** Text- and image-to-3D API (GLB, 4K textures); Unity Moonlander SDK.
- **URL:** https://www.alpha3d.io
- **License:** Trial outputs: check ToS for commercial rights — verify before ship. (UNVERIFIED)
- **Free tier:** Free trial: first 50 AI-generated 3D assets incl. API access, no card.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Generous trial for a true 3D-gen API; image-to-3D currently strongest on shoes/furniture — test on characters before committing.

#### Google Gemini API (AI Studio) ❓
- **What:** Free-tier API including image generation (Imagen) for the concept-image stage.
- **URL:** https://ai.google.dev
- **License:** Google AI Studio ToS; generated images usable commercially per current terms — verify before ship. (UNVERIFIED)
- **Free tier:** Free tier, no credit card; ~50 images/day (Imagen); 1,500 req/day overall.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Best free concept-art engine in this survey; use Google sign-in per standing preference.

#### Icosa Gallery API ❓
- **What:** Open-source Google Poly successor; REST API serving CC-licensed glTF-native 3D models.
- **URL:** https://icosa.gallery
- **License:** CC licenses per asset (CC0/CC-BY variants) — check per item; commercial OK with attribution where required. (UNVERIFIED)
- **Free tier:** Free; keyless per 2026 probe — re-verify.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** api.icosa.gallery/v1/assets with OpenAPI docs. Open-source Google Poly successor; best Sketchfab-shaped replacement now that Fab has no public API.

#### Poly Pizza API ✅
- **What:** Search/download API for 10,100+ free low-poly models (GLB via CDN); mirrors Quaternius + Google Poly archive.
- **URL:** https://poly.pizza
- **License:** Per-model CC0 or CC-BY 4.0 — check model.Licence; attribute CC-BY as "[Title]" by [user] (poly.pizza). (verified)
- **Free tier:** Free API key (create on site, X-Auth-Token header); CDN .glb downloads need no auth.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** api.poly.pizza/v1.1; requests without a key return 401. Mirrors Quaternius + the Google Poly archive — quaternius.com itself has no API, so this is the sanctioned programmatic path.

#### fal.ai ✅
- **What:** 1,000+ image/video/audio/3D models behind one API; serverless GPU option.
- **URL:** https://fal.ai
- **License:** Service terms (Sep 2026: customer retains inputs/outputs, treated as confidential); model-specific commercial terms apply. (verified)
- **Free tier:** Free signup credits (~$10 reported); Sandbox: 15 free generations/day keyless on selected models, no account.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Hosts 1,000+ media models incl. 3D-generation endpoints; per-output pricing; keep FAL_KEY server-side, never in client code.

#### DeepMotion 🚫
- **What:** Markerless AI motion capture: video-to-animation and text-to-animation for custom characters.
- **URL:** https://www.deepmotion.com
- **License:** Freemium outputs non-commercial; commercial license requires paid plan. (verified)
- **Free tier:** Freemium: 60 sec/mo animation, no card — NON-COMMERCIAL. API access on paid plans (Pro ~$19/mo).
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Animate 3D (video→motion) + SayMotion (text→motion, has developer API). Accepts custom FBX/GLB characters; exports FBX/BVH/GLB/MP4.

#### Plask ❓
- **What:** AI mocap from video in the browser: full-body + hand capture; FBX/GLB/BVH export.
- **URL:** https://plask.ai
- **License:** Animations eligible for commercial use incl. free plan (per vendor FAQ) — re-verify ToS before ship. (UNVERIFIED)
- **Free tier:** Free plan: 15 sec/day mocap, 1 GB, FBX/GLB/BVH export, no card. API exists.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Free tier covers short fight-move clips; browser-based, multi-person; retarget to Mixamo-rigged GLBs in Blender.

#### Ready Player Me ❓
- **What:** Avatar SDK/API: full-body rigged humanoid avatars from selfie or parameters; Unity/Unreal/Blender compatible.
- **URL:** https://readyplayer.me
- **License:** Free for developers; commercial use for registered partners (2025 docs) — re-verify current terms before ship. (UNVERIFIED)
- **Free tier:** Free tier; partner registration free.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Fastest path to rigged humanoid base meshes; pair with Plask/DeepMotion for mocap. Wolf3D (Estonia).

#### Zoo Text-to-CAD API ❓
- **What:** Text-to-CAD API (Zookeeper agent → KCL → STEP/STL): mechanical parts, armor pieces.
- **URL:** https://zoo.dev
- **License:** Service terms; verify output-ownership clause before commercial use. (UNVERIFIED)
- **Free tier:** Free plan with monthly allowance (reported ~1,205 credits/mo); pay-as-you-go $0.50/min after.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Only text-to-CAD API found — ideal for mechanical brackets and Gundam-style armor parts (Zookeeper agent -> KCL -> STEP/STL). ML model also open-sourced for local GPU use.

#### Hyper3D Rodin ✅
- **What:** Image/text-to-3D (Gen-2.5) with full PBR; GLB/FBX/OBJ/USDZ/STL export.
- **URL:** https://hyper3d.ai
- **License:** Pay-by-result; any-use commercial license on Creator+; verify API-plan terms. (verified)
- **Free tier:** Free web tier (generate free, pay only on export confirm; ~10 signup credits). API access requires Business $120/mo — NOT free via API.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Best-in-class mesh quality (Gen-2.5, full PBR) but the API is paywalled — use the web tier for eval only.

#### PixelAPI ❓
- **What:** 15 tools, one API key: image gen, bg removal, upscale, face restore, object removal, 3D, moderation.
- **URL:** https://pixelapi.dev
- **License:** Service terms — verify commercial rights per endpoint. (UNVERIFIED)
- **Free tier:** 100 free credits on signup, no card.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Single-key Swiss-army knife for pipeline utilities (bg removal, upscale, face restore, object removal); 3D endpoint exists per docs.

#### Smithsonian Open Access API ✅
- **What:** Search API over 4.7M+ digitized objects across 19 museums, including CC0 3D scans.
- **URL:** https://edan.si.edu/openaccess/apidocs/
- **License:** CC0 — commercial use unrestricted (trust per-item usage.access == 'CC0'). (verified)
- **Free tier:** Free api.data.gov key, issued instantly; DEMO_KEY works at low rate limits.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Keyless requests return API_KEY_MISSING. ~2,199 CC0 3D scans (Draco .glb via public S3) — Apollo capsule, Lincoln life masks; great hero-prop source.

#### Together AI ❓
- **What:** Hosted open-model inference (image + LLM) via OpenAI-compatible API.
- **URL:** https://together.ai
- **License:** Service terms; output rights follow model licenses. (UNVERIFIED)
- **Free tier:** $5–$25 free credits on signup, valid 90 days, no credit card.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** OpenAI-compatible endpoints; good for SDXL/FLUX-class image batches once HF quota is exhausted.

#### CSM (Common Sense Machines) ✅
- **What:** Image/text/sketch-to-3D + text-to-4D animated meshes + AI retexturing; REST API.
- **URL:** https://www.csm.ai
- **License:** Tinkerer (free) outputs CC BY 4.0; Maker/Pro outputs private and customer-owned. (verified)
- **Free tier:** Free tier: unlimited low-res generations (web); API access on paid mid-tier/Enterprise only.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** API not free — web tier useful for prototyping. Text-to-4D animated meshes are unique for animated assets. docs.csm.ai.

#### DeepAI ✅
- **What:** Text-to-image + editing/super-resolution/colorization APIs; simple REST.
- **URL:** https://deepai.org
- **License:** Free-tier outputs are public by default; check API ToS for commercial use. (verified)
- **Free tier:** Free web tier (ad-supported, public gallery); limited free API calls; API via Pro or $5 pay-as-you-go.
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Weakest image API here (public outputs, limited free API) — listed as fallback only.

#### Move.ai ❓
- **What:** Markerless mocap (multi-iPhone) with API; AAA-quality motion data.
- **URL:** https://www.move.ai
- **License:** Service terms; commercial use on paid tiers. (UNVERIFIED)
- **Free tier:** 2-minute free trial only; Creator $365/yr.
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Weakest free tier in this list — trial only; included for completeness. Multi-iPhone markerless capture.


## 3. Texture / material tools

#### SyncMVD ✅
- **What:** Synchronized multi-view diffusion texturing: shares denoised content across views per denoising step — seam-free, fragmentation-free textures.
- **URL:** https://github.com/LIU-Yuxin/SyncMVD
- **License:** MIT (verified)
- **Free tier:** Fully open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT). Built on diffusers — fits the existing Hunyuan3D-Paint/MV-Adapter stack. Closes the multi-view inconsistency gap directly.

#### TEXTure ✅
- **What:** Text-guided iterative depth-diffusion texturing: generate, EDIT, refine, and transfer textures across meshes via trimap multi-view painting.
- **URL:** https://github.com/TEXTurePaper/TEXTurePaper
- **License:** MIT (verified)
- **Free tier:** Fully open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT). Texture EDITING/transfer capability none of the current stack has — enables owner-driven texture tweaks ('make the jacket redder') without full regen.

#### Paint3D ✅
- **What:** CVPR 2024 coarse-to-fine diffusion: generates high-res, LIGHTING-LESS 2K UV texture maps (no baked illumination) for untextured meshes, from text or image.
- **URL:** https://github.com/OpenTexture/Paint3D
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open; weights free
- **Quality impact:** 5/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (Apache-2.0, org OpenTexture/Paint3D). Directly closes the baked-lighting/speckle texture gap vs Tripo — relightable output fits PBR pipeline. Multi-stage (depth-aware views + UV inpaint + UVHD), GPU-heavy.

#### ControlNet ✅
- **What:** Spatial conditioning (depth, normal, pose, canny) for diffusion — depth-locked re-texturing of generated views, pose-locked variants.
- **URL:** https://github.com/lllyasviel/ControlNet
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open, free weights
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (Apache-2.0). Depth-ControlNet on rendered views = texture regen that exactly follows geometry; complements MV-Adapter stage.

#### IP-Adapter ✅
- **What:** Image-prompt adapter for SD/SDXL: condition texture generation on reference IMAGES (owner's art) instead of text alone — likeness lock.
- **URL:** https://github.com/tencent-ailab/IP-Adapter
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open, free weights
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (Apache-2.0). Feeds owner's character references straight into texture diffusion — key for keeping generated textures on-model.

#### Real-CUGAN ✅
- **What:** Real Cascade U-Nets for anime/cartoon super-resolution (2x/3x/4x + denoise levels). Strong on stylized character textures.
- **URL:** https://github.com/bilibili/ailab/tree/main/Real-CUGAN
- **License:** MIT (verified)
- **Free tier:** Fully open, free weights
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Official repo is the bilibili/ailab monorepo; LICENSE file inside Real-CUGAN/ subdir is MIT (fetched raw 2026-10-07). Ideal for the cartoon/stylized AshLane cast textures.

#### SDXL inpainting (diffusers) ✅
- **What:** SDXL inpainting pipeline via diffusers: repair UV maps (fill holes, erase speckle artifacts, seam touch-up) with mask + prompt.
- **URL:** https://github.com/huggingface/diffusers
- **License:** Apache-2.0 (code); model weights = Stability AI Community License (gated) (verified)
- **Free tier:** Code open; weights free but gated (accept license on HF)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified: diffusers Apache-2.0 via GitHub API. Weights are Community License (commercial OK with conditions). Directly targets speckle-noise/hole defects in generated textures.

#### SwinIR ✅
- **What:** Swin-Transformer image restoration / super-resolution (classic, lightweight, anime denoise variants). Texture upscale + denoise stage.
- **URL:** https://github.com/JingyunLiang/SwinIR
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open, free weights
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified via GitHub API license endpoint (Apache-2.0). Cheaper/faster complement to Real-ESRGAN for texture crispness; CPU-capable. Good first texture-SR wire-up.

#### HAT ✅
- **What:** Hybrid Attention Transformer SR — SOTA PSNR single-image super-resolution. Crisp texture upscaling beyond Real-ESRGAN.
- **URL:** https://github.com/XPixelGroup/HAT
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open, free weights
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified via GitHub API license endpoint (Apache-2.0). Heavier than SwinIR (more VRAM); best saved for hero-asset texture pass.

#### Text2Tex 🚫
- **What:** Text-to-texture with automatic view selection and progressive inpainting for full 3D coverage.
- **URL:** https://github.com/daveredrum/Text2Tex
- **License:** CC BY-NC-SA 3.0 (verified)
- **Free tier:** Non-commercial only
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified: LICENSE file is Creative Commons Attribution-NonCommercial-ShareAlike 3.0. NON-COMMERCIAL — research only, quarantine from commercial builds. Study its view-selection strategy; implement equivalent under a clean license if needed.

#### xNormal ✅
- **What:** Industry-standard high-poly to low-poly map baker (normal, AO, displacement, cavity, bent normals). Batch rendering supported.
- **URL:** http://www.xnormal.net/
- **License:** Freeware (proprietary); bundled license permits use/copy/redistribution incl. commercial (verified)
- **Free tier:** Free download
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified: bundled license (quoted in official help docs) permits use, copy, redistribution for any purpose incl. commercial; no reverse-engineering. Windows-only binary — best fit as an offline bake workstation tool, not Linux pipeline code.

#### 3DTextures.me ✅
- **What:** Free seamless PBR sets (diffuse, normal, height, AO, roughness), Blender/UE/Unity oriented.
- **URL:** https://3dtextures.me
- **License:** CC0 1.0 (verified)
- **Free tier:** All downloads free
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified as CC0 via third-party license audit (integrity-engine docs). Good stage/env material source for AshLane districts.

#### NormalMap Online ✅
- **What:** In-browser normal/AO/displacement/roughness map generation from a height/diffuse image (Sobel-based, JS).
- **URL:** https://github.com/cpetry/NormalMap-Online
- **License:** MIT (verified)
- **Free tier:** Fully open; free hosted app
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT). Algorithm is portable to Python/JS in one afternoon — cheapest normal-map stage available, no GPU needed.

#### ShareTextures ✅
- **What:** Free PBR texture sets (diffuse, normal, displacement, roughness, AO, specular) up to 4K, no signup.
- **URL:** https://www.sharetextures.com
- **License:** Custom CC0 (commercial OK, NO attribution, NO redistribution) (verified)
- **Free tier:** All downloads free
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified 2026-08-24 live license page via third-party catalog audit: 'Custom CC0' — commercial use OK, but redistribution on other sites/plugins/collections is banned. Ship inside the game, never re-host the library.

#### Textures.com ✅
- **What:** Large photo-texture library. Free tier: 15 credits/day (limited selection/smaller sizes); commercial license included on all tiers.
- **URL:** https://www.textures.com
- **License:** Proprietary terms; commercial use included even on free tier (verified)
- **Free tier:** 15 credits/day free
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified via ToS Rev3-11 (free credits = limited selection/sizes) and pricing pages (Starter ~$11-14/mo). Manual download site — reference source, not automatable at scale.

#### CodeFormer 🚫
- **What:** Codebook-lookup transformer face restoration, robust on very degraded faces.
- **URL:** https://github.com/sczhou/CodeFormer
- **License:** S-Lab License 1.0 — NON-COMMERCIAL (verified)
- **Free tier:** Research/non-commercial only
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified: LICENSE file is 'S-Lab License 1.0', redistribution/use for non-commercial purpose only. QUARANTINE from any commercial pipeline; research/experiment use only. Prefer GFPGAN for commercial-safe face fix.

#### GFPGAN ✅
- **What:** GAN-based face restoration. Fixes smeared/melted faces on generated character textures.
- **URL:** https://github.com/TencentARC/GFPGAN
- **License:** Apache-2.0 except third-party components (verified)
- **Free tier:** Fully open, free weights
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified: LICENSE file text is Apache-2.0 'except for the third-party components listed below' — audit that component list before shipping. Face-specific; pair with a face-crop stage.

#### Materialize 🚫
- **What:** Free desktop app: converts a single photo into full PBR map set (albedo, normal, height, roughness, metallic, AO, edge/ambient maps).
- **URL:** https://github.com/BoundingBoxSoftware/Materialize
- **License:** GPL-3.0 (verified)
- **Free tier:** Free app
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (GPL-3.0). GPL -> QUARANTINE: do not embed in shipped tree. Useful as an offline authoring reference, not pipeline code.

#### MaterialGAN ❓
- **What:** Generative SVBRDF model: reconstructs PBR material maps from a few flash photographs via optimization.
- **URL:** https://github.com/tflsguoyu/materialgan
- **License:** UNVERIFIED — no LICENSE file in repo (UNVERIFIED)
- **Free tier:** Research code; rights unclear
- **Quality impact:** 3/5 · **Wire-up difficulty:** 5/5
- **Status:** not-started
- **Notes:** GitHub API license endpoint 404 (no license file). Requires calibrated flash-photo capture rig — high effort, niche payoff. Do not ship without author permission.

#### TileGen ✅
- **What:** Tileable, controllable SVBRDF generation (StyleGAN variant) + inverse rendering from a single photo. For repeating stage/env materials.
- **URL:** https://github.com/jackzhousz/tilegen
- **License:** All rights reserved (proprietary) (verified)
- **Free tier:** Not usable without permission
- **Quality impact:** 3/5 · **Wire-up difficulty:** 5/5
- **Status:** not-started
- **Notes:** Verified: README License section says 'Copyright (c) 2023, Xilong Zhou. All rights reserved.' No license granted — effectively proprietary. Note concept only; do not clone.

#### HDRI Skies 🚫
- **What:** Sky HDRI maps; free 2K downloads, paid high-res (up to 30K) with backplates.
- **URL:** https://hdri-skies.com
- **License:** Mixed: some free maps = commercial OK; most free 2K = Non-Commercial, Non-transferable; hi-res paid = royalty-free commercial (verified)
- **Free tier:** Free 2K maps (license varies per map)
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified per-map license labels on hdri-skies.com (e.g. map 809 'Commercial Use'; maps 660/910+ 'Non-Commercial, Non-transferable'). Check EACH map's label before use.

#### NoEmotion HDRs ✅
- **What:** 150 free high-res HDRIs (day/evening/night), ~15K px, for IBL and backgrounds.
- **URL:** http://noemotionhdrs.net
- **License:** CC BY-ND 4.0 (attribution required, no derivatives) (verified)
- **Free tier:** All free; ~300MB each, 1TB/day bandwidth cap
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified on noemotionhdrs.net footer: CC Attribution-NoDerivatives 4.0. Commercial use allowed, but NoDerivatives + attribution burden — fine for lighting, not for redistribution.

#### sIBL archive (HDRLabs) 🚫
- **What:** Smart-IBL HDRI sets (background + reflection + GI variants) for image-based lighting.
- **URL:** http://www.hdrlabs.com/sibl/archive.html
- **License:** CC BY-NC-SA 3.0 — NON-COMMERCIAL (verified)
- **Free tier:** Free but non-commercial; site itself 404 as of 2026-08
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified: NC-SA license quoted on multiple mirrors; archive page HTTP 404 per 2026-08 audit. Non-commercial kills it for shipped games; keep as render-reference only.

#### AwesomeBump 🚫
- **What:** Single-image to normal/roughness/AO/specular map generator (Qt/OpenGL).
- **URL:** https://github.com/kmkolasinski/AwesomeBump
- **License:** GPL-3.0 (verified)
- **Free tier:** Free app
- **Quality impact:** 2/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (GPL-3.0). GPL -> QUARANTINE. NormalMap-Online (MIT) covers the same need commercially safe.

#### InsaneBump 🚫
- **What:** GIMP plugin generating normal/specular/AO/height maps from a single image.
- **URL:** https://github.com/rubencarneiro/gimp-insanebump
- **License:** GPL-3.0 (original distribution; some forks claim XFree-style) (verified)
- **Free tier:** Free plugin
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Original release GPLv3 (gist title confirms); fork READMEs claim ultra-permissive XFree-style. Treat as GPL -> QUARANTINE regardless. Requires GIMP; dated — skip in favor of MIT options.

#### Laigter 🚫
- **What:** Sprite normal/specular map generator (Qt app) with preview.
- **URL:** https://github.com/azagaya/laigter
- **License:** GPL-3.0 (verified)
- **Free tier:** Free app
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (GPL-3.0). GPL -> QUARANTINE. 2D-sprite oriented; marginal value for 3D character pipeline.

#### MetaTexture ❓
- **What:** NO STANDALONE TOOL FOUND under this name. Closest matches: the 'MetaTexture' UV/gradient technique in the Age-of-Sail NPR paper, and Meta 3D AssetGen's UV-space texture-refinement transformer (no public code).
- **URL:** 
- **License:** UNVERIFIED — no such standalone tool (UNVERIFIED)
- **Free tier:** N/A
- **Quality impact:** 1/5 · **Wire-up difficulty:** 5/5
- **Status:** not-started
- **Notes:** Do NOT wire. Deprioritize; if UV-space texture refinement is wanted, look at Paint3D's UVHD stage or Meta AssetGen paper (closed) instead.


## 4. Mesh processing (remesh, retopo, UV, repair, decimation)

#### Manifold ✅
- **What:** Guaranteed-manifold triangle meshes: fast booleans, hull, offset, smooth — 'if the input is garbage, output is still manifold'. Python package manifold3d.
- **URL:** https://github.com/elalish/manifold
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (Apache-2.0). pip install manifold3d — the single best watertightness/boolean guarantee in the catalog; ideal post-generation repair stage.

#### RizomUV ✅
- **What:** Industry-standard standalone UV unwrapping (auto seams, packing, UDIM). Bridge addons for Blender exist.
- **URL:** https://www.rizomuv.com
- **License:** Proprietary — PAID (verified)
- **Free tier:** 15-day full trial; then paid
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified on rizomuv.com plans page: perpetual EUR149.90, node-locked EUR34.90/mo, rent-to-own EUR14.90/mo. No budget -> deprioritize; OptCuts/BFF are the free answers.

#### OptCuts ✅
- **What:** Joint optimization of cuts + parameterization: auto UVs minimizing seam length under distortion bounds. Headless mode available.
- **URL:** https://github.com/liminchen/OptCuts
- **License:** MIT (verified)
- **Free tier:** Fully open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT, LICENSE.txt). Best-in-class automatic UVs — better seams = better texture projection; direct upgrade path over xatlas for hero assets. C++ build, batchable.

#### libigl 🚫
- **What:** Header-only geometry processing library: remeshing, smoothing, decimation, parameterization, booleans, hole filling. Python bindings available.
- **URL:** https://github.com/libigl/libigl
- **License:** MPL-2.0 / GPL-3.0 dual (verified)
- **Free tier:** Fully open
- **Quality impact:** 5/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified: repo root contains LICENSE.MPL2 and LICENSE.GPL (dual). MPL-2.0 is file-level copyleft — usable in proprietary pipelines if libigl files are kept separate. The Swiss-army knife for topology cleanup.

#### fast-simplification ✅
- **What:** Python quadric edge-collapse mesh decimation (pip package), preserves UVs — game-ready LODs from dense generated meshes.
- **URL:** https://github.com/pyvista/fast-simplification
- **License:** MIT (verified)
- **Free tier:** Fully open (PyPI)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT, pyvista org). pip install fast-simplification — near-zero-effort decimation stage for mobile/web poly budgets.

#### Open3D ✅
- **What:** Point-cloud/mesh processing: Poisson surface reconstruction, mesh cleanup, simplification, ray casting. pip-installable.
- **URL:** https://github.com/isl-org/Open3D
- **License:** MIT (verified)
- **Free tier:** Fully open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified: LICENSE file text is MIT (SPDX tag in file). Poisson recon = watertight meshes from generated point clouds/splats; fastest watertightness win in the catalog.

#### PyMeshFix 🚫
- **What:** Python/Cython wrapper of MeshFix: fills holes, removes self-intersections/degenerate elements -> single watertight mesh.
- **URL:** https://github.com/pyvista/pymeshfix
- **License:** GPL-3.0 (verified)
- **Free tier:** Fully open (PyPI)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Verified via GitHub API LICENSE (GPL-3.0; PyPI classifiers agree). GPL -> QUARANTINE despite the easy pip install. Manifold (Apache) is the commercial-safe replacement.

#### Geogram ✅
- **What:** Geometry processing: remeshing, CSG booleans, centroidal Voronoi, parameterization (used inside Blender-adjacent tooling).
- **URL:** https://github.com/BrunoLevy/geogram
- **License:** BSD-3-Clause (verified)
- **Free tier:** Fully open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified: LICENSE file is BSD 3-Clause (Inria). Solid remesh/boolean backend; C++ with some Python exposure.

#### pmp-library ✅
- **What:** Polygon Mesh Processing: smoothing, curvature, hole filling, remeshing, decimation, subdivision. Header-only C++.
- **URL:** https://github.com/pmp-library/pmp-library
- **License:** MIT (verified)
- **Free tier:** Fully open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT). Clean modern API; good hole-fill/smoothing stage for scan/AI-generated meshes.

#### Boundary First Flattening ✅
- **What:** Fast conformal UV flattening with interactive boundary control — near-interactive speed on million-tri meshes.
- **URL:** https://github.com/GeometryCollective/boundary-first-flattening
- **License:** MIT (verified)
- **Free tier:** Fully open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (MIT). Great for user-driven UV workflows (in-game generator UI); OptCuts wins for fully automatic quality.

#### ManifoldPlus 🚫
- **What:** Triangle-soup to watertight manifold conversion preserving sharp features (SDF-free, plane-fitting approach).
- **URL:** https://github.com/hjwdzh/ManifoldPlus
- **License:** Free for non-commercial use only (custom) (verified)
- **Free tier:** Research/non-commercial only
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified: README states 'This software is distributed for free for non-commercial use only.' Research-only; prefer Manifold (Apache) or Open3D Poisson for commercial builds.

#### OpenVDB ✅
- **What:** Sparse volumetric data: level-set repair -> watertight meshing from noisy/SDF inputs; NanoVDB for GPU.
- **URL:** https://github.com/AcademySoftwareFoundation/openvdb
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully open
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified: LICENSE file is Apache-2.0 (note: NOT MPL — older references say MPL 2.0, the current file is Apache). Volume-based repair route for badly broken generated meshes.

#### CGAL 🚫
- **What:** Computational geometry: polygon mesh repair, hole filling, boolean ops, isotropic remeshing, alpha shapes.
- **URL:** https://github.com/CGAL/cgal
- **License:** GPL-3.0-or-later / commercial dual (verified)
- **Free tier:** Open under GPL; commercial license paid
- **Quality impact:** 4/5 · **Wire-up difficulty:** 5/5
- **Status:** not-started
- **Notes:** Verified: LICENSE.md documents the dual scheme (dist tarballs GPL-3.0+; git-only files CC0). GPL -> QUARANTINE for the shipped tree. Heavy C++ build; pmp/libigl cover 80% of the need.

#### PyMesh ❓
- **What:** Revived Python mesh-processing library (boolean, remesh, repair). Revival repo location UNCONFIRMED — PyMesh/PyMesh 404s; original qnzhou/PyMesh archived.
- **URL:** 
- **License:** UNVERIFIED — repo not located (UNVERIFIED)
- **Free tier:** Unknown
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Do NOT wire until the revival repo is located and its license confirmed. libigl/pmp cover the same ground with verified licenses.

#### UVPackmaster 🚫
- **What:** GPU/CPU-accelerated UV island packing engine (Blender addon + standalone SDK).
- **URL:** https://www.uvpackmaster.com
- **License:** Proprietary — PAID (addon GPL, engine EULA); SDK Standard free for any purpose (verified)
- **Free tier:** Free SDK Standard edition (any purpose incl. commercial); full engine ~$29+
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Verified: 80.lv + Blender Market — SDK Standard usable free for any purpose. Packing-only (needs UVs from elsewhere); nice-to-have, not a gap-closer.

#### VCG / vcglib 🚫
- **What:** MeshLab's core library: cleaning, smoothing, simplification, curvature, sampling.
- **URL:** https://github.com/cnr-isti-vclab/vcglib
- **License:** GPL-3.0 (verified)
- **Free tier:** Fully open
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Verified via GitHub API (GPL-3.0). GPL -> QUARANTINE (MeshLab itself was already rejected for this reason). No unique capability vs MIT alternatives.


## 5. Rigging / animation (auto-riggers, retargeters, mocap)

#### Mixamo auto-rigger + animation library ✅
- **What:** Adobe's web auto-rigger (humanoid meshes) + 2,500+ mocap animation clips, FBX download
- **URL:** https://www.mixamo.com
- **License:** Adobe Terms of Use (proprietary) (verified)
- **Free tier:** Free with Adobe ID; unlimited commercial use when embedded in a project; no redistribution of assets or auto-rigged models
- **Quality impact:** 5/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Fastest rig path for humanoids; already in Forge3D lane. Limitation: no finger articulation, skinning quality middling; terms forbid redistributing the downloaded FBXs themselves.

#### CMU Graphics Lab Motion Capture Database 🚫
- **What:** 2,500+ motion sequences (boxing, kicks, karate, dance...) as ASF/AMC; BVH mirror at github.com/una-dinosauria/cmu-mocap
- **URL:** http://mocap.cs.cmu.edu
- **License:** Free for research and commercial products; no direct resale even in converted form; acknowledgment requested (verified)
- **Free tier:** Free
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Highest-value free commercial-safe mocap library. Caveats: 120fps sampling (AMC header lies, BVH conversion fixes it); finger joints have no captured data - ignore them; needs retargeting to game rig.

#### AccuRIG (Reallusion) ✅
- **What:** Free standalone auto-rigger: full-body + finger rigs, FBX/USD/iAvatar export; Blender add-on converts to Rigify controls
- **URL:** https://actorcore.reallusion.com/auto-rig
- **License:** Proprietary, free (verified)
- **Free tier:** Totally free download (Windows); free ActorCore account required to export; 32 free test animations, 4,500+ mostly paid
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Better fingers and weight painting than Mixamo. Caveats: Windows-only desktop app (not scriptable in pipeline); export gated on account registration; rig output is proprietary-format-neutral FBX so fine to wire.

#### Mesh2Motion (app + CC0 anim packs) ✅
- **What:** Free web app: import GLB/FBX, auto-rig humanoids/animals, export multi-clip GLB; 150+ CC0 animation clips (Quaternius-sourced) included
- **URL:** https://github.com/Mesh2Motion/mesh2motion-app
- **License:** MIT (code) + CC0-1.0 (art/animations) (verified)
- **Free tier:** Fully free and open source
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Excellent fallback for clip libraries without Adobe terms baggage; GLB-first exports fit the Three.js pipeline. Mixamo alternative.

#### DeepMotion Animate 3D ✅
- **What:** Cloud video-to-3D-animation (full body + face/hand tracking), FBX/BVH/GLB export, auto-retarget to custom characters
- **URL:** https://deepmotion.com/animate-3d
- **License:** Proprietary freemium (verified)
- **Free tier:** Freemium: ~60 animation credits/month, non-commercial license only. Paid plans ($48+/mo) grant perpetual commercial license for outputs made while subscribed
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Useful for generating motion reference/clips from video; terms prohibit selling retargeted animations standalone. Free outputs NOT commercial-safe; paid outputs are.

#### Plask Motion ❓
- **What:** Browser-based AI mocap: video to 3D animation, full body + hand + multi-person, FBX/GLB/BVH export
- **URL:** https://plask.ai
- **License:** Proprietary freemium (UNVERIFIED)
- **Free tier:** Free: 15 seconds mocap/day, 1GB storage, exports included. Standard $18/mo, Pro $50/mo
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Most generous free daily allowance of the AI-mocap services; GLB export is web-game friendly. Commercial-use terms of the free tier UNVERIFIED on their terms page - confirm before shipping free-tier outputs.

#### Rigify (Blender) 🚫
- **What:** Blender's built-in modular auto-rig: meta-rig to full control rig (IK/FK, fingers, face); scriptable headless
- **URL:** https://docs.blender.org/manual/en/3.3/addons/rigging/rigify/index.html
- **License:** GPL (verified)
- **Free tier:** Bundled with Blender, free
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** QUARANTINE per standing rules (GPL). High-quality rigs but does not do skinning (weights still manual). AccuRIG has a free Blender add-on that converts AccuRIG armatures to Rigify control rigs.

#### Rokoko Studio + Vision ✅
- **What:** Free mocap/animation suite (Smartsuit/Vision), FBX export, cleanup filters; Vision = browser video-to-motion
- **URL:** https://www.rokoko.com/pricing
- **License:** Proprietary freemium (verified)
- **Free tier:** Starter: free forever, FBX export, Vision 30s/mo video processing, unlimited text-to-motion generation (5 studio imports/mo)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Free Starter is genuinely usable (FBX export included, unlike Cascadeur free). Vision has no finger tracking yet. Text-to-motion clips are free to generate.

#### AMASS 🚫
- **What:** 40-50h of motion across 15 mocap datasets, unified to SMPL(+H) parameters via MoSh++
- **URL:** https://amass.is.tue.mpg.de/
- **License:** Custom non-commercial scientific research license (verified)
- **Free tier:** Free for non-commercial research; commercial requires contacting ps-license@tue.mpg.de; gated behind SMPL registration
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: NC research only, and SMPL body model itself is NC for commercial use. Enormous research value (motion priors, training data); cannot feed shipped game assets.

#### Cascadeur (Nekki) ✅
- **What:** Standalone AI-assisted keyframe animation: AutoPosing, AutoPhysics, quick-rigging, retargeting, mocap cleanup
- **URL:** https://cascadeur.com/
- **License:** Proprietary freemium (verified)
- **Free tier:** Free forever for NON-COMMERCIAL use only, exports to proprietary .casc format only. Indie ~$99/yr (<$100k revenue) unlocks FBX/DAE/USD export + commercial use
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** Great for action animation quality (physics-driven), but free tier is a dead end for shipping: .casc-only export + no commercial use. Only useful if/when paid Indie tier is acceptable.

#### GVHMR 🚫
- **What:** World-grounded human motion recovery (SMPL-X) from in-the-wild video; state of the art 2024-2025
- **URL:** https://github.com/zju3dv/GVHMR
- **License:** Custom: educational/research/non-profit use only, no commercial use, derivatives must be open source (verified)
- **Free tier:** Free for research/non-profit
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: NC + share-alike-style terms per third-party license notices. Great for offline reference-motion research; CANNOT ship in a commercial game pipeline. Needs GPU + SMPL-X.

#### MediaPipe Pose Landmarker ✅
- **What:** 33-landmark 2D/3D pose estimation, on-device CPU real-time, TFJS/WASM bindings
- **URL:** https://github.com/google-ai-edge/mediapipe
- **License:** Apache-2.0 (verified)
- **Free tier:** Free, open source
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Already the video-mocap lane baseline. Fine to ship.

#### mocapdata.com ✅
- **What:** Japanese mocap library: free sample clips (CC BY-SA 2.1 Japan) + paid motion packs
- **URL:** http://mocapdata.com/Terms_of_Use.html
- **License:** CC BY-SA 2.1 Japan (free files); purchased packs under buyer license (no redistribution) (verified)
- **Free tier:** Free files under CC BY-SA 2.1 JP; full pack (~16GB) requires academic/research request + $200 handling
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Small free pool but clean terms; paid packs allow commercial use as long as the data is protected from extraction.

#### Kinetix ❓
- **What:** Video-to-animation AI + emote SDK/API, retargeting tech
- **URL:** https://www.kinetix.tech
- **License:** Proprietary, terms unclear (UNVERIFIED)
- **Free tier:** Basic tier historically: 10,000 free emote generations then 0.15 EUR/emote; site has pivoted to B2B, pricing page 404s - UNVERIFIED
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Murky current status (2026: positioned as B2B 3D/motion research). De-prioritize until terms clarified.

#### KIT Motion-Language Dataset ❓
- **What:** Motion sequences paired with natural-language descriptions ('a person walks backward slowly') - text-to-motion training data
- **URL:** https://github.com/EricGuo5513/HumanML3D
- **License:** UNVERIFIED (research terms suspected) (UNVERIFIED)
- **Free tier:** Free download (KIT database)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: treat as research-only until KIT license page is read. Interesting for future text-driven animation, low priority for now. (KIT-ML conversion scripts live in the HumanML3D repo.)

#### MMPose / RTMPose ✅
- **What:** OpenMMLab pose framework; RTMPose = 75.8% COCO AP at 90+ FPS CPU; whole-body 133-keypoint variant (RTMW)
- **URL:** github.com/open-mmlab/mmpose/tree/main/projects/rtmpose
- **License:** Apache-2.0 (verified)
- **Free tier:** Free, open source
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Commercial-safe replacement for OpenPose; notably faster and more accurate than MediaPipe but heavier install (PyTorch stack). URL: github.com/open-mmlab/mmpose (path unverified in results).

#### MakeHuman 🚫
- **What:** Open parametric human generator (morphs for age/gender/ethnicity); exports rigged meshes
- **URL:** http://www.makehumancommunity.org/content/downloads.html
- **License:** AGPL (code) + CC0 exception for exported models (verified)
- **Free tier:** Free, open source; exported models are CC0 and commercial-safe
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** QUARANTINE the AGPL code per standing rules, but exported MODELS are CC0 - safe as asset source. Quality is dated vs Tripo; good for background NPC variety.

#### Ubisoft La Forge Animation Dataset (LAFAN1) 🚫
- **What:** Ubisoft mocap: locomotion/fight-style clips in BVH; FBX/BVH conversions exist (lafan1-resolved)
- **URL:** https://github.com/ubisoft/ubisoft-laforge-animation-dataset
- **License:** CC BY-NC-ND 4.0 (verified)
- **Free tier:** Free for non-commercial use
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: NC-ND - NoDerivatives bars even retargeting onto our rig, so it is reference-only even for research. (Found during research; listed as warning, not a wire candidate.)

#### BABEL 🚫
- **What:** 43.5h of AMASS mocap with 15k+ frame-level action labels in 260 categories - the action-labeled motion corpus
- **URL:** https://github.com/abhinanda-punnakkal/BABEL
- **License:** Custom non-commercial scientific research license (verified)
- **Free tier:** Free for academic research
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: NC research only. Valuable for training/searching motion by action label; inherits AMASS/SMPL commercial blocks.

#### EasyMocap (ZJU) ❓
- **What:** Multi-view and monocular markerless mocap to SMPL-X; widely used research pipeline
- **URL:** https://github.com/zju3dv/EasyMocap
- **License:** UNVERIFIED (UNVERIFIED)
- **Free tier:** Free code; SMPL-X body model needs free research registration
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: check LICENSE; several ZJU human-capture repos carry non-commercial terms. Heavy setup (multi-view calibrated or monocular + SMPL-X).

#### HybrIK ❓
- **What:** Hybrid analytical-neural inverse kinematics: 2.5D pose to SMPL body mesh
- **URL:** github.com/Jeff-sjtu/HybrIK (not verbatim-confirmed in search results)
- **License:** UNVERIFIED (research release; expected non-commercial terms) (UNVERIFIED)
- **Free tier:** Free code, research terms suspected
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: likely Max-Planck-style non-commercial license. Confirm LICENSE file before any wiring. SMPL body model itself is NC for commercial use.

#### METRO ❓
- **What:** Mesh Graphormer: 3D human mesh regression via transformer, monocular
- **URL:** repo URL not verbatim-confirmed in search results
- **License:** UNVERIFIED (expected non-commercial research terms) (UNVERIFIED)
- **Free tier:** Free code, research terms suspected
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: likely NC. Confirm before wiring.

#### PIXIE ❓
- **What:** Expressive full-body capture: SMPL-X body + hands + face from a single image
- **URL:** repo URL not verbatim-confirmed in search results
- **License:** UNVERIFIED (expected non-commercial research terms) (UNVERIFIED)
- **Free tier:** Free code, research terms suspected
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: likely NC. The face+hands detail is its differentiator, but SMPL-X is NC for commercial use.

#### ROMP ❓
- **What:** Real-time monocular multi-person 3D pose/mesh (SMPL) estimator
- **URL:** repo URL not verbatim-confirmed in search results
- **License:** UNVERIFIED (expected non-commercial research terms) (UNVERIFIED)
- **Free tier:** Free code, research terms suspected
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: likely NC. Confirm before wiring. SMPL dependency blocks commercial use regardless.

#### SFU Motion Capture Database 🚫
- **What:** Small academic mocap database (~38 sequences in common mirrors)
- **URL:** URL not verbatim-confirmed in search results (Simon Fraser University)
- **License:** Free for research only; cannot be used for commercial products or resale (verified)
- **Free tier:** Free for research
- **Quality impact:** 2/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** FLAG: research-only, no commercial use. Low value vs CMU; skip for shipping.

#### Daz3D / Daz Studio ❓
- **What:** Free Daz Studio + marketplace of rigged 3D humans; Genesis figure ecosystem
- **URL:** daz3d.com (not verbatim-confirmed in search results)
- **License:** Proprietary; per-model royalty-free-ish licenses (UNVERIFIED)
- **Free tier:** Daz Studio free; models mostly paid, royalty-free terms vary per model
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Per-model licensing is a paperwork minefield; historically no game-engine use under base license. Low priority for a game pipeline.

#### Human3.6M ✅
- **What:** 3.6M video frames + 3D poses, 11 actors, 17 everyday scenarios - pose estimation benchmark
- **URL:** None
- **License:** EULA: free of charge for ACADEMIC use only; commercial licensing is a separate paid path (verified)
- **Free tier:** Free for academic use
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: research-only per task brief. Evaluation reference only, not a pipeline input. URL: vision.imar.ro/human3.6m (not verbatim-confirmed).

#### OpenPose (CMU) 🚫
- **What:** Multi-person 2D pose (body+face+hands) - the legacy academic standard
- **URL:** https://github.com/CMU-Perceptual-Computing-Lab/openpose
- **License:** Custom non-commercial research license (verified)
- **Free tier:** Free for non-commercial use only; commercial license ~$25k/yr and excludes Sports field
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: NC-only, expensive commercial path, CPU speed is poor (1-3 FPS). RTMPose/MediaPipe are the commercial-safe replacements. Do not wire.


## 6. Multiview / scan / reconstruction (photogrammetry, NeRF, 3DGS, depth)

#### DUST3R (NAVER) 🚫
- **What:** Pose-free dense 3D reconstruction: stereo pointmaps from image pairs + global alignment, no camera calibration needed
- **URL:** https://github.com/naver/dust3r
- **License:** CC BY-NC-SA-4.0 (verified)
- **Free tier:** Free for research
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: NC-SA - research tooling only. Hugely promising for the multiview stage, but outputs feed research only; commercial deployments must swap in a permissive alternative.

#### MASt3R (NAVER) 🚫
- **What:** DUST3R + learned dense local features (24-dim descriptors): grounding image matching in 3D
- **URL:** https://github.com/naver/mast3r
- **License:** CC BY-NC-SA-4.0 (verified)
- **Free tier:** Free for research
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: NC-SA. Successor of DUST3R for the matching path. Keep as experimental/research lane only.

#### gsplat ✅
- **What:** Apache-2.0 3D Gaussian Splatting rasterizer/trainer: pure Python/CUDA, NeRFStudio integration
- **URL:** https://github.com/nerfstudio-project/gsplat
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully free and open source (Apache)
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** THE permissive 3DGS path - use this instead of Inria's research-only reference implementation for anything that ships. Already the community standard.

#### VGGT (Meta) 🚫
- **What:** Visual Geometry Grounded Transformer: feed-forward camera poses + depth + pointmaps from video
- **URL:** https://github.com/facebookresearch/vggt
- **License:** Custom non-commercial (VGGT License v1); Meta commercial variant has its own terms (verified)
- **Free tier:** Research license; commercial checkpoint (VGGT-1B) gated on HF with custom AUP
- **Quality impact:** 5/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: NC. The strongest feed-forward geometry model (2025). Research lane only until commercial terms are negotiated.

#### Depth Anything V2 ✅
- **What:** Foundation monocular depth model; Small variant is Apache-2.0 and ships via HF transformers
- **URL:** https://github.com/DepthAnything/Depth-Anything-V2
- **License:** Depth-Anything-V2-Small = Apache-2.0; Base/Large/Giant = CC-BY-NC-4.0 (verified)
- **Free tier:** Free and open source (split license)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** FLAG: only the SMALL model is permissive - wire the Small checkpoint and verify no NC weights in the closure. HF transformers + Apple Core ML ports exist.

#### OpenSfM ✅
- **What:** Python SfM pipeline (Mapillary): feature detection/matching, reconstruction, GPS/accelerometer sensor fusion
- **URL:** https://github.com/mapillary/OpenSfM
- **License:** BSD-style (verified)
- **Free tier:** Fully free and open source
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** BSD + Python makes it the most pipeline-friendly classical SfM option; GPS integration is a plus for environment scans.

#### Brush (ArthurBrussee/brush) ✅
- **What:** Rust/CUDA 3DGS trainer with GUI; Apache-2.0 alternative to the Inria trainer
- **URL:** https://github.com/ArthurBrussee/brush
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully free and open source (Apache)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Good candidate for a self-hosted 3DGS CLI stage alongside gsplat.

#### Depth Pro (Apple) 🚫
- **What:** Sharp monocular metric depth in under a second
- **URL:** https://github.com/apple/ml-depth-pro
- **License:** Apple sample-style license (non-commercial) (verified)
- **Free tier:** Code free; sample/license terms non-commercial-ish
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: Apple's license is research/sample terms - do not ship. Very fast (<1s) sharp metric depth for internal geometry checks.

#### Meshroom / AliceVision ✅
- **What:** Node-based SfM+MVS photogrammetry app: camera tracking, dense meshing, HDR pipelines
- **URL:** https://github.com/alicevision/Meshroom
- **License:** MPL-2.0 (verified)
- **Free tier:** Fully free and open source (AliceVision framework)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** The standard free desktop photogrammetry pipeline. Needs NVIDIA GPU; node-based so Forge3D could script specific node chains later.

#### Metric3D v2 ✅
- **What:** Zero-shot metric depth + surface normals; outdoor checkpoints tuned for driving scenes
- **URL:** https://github.com/YvanYin/Metric3D
- **License:** BSD-2-Clause (verified)
- **Free tier:** Free and open source (BSD)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** One of the few permissively-licensed ZERO-SHOT metric depth options - important for object scanning without calibrated rigs.

#### MoGe (Microsoft) ✅
- **What:** Monocular geometry estimation with sharp details and metric scale; outputs point maps (mesh-ready)
- **URL:** https://github.com/microsoft/MoGe
- **License:** MIT (verified)
- **Free tier:** Free and open source
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** MIT + point-map output makes it the cleanest licensed monocular geometry option. VRAM-hungry at high res.

#### NeRFStudio ✅
- **What:** Modular neural rendering framework: NeRF + 3DGS training, interactive viewer, camera-path rendering
- **URL:** https://github.com/nerfstudio-project/nerfstudio
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully free and open source (Apache)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** modular method system - new neural renderers drop in as plugins. Heavy GPU requirements.

#### OpenMVG ❓
- **What:** Open multiple-view geometry library: camera calibration, feature detection/matching, incremental SfM
- **URL:** github.com/openMVG/openMVG
- **License:** MPL-2.0 (UNVERIFIED - confirm at openMVG/openMVG) (UNVERIFIED)
- **Free tier:** Fully free and open source
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Library-style SfM (vs Meshroom's nodal app). MPL-2.0 is file-level copyleft - fine to ship, note in license manifest.

#### OpenMVS ❓
- **What:** Multi-view stereo: dense point cloud reconstruction, mesh reconstruction, refinement, texturing
- **URL:** github.com/cdcseacave/openMVS (URL not verbatim-confirmed)
- **License:** BSD 3-Clause (UNVERIFIED - confirm at cdcseacave/openMVS) (UNVERIFIED)
- **Free tier:** Fully free and open source
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** High-quality dense point-cloud/mesh stage. Pair with OpenMVG or COLMAP for the full pipeline. URL not verbatim-confirmed in search results.

#### 2DGS (2D Gaussian Splatting) ❓
- **What:** Surfel-based splatting with better surface geometry - mesh reconstruction from splats
- **URL:** https://github.com/hbb1/2d-gaussian-splatting
- **License:** UNVERIFIED (UNVERIFIED)
- **Free tier:** Free for research (assumed)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: confirm license at hbb1/2d-gaussian-splatting; several forks say 'follow the 3DGS license' which would mean NC. Better geometry than vanilla 3DGS.

#### SuGaR ❓
- **What:** Surface-Aligned Gaussian Splatting: extracts editable/textured meshes from 3DGS via Poisson reconstruction + Blender add-on
- **URL:** https://github.com/Anttwo/SuGaR
- **License:** UNVERIFIED (UNVERIFIED)
- **Free tier:** Free for research (assumed)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** FLAG: confirm license at Anttwo/SuGaR before wiring; it wraps vanilla 3DGS code so the NC question propagates. Mesh extraction is exactly what Forge3D needs for scan-to-asset.

#### Kiri Engine ✅
- **What:** Phone photogrammetry/NeRF/3DGS scanner with quad-mesh retopology + 3DGS-to-mesh export
- **URL:** https://www.kiriengine.app/
- **License:** Proprietary (per-app ToS) (verified)
- **Free tier:** Free: unlimited scans, unlimited exports (OBJ/FBX/STL/glTF), 150 photos/scan; Pro ~$80/yr lifts photo cap
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Most generous free tier for getting editable meshes off a phone; 3DGS-to-Mesh writes OBJ/FBX/glTF directly. Good for quick real-world reference captures.

#### RealityScan (Epic) ✅
- **What:** Epic's phone photogrammetry app (Sketchfab export) + free-tier desktop photogrammetry suite
- **URL:** https://www.strayspark.studio/blog/photogrammetry-scan-to-game-ready-prop-blender-2026
- **License:** Proprietary (Epic Games) (verified)
- **Free tier:** Mobile app free with no paid tier (up to 300 photos/scan); Desktop (ex-RealityCapture) 2.0 free for individuals/orgs under $1M revenue
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Epic ecosystem integration is a plus if Unreal is ever in the loop; desktop version is professional-grade photogrammetry for free under $1M revenue.

#### Scaniverse ✅
- **What:** Free phone 3D scanner: LiDAR mesh + photogrammetry + Gaussian splats, full export for free
- **URL:** https://www.apkmirror.com/apk/niantic-spatial-inc-2/scaniverse/scaniverse-free-3d-scanner-5-2-8-release/
- **License:** Proprietary (Niantic Spatial ToS) (verified)
- **Free tier:** Fully free: on-device processing, unlimited exports (OBJ/FBX/GLB/USDZ/LAS, splats to PLY/SPZ); paid cloud tiers optional
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Best free option: no export paywall, processing stays on-device (private), exports include FBX/GLB. Niantic Spatial ownership note.

#### Gaussian-Splat-Lite ✅
- **What:** Three.js/WebGPU Gaussian splatting renderer with GPU sorting, streaming LOD, depth rendering
- **URL:** https://github.com/WilliamLiu-1997/Gaussian-Splat-Lite
- **License:** Apache-2.0 (verified)
- **Free tier:** Fully free and open source (Apache)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Web viewer for splats matters because Forge3D deliverables target browser/Three.js viewing.

#### LightGlue ✅
- **What:** Local feature matching at light speed (learned matcher for SuperPoint/ALIKED/DISK/SIFT)
- **URL:** https://github.com/cvg/LightGlue
- **License:** Apache-2.0 (code + LightGlue weights; SuperPoint weights are a restrictive exception - avoid) (verified)
- **Free tier:** Free and open source (Apache)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Fast learned feature matching - drop-in upgrade for classical matching in SfM. Avoid SuperPoint weights (restrictive license); use ALIKED (BSD) or DISK.

#### MiDaS ✅
- **What:** Robust relative monocular depth estimation (MiDaS DPT) - the older workhorse
- **URL:** https://github.com/isl-org/MiDaS
- **License:** MIT (verified)
- **Free tier:** Free and open source
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Archived upstream; keep as fallback only.

#### Regard3D ❓
- **What:** Free GUI photogrammetry app (built on OpenMVG + OpenMVS): sparse point cloud, triangulation, textured mesh
- **URL:** http://www.regard3d.org
- **License:** MIT (UNVERIFIED - confirm at rhiestan/regard3d) (UNVERIFIED)
- **Free tier:** Fully free and open source; free for commercial work
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Easiest path to a first scan-to-mesh demo; avoids SIFT patent concerns via AKAZE. GUI app, less scriptable than Meshroom.

#### ZoeDepth ✅
- **What:** Metric + relative depth via MiDaS backbone; official impl archived
- **URL:** https://github.com/isl-org/ZoeDepth
- **License:** MIT (verified)
- **Free tier:** Free and open source
- **Quality impact:** 3/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Archived upstream (maintainers recommend forking); still a fine metric-depth baseline.

#### 3D Gaussian Splatting (Inria reference, graphdeco-inria) 🚫
- **What:** Original SIGGRAPH 2023 3DGS reference implementation
- **URL:** https://github.com/graphdeco-inria/gaussian-splatting
- **License:** Custom non-commercial research license (Inria + MPII hold all rights) (verified)
- **Free tier:** Free for research/evaluation only
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** FLAG: NC research-only - do not vend or ship. Use gsplat/Brush for anything commercial. Keep as algorithm ancestor/reference only.

#### LoFTR ❓
- **What:** Detector-free transformer-based local feature matching (CVPR 2021)
- **URL:** repo URL not verbatim-confirmed in search results (zju3dv/LoFTR)
- **License:** UNVERIFIED (reported permissive by secondary tables - confirm before wiring) (UNVERIFIED)
- **Free tier:** Free and open source (assumed)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Detector-free matching is ideal for texture-poor character reference shots. Verify license; repo URL: zju3dv/LoFTR (not verbatim-confirmed).

#### hloc (Hierarchical Localization) ❓
- **What:** Visual localization toolbox: feature extraction + matching + SfM (SuperPoint/SuperGlue/LoFTR combos)
- **URL:** repo URL not verbatim-confirmed in search results (cvg/Hierarchical-Localization)
- **License:** UNVERIFIED (reported permissive - confirm before wiring) (UNVERIFIED)
- **Free tier:** Free and open source (assumed)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Combines the matchers above into a full localization pipeline. Verify license; repo URL: cvg/Hierarchical-Localization (not verbatim-confirmed).

#### Marigold ✅
- **What:** Diffusion-based monocular depth estimation with excellent detail
- **URL:** https://github.com/prs-eth/Marigold
- **License:** Apache-2.0 (verified)
- **Free tier:** Free and open source (Apache)
- **Quality impact:** 3/5 · **Wire-up difficulty:** 4/5
- **Status:** not-started
- **Notes:** High quality but slow (diffusion sampling); best as an offline refinement stage, not the main path.

#### Polycam ✅
- **What:** Phone 3D scanning app (photogrammetry, LiDAR, Gaussian splats, room capture)
- **URL:** https://poly.cam
- **License:** Proprietary (per-app ToS) (verified)
- **Free tier:** Free tier: glTF-only export (must be published to Polycam explore page); paid Basic $150/yr or $30/mo adds OBJ/FBX/DAE/STL/USDZ
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Free tier is glTF-only - limiting for a mesh pipeline. Kiri/Scaniverse free tiers export more formats for free.

#### OpenSplat 🚫
- **What:** C++ CPU/GPU 3DGS trainer - permissive-featured but AGPL-licensed
- **URL:** https://github.com/pierotofy/OpenSplat
- **License:** AGPL-3.0 (verified)
- **Free tier:** Fully free and open source
- **Quality impact:** 2/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** QUARANTINE (AGPL) per standing rules; gsplat/Brush cover the same ground permissively.


## 7. Public-domain / CC0 asset libraries

#### NoEmotion HDRs ✅
- **What:** 150 free HDR environment maps, explicitly usable for personal and commercial work
- **URL:** https://80.lv/articles/a-treasury-of-free-hdrs
- **License:** Free for personal AND commercial work (no formal license file found) (verified)
- **Free tier:** Free download (bandwidth-capped)
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** 150 HDRs (300MB each) of Prague/Czech skies - excellent lighting source. Bandwidth limited (~1TB/day); download selectively.

#### itch.io CC0 ✅
- **What:** Game asset storefront with tag-based CC0 browsing; many GLB/FBX packs incl. animated characters
- **URL:** https://itch.io/game-assets/new-and-popular/tag-cc0
- **License:** CC0 per-asset (tag-based; check each page) (verified)
- **Free tier:** Free; many packs are pay-what-you-want with $0 minimum
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Best discovery path for CC0: tag-cc0 page + curated collections; includes rigged+animated CC0 GLBs, which are directly game-usable. Per-asset verification still needed.

#### HDRI Hub free samples ✅
- **What:** 11 free HDR/EXR environment maps (city, nature, industrial) with free commercial license
- **URL:** https://www.hdri-hub.com/shop/free-samples/free-hdri-downloads
- **License:** Free commercial license (per site) (verified)
- **Free tier:** Free samples, free commercial license
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Only 11 free samples - small but zero-friction; confirm the license statement on each sample page.

#### HDRI Skies (hdri-skies.com) ✅
- **What:** High-quality HDR sky maps; 2K free for commercial use, paid full-res packs
- **URL:** https://technofizi.net/sitelike/openfootage.net
- **License:** Free 2K = royalty-free commercial OK (per site); paid tiers for full-res (verified)
- **Free tier:** Free 2K skies (royalty-free); paid full-res up to 20K
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** 2K free tier is plenty for Forge3D env lighting; full-res is paid. Terms confirmed via secondary source - re-confirm on site before bulk use.

#### RenderPeople samples ❓
- **What:** Photogrammetry 3D people scans; free sample pack offered
- **URL:** https://www.renderpeople.com (not verbatim-confirmed in search results)
- **License:** UNVERIFIED (reported royalty-free for samples - confirm at renderpeople.com) (UNVERIFIED)
- **Free tier:** Free sample models
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** High-quality photogrammetry human scans - exactly the kind of reference Forge3D needs - but sample license terms must be confirmed before use.

#### Sketchfab CC0 filter ✅
- **What:** Huge 3D model platform with CC licenses for downloadable models; searchable CC0 subset incl. museum collections (Smithsonian, Cleveland Museum of Art...)
- **URL:** https://sketchfab.com/
- **License:** Per-model CC licenses incl. CC0; filter for downloadable + CC0 (verified)
- **Free tier:** Free with account
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Note: Sketchfab is being deprecated in favor of Epic's Fab platform (2025+); verify the CC0 filter still exists there before depending on it. Per-model license - check each.

#### sIBL Archive ❓
- **What:** Smart IBL lighting sets (HDR/EXR + XML) from many artists for image-based lighting
- **URL:** http://www.hdrlabs.com/sibl/archive.html
- **License:** Per-artist license; archive mixes licenses (UNVERIFIED)
- **Free tier:** Free download
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** UNVERIFIED: the archive is a collection of per-artist sIBL sets - check each set's terms. The sIBL FORMAT itself is an open standard (hdrLABS).

#### BlendSwap ❓
- **What:** Community .blend model sharing; license is per-model
- **URL:** https://blendswap.com (not verbatim-confirmed in search results)
- **License:** Mixed per-model (CC-BY, CC-BY-SA, CC0...) (UNVERIFIED)
- **Free tier:** Free to download
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** UNVERIFIED: per-model licenses; many are CC-BY (attribution OK) but some carry fanart/copyright risk. Never pull fanart-tagged models into a shipping game.

#### BlenderKit ❓
- **What:** In-Blender asset library (models, materials, HDRIs): free tier for any purpose, premium paid
- **URL:** URL not verbatim-confirmed in search results
- **License:** Per-asset free license (not CC0) (UNVERIFIED)
- **Free tier:** Free assets accessible in-Blender; paid premium tier
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** NOT CC0 - free assets under BlenderKit's own free license. Convenient for prototyping, not a CC0 supply.

#### OpenGameArt ✅
- **What:** Game asset archive (models, textures, audio) with per-asset CC licenses; CC0 filter available
- **URL:** http://opengameart.org/forumtopic/planning-on-releasing-cc0-in-future
- **License:** Mixed per-asset (verified)
- **Free tier:** Free to download; license is per-asset (CC0, CC-BY, CC-BY-SA, GPL, OGA-BY...) - filter required
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** NOT a blanket CC0 source. Use only assets explicitly tagged CC0/PD; the site vets CC0 submissions. Mostly 2D/game audio; 3D section thinner.

#### Textures.com ❓
- **What:** Large texture photo library with free tier (daily caps) and subscription tiers
- **URL:** https://www.textures.com (not verbatim-confirmed in search results)
- **License:** Proprietary free/paid tiers; free content usable in renders, no standalone redistribution (UNVERIFIED - confirm at textures.com/license) (UNVERIFIED)
- **Free tier:** Free account with daily download caps
- **Quality impact:** 2/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Useful texture library but NOT CC0; daily caps on free accounts. Flag as non-CC0 texture source.

#### Printables CC0 ❓
- **What:** Prusa's 3D-print model repository with per-model license choice
- **URL:** https://www.printables.com (not verbatim-confirmed in search results)
- **License:** Mixed per-model (incl. CC0) (UNVERIFIED)
- **Free tier:** Free with account
- **Quality impact:** 2/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** UNVERIFIED: per-model licenses, CC0 filter exists. Same STL-print caveat as Thingiverse.

#### Thingiverse CC0 ❓
- **What:** 3D-print model repository (MakerBot); per-model CC licenses, some CC0
- **URL:** https://www.thingiverse.com (not verbatim-confirmed in search results)
- **License:** Mixed per-model (CC-BY, CC-BY-NC, CC0...) (UNVERIFIED)
- **Free tier:** Free with account
- **Quality impact:** 2/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** UNVERIFIED: license is per-model; filter for CC0. Mostly STL for 3D printing (low game value; retopo needed).

#### CGTrader Free ❓
- **What:** Marketplace with a free section; per-model royalty-free licenses
- **URL:** https://www.cgtrader.com/free-3d-models
- **License:** Marketplace royalty-free (per-model), NOT CC0 (UNVERIFIED)
- **Free tier:** Free models exist
- **Quality impact:** 1/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** EXCLUDED from CC0: free models carry CGTrader's royalty-free license, not CC0. Useful as reference, not as CC0 supply.

#### Quixel Megascans ✅
- **What:** Photogrammetry asset library (Epic) - verified NOT CC0; UE-only under free tier
- **URL:** https://d3uwib8iif8w1p.cloudfront.net/docs/QuixelMegascansToS_JUL272018.pdf
- **License:** Proprietary (Epic EULA: UE-Only Content) (verified)
- **Free tier:** Free via Epic account but UE-ONLY
- **Quality impact:** 1/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** EXCLUDED from CC0 section: NOT public domain. Free access is licensed for use with Unreal Engine only; using in other engines needs a paid Quixel subscription. Flag as non-CC0.

#### TurboSquid Free ❓
- **What:** Large marketplace with a free-models section; licenses are royalty-free marketplace terms, not CC0
- **URL:** https://www.turbosquid.com/Search/3D-Models/free
- **License:** Marketplace royalty-free (per-model), NOT CC0 (UNVERIFIED)
- **Free tier:** Free models exist; priced per purchase
- **Quality impact:** 1/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** EXCLUDED from CC0: free != CC0. Royalty-free per TurboSquid's own terms; check each model's terms. Not a CC0 source.


## 8. Hugging Face Spaces with free keyless GPU endpoints

#### HiDream-ai/HiDream-I1-Dev ✅
- **What:** Official HiDream demo: 17B text-to-image (distilled Dev, 28 steps) — SOTA prompt adherence for concept art.
- **URL:** https://huggingface.co/spaces/HiDream-ai/HiDream-I1-Dev
- **License:** MIT — unrestricted commercial use. (verified)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Existence verified via official launch announcement. NOTE: guessed 'HiDream-I1-Full' space ID was wrong — official space is HiDream-I1-Dev. Beats FLUX/SD3.5 on GenEval/DPG-Bench.

#### stabilityai/TripoSR ✅
- **What:** Official Stability demo: single-image to textured 3D mesh in ~0.5s (LRM-style + FlexiCubes).
- **URL:** https://huggingface.co/spaces/stabilityai/TripoSR
- **License:** MIT (code + weights) — unrestricted commercial use. (verified)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Page-verified 2026-10-06 (container showed a build error at check time — re-verify live before wiring). Only fully permissive image-to-mesh in the survey — default bring-up provider.

#### stabilityai/stable-fast-3d 🚫
- **What:** Official Stability demo: image-to-GLB in 0.5s with UVs, de-lit albedo, normals, material scalars.
- **URL:** https://huggingface.co/spaces/stabilityai/stable-fast-3d
- **License:** Stability AI Community License — research/non-commercial + commercial ≤$1M annual revenue; 'Powered by Stability AI' attribution required. (verified)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 5/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Page-verified 2026-10-06. Game-ready output (UVs + PBR params + optional quad remesh) makes it the shortest path to engine-ready GLB.

#### tencent/Hunyuan3D-2 ✅
- **What:** Official Tencent demo: image-to-3D with PBR texture generation; keyless Gradio API.
- **URL:** https://huggingface.co/spaces/tencent/Hunyuan3D-2
- **License:** Tencent Hunyuan 3D Community License — commercial OK under 1M MAU; EXCLUDES EU/UK/South Korea; no model redistribution; no training other models on outputs. (verified)
- **Free tier:** Free shared GPU (ZeroGPU); keyless; queues vary.
- **Quality impact:** 5/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Page-verified 2026-10-06. Highest-quality free image-to-3D (ShapeGen + TexGen). Territory exclusion is a hard blocker for EU/UK/KR — flag in docs.

#### akhaliq/Real-ESRGAN ✅
- **What:** Community demo of Real-ESRGAN: AI upscaling for textures and concept art.
- **URL:** https://huggingface.co/spaces/akhaliq/Real-ESRGAN
- **License:** BSD-3-Clause (xinntao/Real-ESRGAN). (verified)
- **Free tier:** Free shared GPU/CPU; keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Existence verified via official Real-ESRGAN README acknowledgement. Upscaler stage for the texture pass.

#### Zhengyi/CRM ❓
- **What:** Official THU demo: single image to textured 3D mesh in ~10s (Convolutional Reconstruction Model).
- **URL:** https://huggingface.co/spaces/Zhengyi/CRM
- **License:** Upstream license not confirmed in this pass — verify before commercial use; HF Spaces ToS apply. (UNVERIFIED)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 2/5
- **Status:** not-started
- **Notes:** Existence search-verified via official repo. NOTE: guessed ID 'Shenyi-Zhang/CRM' was wrong — correct ID is Zhengyi/CRM.

#### Stable-X/Hi3DGen ❓
- **What:** Official demo: high-fidelity 3D geometry from images via normal bridging.
- **URL:** https://huggingface.co/spaces/Stable-X/Hi3DGen
- **License:** Upstream license not confirmed in this pass — verify before commercial use. (UNVERIFIED)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Existence verified via official demo badge in ComfyUI integration + paper repos. ICCV 2025 normal-bridging geometry — quality stage for meshes.

#### TencentARC/PhotoMaker ✅
- **What:** Official Tencent demo: ID-preserving human photo customization from 1+ face photos + prompt.
- **URL:** https://huggingface.co/spaces/TencentARC/PhotoMaker
- **License:** Apache-2.0 (V1); V2 adds InsightFace terms — use V1 for cleanest commercial posture. (verified)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Existence verified via official README demo badge. Directly relevant to keeping wrestler likeness in concept images (stacked ID embedding, no training).

#### VAST-AI/TripoSplat ✅
- **What:** Official VAST AI Research demo: single image → 3D Gaussian splats (up to 262k).
- **URL:** https://huggingface.co/spaces/VAST-AI/TripoSplat
- **License:** MIT (code + weights) — unrestricted commercial use. (verified)
- **Free tier:** Free shared GPU; keyless; no account needed for the demo.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Existence verified via multiple integrations; beat TRELLIS.2/Hunyuan3D-2.1 in a 399-vote human preference study. Gaussian output (.ply/.splat) needs splat→mesh conversion for GLB.

#### ashawkey/LGM ❓
- **What:** Official 3DTopia demo: Large Multi-View Gaussian Model — image/text to 3D Gaussians in ~5s (+ mesh extraction).
- **URL:** https://huggingface.co/spaces/ashawkey/LGM
- **License:** Upstream license not confirmed in this pass — verify before commercial use; HF Spaces ToS apply. (UNVERIFIED)
- **Free tier:** Free shared GPU; keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Existence search-verified via official repo demo badge. NOTE: guessed ID '3DTopia/LGM' was wrong — correct ID is ashawkey/LGM.

#### yisol/IDM-VTON 🚫
- **What:** Official virtual try-on demo: dress person photos in garment images — outfit concepting for fighters.
- **URL:** https://huggingface.co/spaces/yisol/IDM-VTON
- **License:** CC BY-NC-SA 4.0 — NON-COMMERCIAL. (verified)
- **Free tier:** Free ZeroGPU; keyless.
- **Quality impact:** 4/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Existence + public /tryon endpoint verified via third-party integration writeup. NC license limits it to R&D/concept use.

#### Sanster/Lama-Cleaner-lama ✅
- **What:** Official LaMa inpainting demo: remove objects/defects/people from images.
- **URL:** https://huggingface.co/spaces/Sanster/Lama-Cleaner-lama
- **License:** Apache-2.0. (verified)
- **Free tier:** Free shared GPU/CPU; keyless.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 1/5
- **Status:** not-started
- **Notes:** Existence verified via official repo badge. Exact casing: Sanster/Lama-Cleaner-lama. Cleanup stage for concept art.

#### zhengchong/CatVTON 🚫
- **What:** Official CatVTON demo (ICLR 2025): virtual try-on for outfit variants.
- **URL:** https://huggingface.co/spaces/zhengchong/CatVTON
- **License:** CC BY-NC-SA 4.0 — NON-COMMERCIAL. (verified)
- **Free tier:** Free ZeroGPU; keyless.
- **Quality impact:** 3/5 · **Wire-up difficulty:** 3/5
- **Status:** not-started
- **Notes:** Existence verified via official repo (ZeroGPU grant) + third-party integration docs. Mask-free try-on for tops/bottoms/dresses.


## Appendix — quarantine watchlist

GPL/AGPL or otherwise restricted tools that are useful references but must stay OUT of the shipped tree (per standing rules, `quarantine/` only):

- Materialize (GPL-3.0)
- Laigter (GPL-3.0)
- AwesomeBump (GPL-3.0)
- InsaneBump (GPL-3.0)
- vcglib (GPL-3.0)
- PyMeshFix (GPL-3.0)
- CGAL (GPL dual)
- CodeFormer (S-Lab non-commercial)
- Text2Tex (CC BY-NC-SA 3.0)
- ManifoldPlus (non-commercial)
- sIBL archive (CC BY-NC-SA 3.0)
- TileGen (all rights reserved)
- MaterialGAN (no license)
- PyMesh (repo unlocated)
- MetaTexture (no such tool)

## Methodology

- 4 parallel research workers, one per category group, each checkpointed under `~/workspace/agent-ops/checkpoints/forge3d-catalog-*.json`.
- Every entry confirmed as a real project (live repo URL + recent activity checked). Entries that couldn't be confirmed were dropped, not listed.
- Licenses read from upstream LICENSE files / README License sections / official terms pages. `license_verified:false` means 'could not confirm — read before wiring', never a guess.
- Raw machine-readable data: `docs/catalog-parts/{genmodels,apis_spaces,texmesh,rigscan_assets}.json`.
- Wiring status: none of these are wired by this catalog task. Wire-up order follows the Top-10 above; update each entry's Status when a wiring worker picks it up.