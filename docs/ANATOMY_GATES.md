# Forge3D Anatomical Defect Gates

**Origin:** `grunt_onyx` shipped to the owner with a horse-shaped lower leg and was
presented as a roster candidate. Owner verdict: TRASH. Generation is frozen until the
pipeline is 400% better — these gates are part of that bar. A horse-legged model must
NEVER reach the owner again.

**Module:** `forge3d/pipelines/anatomy_gates.py` (Forge3D-original, no third-party code).
**Optional ML second opinion:** MediaPipe Pose Landmarker (`pose_landmarker_full.task`,
Apache-2.0, Google) at `~/.forge3d/weights/mediapipe/` or `$FORGE3D_MEDIAPIPE_BUNDLE`.
The geometric gates are the primary defense and need no ML.

## How it works

Every generated GLB is normalized (feet at y=0, height=1) and sliced into horizontal
vertex bands. Below mid-body the slice must split into two x-clusters (the legs);
each leg gets a thickness profile (max of x-width / z-depth per band), from which:

- **thigh** = max thickness in the upper leg region
- **calf** = max thickness in the lower leg region (above the ankle)
- **knee** = deepest local minimum of the smoothed profile inside [0.18, 0.38] of height

## Gates

| Gate | What it catches | Threshold (human basis) |
|---|---|---|
| `leg_split` | fused/absent legs | must split into 2 clusters below mid-body |
| `leg_segment_ratio` | **horse-like lower leg** — uniform thin tube, no calf bulge | calf/thigh in [0.50, 0.88] (human ~0.60–0.75) |
| `thigh_absolute` | spindly/animal legs | thigh ≥ 0.085 of height |
| `knee_articulation` | straight tube, no knee joint | profile dips ≥ 8% inside knee band |
| `leg_symmetry` | one deformed leg | L/R thigh+calf diff ≤ 30% |
| `leg_axis` | digitigrade/reverse-joint kink | centroid-path kink ≤ 6% of height (FLAG) |
| `head_presence` | missing/floating/giant head | single top component, width 0.08–0.30 of height |
| `feet_grounded` | floating character | feet within 2% of ground |
| `rig_bone_ratios` | inhuman skeleton (skinned GLBs) | thigh/shin [0.85, 1.15], upper/fore [0.60, 0.95] |
| `preview_pose` | missing limbs, wrong joint order (MediaPipe) | all leg landmarks visible; hip<knee<ankle; knee 135–205° |

Verdict: FAIL if any gate FAILs → GLB copied to `<out_dir>/quarantine/` with its
report, pipeline raises `ProviderError` loudly. FLAG ships with warnings (existing
`gates.py` contract). CLI: `python -m forge3d.pipelines.anatomy_gates model.glb [preview.png]`
(exit 0 = PASS, 2 = FAIL).

Pipeline integration: `pipelines/pipeline.py::run_from_mesh` runs `run_anatomy_gates`
right after the structural `run_gates`, same fail-loudly/quarantine contract.

## Proof corpus (measured 2026-10-07)

### grunt_onyx — MUST FAIL → **FAIL** ✅ (the horse leg)

| Gate | Verdict | Measured |
|---|---|---|
| leg_segment_ratio | **FAIL** | L calf/thigh **1.224**, R **0.935** — both above 0.88: uniform thin tubes, no calf bulge |
| thigh_absolute | **FAIL** | L thigh **0.054**, R **0.066** of height — floor is 0.085 |
| knee_articulation | **FAIL** | dip **0.0** both legs — no knee joint at all |
| leg_symmetry / leg_axis / head / feet | PASS | symmetric, straight axes, head + feet fine |
| preview_pose | PASS | MediaPipe found a sane pose (knee 175.6°/171.4°) — **pose alone does NOT catch this defect**; the geometric profile gates are the defense |

### trellis2-concept2-high (brawler) — MUST PASS → **PASS** ✅

| Gate | Verdict | Measured |
|---|---|---|
| leg_segment_ratio | PASS | L **0.650**, R **0.733** — textbook human |
| thigh_absolute | PASS | L **0.131**, R **0.145** of height |
| knee_articulation | PASS | knees at 0.26/0.27 of height, dips 13%/31% |
| leg_symmetry / leg_axis / head / feet | PASS | all sane |
| preview_pose | PASS | fighting stance correctly tolerated (R knee 152.3°) |

## Key finding

MediaPipe pose estimation **cannot** catch the horse-leg defect — joint angles look
normal (175°) because the defect is in limb *shape*, not joint *angles*. The defense
is the cross-section thickness profile: a human leg has thigh ≫ calf ≫ ankle with a
knee dip; a horse-like leg is a uniform tube. Any future "looks fine at a glance"
defect needs a shape-based gate, not just a pose-based one.

## Limits (honest)

- Assumes a standing, roughly A-pose character. Sitting/creature/non-humanoid models
  fail by design — that is intended.
- Boots inflate the ankle region; ankle-specific checks are deliberately omitted.
- Arm anatomy is covered by MediaPipe landmarks only (geometric arm profiling is
  future work — arms vary too much in pose for a simple band method).
- Mitten hands / fused fingers are NOT caught — needs a hand detector (open item).
