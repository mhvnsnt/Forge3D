# INVENTORY.md — Phase 0 audit (2026-10-06, verified live)

Full reports: `docs/research/image-to-3d-open-source-verification-2026-10-06.md`
and `docs/research/free-api-gpu-research.md`. His-repo audit: read-only
`gh` API survey 2026-10-06 (54 repos found; no commits, no secrets touched).

## His repos (mhvnsnt) — generation-relevant

**AshLanev2 `tools/generative/`** (master docs: GENERATIVE_PIPELINE.md, LICENSE-MANIFEST.md)
- `3d/`: `triposr_generate.py` (image→GLB, mc_res 128–256, bg-removal) →
  ported into Forge3D as `forge3d/providers/triposr.py`;
  `trellis_generate.py`, `shap_e_generate.py` (wired, GPU-only);
  `postprocess.py` (decimate/weld/normals/center → game-ready GLB, CPU-runnable) →
  adapted into `forge3d/pipelines/postprocess.py`;
  `buffalo_bill.py` (reference→TripoSR/TRELLIS→postprocess orchestrator);
  `*_setup.sh` installers.
- `character/`: `auto-character.py` (keyless HF Spaces REST, WORKING per docs —
  proof-shap-e-wrestler.glb exists); `char-pipeline.py` (GENERATE→POSTPROCESS→
  RIG→VALIDATE→DEPLOY); `auto-rig.py` (capsule-distance skinning to 58-joint
  Mixamo skeleton, pure CPU); `char-procedural.py` (CPU proof path);
  Colab notebook + RunPod/Vast.ai deploy (~$0.34/hr RTX 3090); `server.py`
  (GPU-box HTTP server, NO AUTH — internal only).
- `motion/glb_anim.py` (GLB animation injection), `splat/`, `world/` (seeded
  city gen), `textures/` (+ Real-ESRGAN upscaler). No keys/secrets in generative code.

**Bannon `tools/generative/`** (most mature layer, CPU-proven 2026-10-06, proof/ artifacts)
- `mesh/mesh_doctor.py` (weld, degenerate removal, normal fix, HOLE FILL —
  81 holes on STICKUP proof); `mesh/lod_chain.py` (18k→9k→4.5k faces);
  `motion/procedural_moves.py` (34 wrestling moves baked as glTF anims);
  `retarget/mediapipe_to_glb.py` + `bvh_retarget.py`; `common/` (glb_anim, fk, quat);
  `world/` arena + crowd generators; `selftest.py` (one-command PASS/FAIL).
- `tools/gen/hf_pipeline.py`: free HF GPU-Spaces 3D (text→FLUX→Hunyuan3D-2/
  InstantMesh→GLB), `HF_TOKEN` env (owner authed 'Dmn52').
- `tools/forge/generate.py`: brief→TripoSR→UniRig auto-rig→QA pipeline;
  license table REJECTED Hunyuan3D-2/Stable Fast 3D (outdated — SF3D now
  commercial-OK <$1M; Hunyuan still gated).
- Free-API usage: `TRIPO_API_KEY` (PAID credits) in tools/tripo/*.mjs;
  `TRIPOSR_DIR`/`TRELLIS_DIR` path vars. ⚠️ Tripo3D FREE tier outputs are
  NON-commercial — only paid-credit outputs are money-safe.

**Other repos:** `texture-customizer` (GLB material-tweaking PWA, no AI);
`QuantumBlur` (quantum seeds/heightmaps only); `brutalfistgrokversionten`
(correct Bannon model SOURCE, not a generator); `ConcreteDragon`/`AshLane`/
`Brutal-Fist` (consumers, not generators).

**Name check:** `mhvnsnt/Forge3D` was free at creation and is THIS repo
(authorized build). ModelForge, DragonForge available as fallbacks (unused).

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

## REINFORCEMENT ROUND 1 (2026-10-06) — keyless HF Spaces GPU path

Owner directive: wire open-source across every stage until output matches/beats
Tripo3D. This box has NO GPU (nvidia-smi absent, torch CUDA false, 7GB RAM), so
the reinforcement leans on **keyless HuggingFace Spaces** (free GPU, Gradio
REST — proven pattern from AshLanev2 auto-character.py) plus the local CPU
fallback.

New providers wired (all keyless, verified reachable 2026-10-06):
| Provider | Backend | License | What it does |
|---|---|---|---|
| `trellis2-space` | microsoft/TRELLIS.2 Space | MIT (code+weights) | image→3D SOTA mesh + PBR texture → GLB. QUALITY ANCHOR. |
| `instantmesh-space` | TencentARC/InstantMesh Space | Apache-2.0 | fast image→3D (~10s GPU) via preprocess→multiview→make3d chain. Iteration speed. |

Shared client: `forge3d/providers/_vendor/hf_space.py` (urllib-based Gradio
REST: upload → call → SSE poll → download; avoids the httpx/no_proxy IPv6 bug).

`generate --provider auto` now runs a **fallback chain** (best quality first,
local CPU last): trellis2-space → instantmesh-space → pollinations-3d →
tripo-api → GPU-local providers → triposr. Any provider raising ProviderError
is skipped loudly; all-fail still produces NO fake output.

Cleanup stage reinforced: `pipelines/postprocess.py` now counts boundary loops
(holes) before/after and runs `trimesh.repair.fill_holes()` — stats written to
`<name>.cleanup.json` for the run manifest.

### Exact command for the owner's first job (image-to-3D)
```bash
cd ~/workspace/forge3d
python3 -m forge3d generate --image /path/to/echo.png --provider auto --out runs/echo1
# --provider trellis2-space   # force the quality anchor
# --provider instantmesh-space # force the fast path
# --provider triposr           # force local CPU fallback
```
Output: `runs/echo1/*.clean.glb` (postprocessed) + run manifest with stage
recordings + cleanup stats. `--rig` adds the CPU auto-rig stage.

### Remaining gaps vs Tripo3D (honest, after round 1)
1. Space queue latency: HF Spaces are free-tier shared — generations take
   2–15 min wall-clock vs Tripo's seconds. Mitigated by the fallback chain.
2. Texture backs: TRELLIS.2 bakes good textures but backs are still hallucinated
   from one view. Next: Hunyuan3D-Paint-equivalent via space, or multi-view
   input (owner can supply front+back images — pipeline accepts one today).
3. Topology: triangle soup persists; hole-fill + weld help, true quad remesh
   still open (research: Open3D/MeshLab-based remesh on CPU).
4. Pixal3D (TencentARC, SIGGRAPH 2026) — pixel-aligned TRELLIS.2 successor —
   not yet wired; top candidate for round 2.
