# INVENTORY.md — Phase 0 audit (2026-10-06, verified live)

Full reports: `docs/research/image-to-3d-open-source-verification-2026-10-06.md`
and `docs/research/free-api-gpu-research.md`. His-repo audit pending (GitHub
audit agent still running — merged on landing).

## Open-source models — ranked for Forge3D (textured character mesh, limited HW)

| Rank | Model | License | Min VRAM | Verdict |
|---|---|---|---|---|
| #1 default | Stable Fast 3D (SF3D) | Stability AI Community (<$1M revenue — safe for us) | 7–9 GB | UV-unwrapped GLB, de-lit PBR; best quality-per-VRAM on free-tier GPUs |
| #2 shape fallback | TripoSG | MIT | 8–12 GB | watertight manifold geometry, MIT-clean; geometry-only (bake texture separately) |
| #3 CPU fallback | TripoSR | MIT | ~6 GB / CPU ~45s | runs on THIS VM; 2024-era quality, no UV unwrap |
| #4 hero (16GB) | Unique3D | MIT | 12–16 GB | best texture detail in permissive class |
| hero (real GPU) | TRELLIS.2 | MIT | 24 GB (16 fp16) | open SOTA, PBR to 4K — needs rented GPU |
| texture stage | Hunyuan3D-Paint | Tencent Community (EU/UK/SK excluded, 1M MAU cap) | 21 GB | bake PBR onto any mesh; licensed-tier, US-ok |

Hard no-gos: Zero123++ weights (CC-BY-NC), Hunyuan3D-2/2.1 weights (territory
exclusion + attribution + 1M MAU — NOT Apache-2.0), LGM/TripoSplat/GRM (splat
output, not meshes), Shap-E/Point-E (obsolete for characters).

## Free APIs — ranked

| Rank | API | Free quota | Commercial | Automatable |
|---|---|---|---|---|
| #1 | Pollinations 3D (trellis-2-low) | key free; $0.24/gen via earnable Quest Pollen | check terms | YES (REST) |
| #2 | Tripo3D API Platform | 300 cr/mo (~10 models), no card | NO (CC BY 4.0 non-commercial) | YES (REST) |
| #3 | Meshy free | 100 cr/mo (~3 models), no card | YES (CC BY 4.0 w/ attribution) | NO (web UI only; API is paid) |
| bonus volume | SupaVoxel | 3 models/day, no card | check terms | web |

Skip: Spline (no AI gen on free), fal.ai/Replicate/Stability (no real free 3D
tier), HF serverless (no 3D models deployed).

## Free GPU compute — ranked

1. **Kaggle** — 30 GPU-h/week, dual T4 16GB, no card (phone verify). Best free path for SF3D/TripoSG/Unique3D.
2. **Colab free** — T4, ~100 compute units/mo; dynamic availability.
3. **Lightning AI** — ~30 starter credits (~75 T4-h), real Linux dev box.
4. **HF ZeroGPU Spaces** — 5 GPU-min/day; agent-callable Gradio API.

## CPU-only VM reality (this box)
Genuinely usable today: TripoSR (~45s/mesh, MIT), rembg, trimesh repair/decimate,
GLB manipulation. So the **Forge3D v0 free pipeline runs end-to-end on this VM**:
`pollinations-image (keyless) → triposr (CPU) → trimesh cleanup → GLB`.

## Quality bottleneck vs Tripo (honest)
Topology (triangle soup vs clean mesh) → closed by cleanup + retarget tooling.
Textures (blurry backs) → Hunyuan3D-Paint stage / better provider.
Anatomy (hallucinated occlusions) → multi-view stage; owner's eyes-on loop is
the real training signal.
