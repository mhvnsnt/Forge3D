# Pose / animate stage evidence (2026-10-06)

Prisma 3D workflow step 5 — pose/animate — implemented in Forge3D as
`forge3d/animation/pose.py`: injects one Bannon procedural move
(`tools/generative/motion/procedural_moves.py`, imported in-place via
`FORGE3D_BANNON_GENERATIVE`, never copied) as a `MOVE_*` glTF animation
into a 58-bone-rigged GLB. Injection validated: the named animation must
exist with >0 channels or the stage raises (never a silent no-op).

## This run

- Input: `bannon_58bone_singlebody.glb` (derived in this stage — see below),
  58-bone Mixamo skeleton, 4,099 verts, single body
- Move: `TAUNT_CROWD` ("arms raised to the crowd, head back", 2.0 s,
  bones RA/LA/S/N/S1)
- Output: `pose_TAUNT_CROWD.glb` — carries `MOVE_TAUNT_CROWD`
  (5 channels, 5 samplers)
- Proof renders: `pose_TAUNT_CROWD_f0.png` (rest) and
  `pose_TAUNT_CROWD_f24.png` (t=1.0 s, arms-raised apex), headless Cycles.

## Input cleaning (this stage)

Both available 58-bone sources (`bannon_15bone.58bone.glb`,
`blender/bannon_muscular_clean.glb`) contain two fully-skinned wrestler
bodies in one vertex buffer — triangle-soup patches, so the bodies were
separated by patch-centroid Y (valley at y≈0.25) in headless Blender and
the unwanted body's patches deleted. Result `bannon_58bone_singlebody.glb`
renders as one complete figure (verified by proof render). The upstream
double-body files were left untouched (other workers' files).

## Known upstream defect (NOT from this stage)

`docs/stage-evidence/bannon_15bone.58bone.glb` (and its source
`bannon_15bone.glb`, committed 2026-10-06 in 43ca3db) contains **two
wrestler bodies side by side in one vertex buffer** (14,789 verts, Y
histogram shows two clusters ~0.7 m apart; both fully skinned). The same
defect is in `blender/bannon_muscular_clean.glb` (8,463 verts, triangle-soup
patches — vert-island flood fill finds 571 patches, so the bodies were
separated by patch-centroid Y instead). The 58bone reference files were
left untouched (other workers' files); the rig lane should rebuild them
from single-body sources.
