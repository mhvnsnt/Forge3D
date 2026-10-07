# Scan path: phone photogrammetry -> mesh (evaluation, 2026-10-06)

Owner ask: "scan" models like Prisma 3D / Blender workflows allow. Brief
evaluation of the open-source options:

## COLMAP (BSD-3-Clause, ETH Zurich)

- The standard open-source Structure-from-Motion + Multi-View Stereo pipeline.
- Phone photos (20-60 shots circling the subject) -> dense point cloud ->
  meshed via Poisson reconstruction -> textured mesh.
- `pycolmap` (pip, BSD) exposes the SfM pipeline in Python; the MVS
  (PatchMatch) step needs the compiled COLMAP binaries.
- CPU-only is *slow* (tens of minutes for a head scan) but works; GPU
  (CUDA) makes it practical.
- License is commercial-safe (BSD-3-Clause).

## Where it plugs into Forge3D

`scan/` (not yet built) would be: phone photos -> COLMAP SfM+MVS ->
Poisson mesh -> `blender/stage.py` cleanup -> `pipelines/texture.py` ->
`pipelines/rig.py` retarget_58. Every downstream stage already exists.

## Verdict

Documented, not wired: on this CPU-only VM the MVS step is impractically
slow, and COLMAP needs compiled binaries per host. Recommended host is the
same free GPU runner (Kaggle) that unlocks SF3D/TRELLIS.2 — COLMAP CUDA
builds run there. When a GPU runner is live, `scan/` is ~1 day of wiring.

Alternatives noted, not evaluated: OpenMVS (MPL-2.0), Meshroom/AliceVision
(MPL-2.0, needs CUDA), NeRF-based (instant-ngp is non-commercial).
