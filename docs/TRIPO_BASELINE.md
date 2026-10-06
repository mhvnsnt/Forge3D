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

| Metric | Tripo bar | Forge3D (fill per run) | Delta |
|---|---|---|---|
| Faces | ~1.93M | _pending first measured run_ | — |
| Vertices | ~1.00M | _pending_ | — |
| Texture resolution | _read from Tripo GLB when available_ | _pending_ | — |
| Watertight / manifold | _pending_ | _pending_ | — |
| Bones (rig) | 0 (Tripo Studio output is unrigged; rigging is a paid add-on) | _pending_ | — |

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
   Zero123++ is CC-BY-NC research-only, MV-Adapter pending license check)
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
