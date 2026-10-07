# TRIPO_BASELINE.md — the bar to beat (owner-supplied, 2026-10-06)

Reference images: `docs/tripo-baseline/` (10 images: 2 generated wrestler
outputs, 4 Tripo Studio viewport screenshots with model stats, plus context
shots). All numbers below are read directly off the owner's Tripo Studio
screenshots — this is the measured bar, not marketing copy.

## Tripo Studio output (measured)

| Model (screenshot) | Topology | Faces | Vertices |
|---|---|---|---|
| red-hooded T-pose figure | Triangle | 1,931,958 | 1,001,425 |
| horned warrior (black tee) | Triangle | 1,904,964 | 977,503 |
| horned warrior (purple robe) | Triangle | 1,921,291 | 1,002,955 |
| horned warrior (tattoo) | Triangle | 1,993,136 | 1,025,810 |
| **Median (the bar)** | **Triangle** | **~1.93M** | **~1.00M** |

Other observed properties:
- **Pose:** T-pose / A-pose output (rig-ready stance).
- **Textures:** full PBR color textures, crisp at viewport zoom (see
  `tripo-gen-skull-wrestler.png` — clean albedo, skin/cloth/metal separation).
- **UI notes (for the web build):** left icon toolbar, model-info card
  (Topology/Faces/Vertices), bottom bar with *Edit in Workspace*, *Share*,
  *Export* (purple button), credits pill + *Upgrade* top-center, prompt title
  bottom-left, *Model Info* bottom-right.

## Where Forge3D stands (measured with `forge3d/pipelines/measure.py`)

**Measured 2026-10-07** — first real TripoSR run through the web API
(`POST /api/upload` → `POST /api/generate` → triposr provider, texture=lanczos,
densify=true). Test input: `web/data/test-images/wrestler_rgba.png` (synthetic
wrestler silhouette, RGBA). Job `be5358713bf2`, all values from `measure_glb`.

| Metric | Tripo bar | Forge3D (measured) | Delta |
|---|---|---|---|
| Faces (raw backbone) | ~1.93M | 112,680 (TripoSR, mc_res 256) | 5.8% — confirms the research: TripoSR-class emits far less tessellation |
| Faces (after densify) | ~1.93M | **1,751,968** | **90.7% of the Tripo bar** |
| Vertices (after densify) | ~1.00M | **875,984** | **87.3% of the Tripo bar** |
| Watertight / manifold | no published number; raw Tripo output is triangle soup with known open shells | raw: False → **cleaned+densified: True** (trimesh `is_watertight`) | **our edge: watertight output; Tripo's observed rate is lower** |
| Texture resolution | standard ~2K / detailed / extreme 8K; PBR set = base_color + metallic + roughness + normal | vertex colors (TripoSR bakes no texture maps); lanczos stage refines when maps exist | gap: texture-map baking is the next stage to wire |
| Game-ready poly target | 50–100K (their docs); Smart Low Poly 500–20K | densify targets tessellation parity; lod_chain port planned | — |
| Quad output | ≤25K faces (P-series, FBX only) | triangle only (glTF can't store quads) | — |
| Bones (rig) | 0 (Tripo Studio output is unrigged) | rig stage via instance-rig (beyond-Tripo edge; DOWN on CPU VM — needs libEGL) | — |
| Pose | T-pose/A-pose output | backbone-dependent (this test: A-pose-ish silhouette in → figure out) | — |
| Latency | ~1–3 min/generation (async cloud) | ~10 min CPU (bf16, 2-core VM); ~45s–3min quoted for faster hosts | slower on this VM, $0 |

**Honest reading:** raw TripoSR is 5.8% of Tripo's tessellation — the "geometry
density" gap from the steer is real and measured. Our densify stage closes it
to 90.7% *tessellation* parity, watertight. Tessellation ≠ detail: subdivision
adds triangles, not surface detail — real detail still needs higher-res
backbones (TRELLIS.2 / TripoSG / SF3D on GPU runners). What we beat Tripo on
*today*: watertightness (theirs is triangle soup) and $0 fully-owned pipeline.
What we don't beat yet: PBR texture maps (we emit vertex colors; their PBR
set is base_color + metallic + roughness + normal) and raw surface detail.

