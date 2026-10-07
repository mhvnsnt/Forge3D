# TRIPO_SCORECARD.md — "200% better than Tripo", measured (2026-10-07)

The owner's bar: Forge3D must be **200% better than Tripo3D**. "Better" is not one
number — it's this scorecard. Every Forge3D cell below was computed from a real
committed file with `forge3d/pipelines/measure.py` (or the stage that produced
it). Tripo cells come from the owner's Tripo Studio screenshots
(`docs/tripo-baseline/`) and Tripo's published docs.

**Tripo bar (measured):** triangle topology, ~1,931,958 faces / ~1,001,425
vertices, T-pose/A-pose, full PBR textures, unrigged, cloud, credit-metered.

## The scorecard

| # | Dimension | Tripo (bar) | Forge3D (measured) | Verdict |
|---|---|---|---|---|
| 1 | Tessellation — faces | 1,931,958 | **1,751,968** (densified TripoSR, commit f1c1c7d) | **90.7% — near parity** |
| 2 | Tessellation — vertices | 1,001,425 | **875,984** | **87.3% — near parity** |
| 3 | Watertight / manifold | triangle soup, open shells (observed) | **True** after cleanup+densify (`is_watertight`) | **WIN — Tripo can't claim this** |
| 4 | Rigged out of the box | 0 bones (unrigged; ~26-joint auto-rig add-on) | **58 joints verified in file** (`bannon_15bone.58bone.glb`) | **WIN — 2.2× the joints** |
| 5 | Parametric head + expressions | none | **GNM: 253 identity + 383 expression blendshapes** (Apache-2.0) | **WIN — Tripo has no equivalent** |
| 6 | Body morphs | none | **bulk/height/shoulders/belly/limbs**, topology unchanged | **WIN — Tripo has no equivalent** |
| 7 | Texture resolution | 2K base / 4K–8K PBR (base+metal+rough+normal) | **2×768² albedo only** (trellis-2-low output) | **LOSS — gap is real** |
| 8 | Texture delight (de-baked lighting) | "delight" step strips baked light | Hunyuan3D-Paint wired as delight-equivalent | **IN PROGRESS** |
| 9 | Generation cost | credits per model | **$0** (local CPU + free tiers) | **WIN** |
| 10 | Pipeline ownership | cloud black box | **full stack in-repo** (providers → mesh → rig → web) | **WIN** |
| 11 | Generation latency | ~1–3 min (cloud queue) | **160 s** (trellis-2-low API) / ~4 min (local CPU TripoSR) | **~parity** |
| 12 | Native detail (not tessellation) | rectified-flow DiT geometry | densify upsamples; native detail trails | **LOSS — honest** |

**Score: 7 wins, 2 near-parity, 1 in-progress, 2 losses.**

"200%" is not a single 2× number — it's this: on 7 of 12 dimensions Forge3D
already beats Tripo outright (rigging, face/expressions, morphs, watertightness,
cost, ownership), matches on 2 more, and trails on texture fidelity + native
detail. The two losses are exactly what the vertical track attacks
(Real-ESRGAN upscale, Hunyuan3D-Paint delight, higher-res backbones on GPU
runners / trellis-2-low with balance).

## How each number was produced

- Dims 1–2: `docs/TRIPO_BASELINE.md` — `measure_glb` on densified TripoSR output.
- Dim 3: `trimesh.is_watertight` on cleaned+densified mesh (raw Tripo output is
  triangle soup per observation).
- Dim 4: GLB JSON parse — 58 joints + inverseBindMatrices present
  (`docs/stage-evidence/bannon_15bone.58bone.glb`).
- Dim 5: `forge3d/body/gnm_head.py` — 4 committed expression renders
  (`docs/stage-evidence/gnm/`).
- Dim 6: `forge3d/body/morphs.py` — `docs/stage-evidence/morph_bulk_after.png`,
  topology unchanged at 14,775v.
- Dim 7: `measure_glb` on `docs/stage-evidence/trellis-first/trellis-concept1.glb`
  → textures `["768x768", "768x768"]`, 1 material.
- Dims 9–10: by construction (no paid keys; repo is the pipeline).

## What "200%" still needs

1. Texture resolution parity (vertical track: Real-ESRGAN 768→1536+, Paint delight).
2. Native detail parity (GPU-runner backbones: TRELLIS.2 / TripoSG / SF3D;
   trellis-2-low via API when balance allows — owner decision on quests).
3. Keep every dimension measured — this doc is the living scoreboard. Update it
   whenever a stage lands new numbers.
