# Scan path: phone photogrammetry -> mesh (WIRED 2026-10-07, GPU-gated)

Owner ask: "scan" models like Prisma 3D / Blender workflows allow.

## Status

`forge3d/scan/stage.py` is wired with a HARD gate: `scan_photos()` raises
`ScanError` loudly when pycolmap / the COLMAP binary / CUDA is missing, and
NEVER returns a fake mesh. Selftest check `scan-gate-loud-without-gpu`
proves the gate on GPU-less hosts. Photo validation requires >= 8 circling
photos or it also fails loudly.

## COLMAP (BSD-3-Clause, ETH Zurich) — commercial-safe

- The standard open-source Structure-from-Motion + Multi-View Stereo pipeline.
- Phone photos (20-60 shots circling the subject) -> dense point cloud ->
  meshed via Poisson reconstruction -> textured mesh.
- `pycolmap` (pip, BSD) exposes the SfM pipeline in Python; the MVS
  (PatchMatch) step needs CUDA; Poisson meshing shells to the COLMAP binary.
- CPU-only is *slow* (tens of minutes for a head scan) but the SfM half works;
  dense MVS is the CUDA-gated step.

## Where it plugs into Forge3D

`scan_photos(photo_dir, out_dir)` -> textured `scan.glb` -> downstream:
`blender/stage.py` cleanup -> `pipelines/texture.py` -> `pipelines/rig.py`
retarget_58. Every downstream stage already exists.

## Kaggle free-GPU runner path (how to actually run a scan)

1. Kaggle notebook, GPU (T4 x2, 30h/week free): `pip install pycolmap`
   + `apt install colmap` (or conda-forge colmap).
2. Clone `mhvnsnt/Forge3D`, upload phone photos to `photos/`.
3. `python3 -c "from forge3d.scan import scan_photos;
   print(scan_photos('photos', 'out'))"`.
4. Download `out/scan.glb` -> continues through the normal Forge3D pipeline
   (cleanup, texture, rig) anywhere.

## Verdict

Wired and gated; runnable the moment a CUDA host is available. Not runnable
on the CPU-only agent VM by design (loud failure, never a fake mesh).

Alternatives noted, not evaluated: OpenMVS (MPL-2.0), Meshroom/AliceVision
(MPL-2.0, needs CUDA), NeRF-based (instant-ngp is non-commercial).