### Update 2026-10-07 — first high-quality generation (trellis-2-low)

`docs/stage-evidence/trellis-first/` — Pollinations 3D API, `trellis-2-low`,
concept1 (hooded street fighter). Measured with `measure_glb`:

| Metric | Tripo bar | Forge3D trellis-2-low | Delta |
|---|---|---|---|
| Faces | ~1.93M | 96,825 | 5.0% — low tessellation, but native detail is high |
| Vertices | ~1.00M | 57,865 | 5.8% |
| Textures | 2K–8K PBR set | **2×768² albedo, 1 PBR material** | real texture maps now (was: vertex colors) |
| Latency | ~1–3 min | 160 s | parity |
| Cost | credits | 0.24 Quest Pollen (free tier) | free; balance now 0 — further gens need top-up/quests (owner decision) |

This is the texture-quality jump the baseline called for: from vertex colors to
real baked texture maps. Tessellation is low on `trellis-2-low` by design —
run it through `densify` for the 90.7% parity number. Full dimension-by-dimension
verdict lives in `docs/TRIPO_SCORECARD.md`.

### Why Tripo is good (research 2026-10-06 — what we're countering)
- **TripoSR** (the open one): LRM → triplane → NeRF → marching cubes; fast and MIT, but projection textures (blurry backs — confirmed) and low tens-of-thousands of tris. It's the baseline, not the ceiling.
- **TripoSG** (their quality jump): rectified-flow DiT in a 3D VAE latent trained with SDF + surface-normal + eikonal loss on 2M curated samples; MoE; geometry-only. **Our answer: TripoSG itself is MIT — wired as a provider.**
- **Tripo 3.0**: SparseFlex (Flexicubes accuracy + sparse voxels, up to 1024³, −82% Chamfer / +88% F-score) + PBR texture model with a "delight" step (strips baked lighting before texturing — key crispness factor) + 4K/8K maps + native quad topology (P-series). **Our answers: TRELLIS.2 (MIT SOTA anchor) on GPU runners; Hunyuan3D-Paint as the delight-equivalent texture stage; densify for tessellation parity.**
- **Their edge is the stack**, not one trick: high-res geometry + data curation + PBR pipeline + production tooling. Ours is the same stack shape at $0: TripoSG geometry → Paint texture → MV-Adapter multi-view → measure → rig.

## Gap-closing plan (mapped to the numbers)

1. **Geometry density** — TripoSR-class backbones emit far less tessellation
   than 1.9M faces. `pipelines/densify.py` upsamples via midpoint
   subdivision (same surface, UV-safe) to tessellation parity. Honest limit:
   subdivision adds triangles, not detail — real detail comes from
   higher-res backbones (TRELLIS.2 / TripoSG / SF3D on GPU runners).
2. **Texture quality** — `pipelines/texture.py` refinement stage
   (lanczos2x now; Real-ESRGAN / Hunyuan3D-Paint when pulled). Attacks the
   blurry-back weakness.
3. **Occluded anatomy** — multi-view stage (`pipelines/multiview.py`;
   Zero123++ is CC-BY-NC research-only, MV-Adapter Apache-2.0 verified 2026-10-06)
   so backs/sides are observed, not hallucinated.
4. **Rig-readiness (the beyond-Tripo edge)** — `pipelines/rig.py` auto-rig
   stage (instance-rig, CPU). Tripo's free output ships unrigged; a Forge3D
   GLB that arrives rigged to the game skeleton beats Tripo on the metric
   that matters for games, even at tessellation parity.

## Verdict rule

"Beats Tripo" = owner-judged character quality at $0 with full pipeline
ownership. The table above is the numerical scoreboard; his eyes are the
final judge. No row gets filled with an estimate — only measured values
from `measure.py`.
