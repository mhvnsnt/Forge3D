"""COLMAP/pycolmap photogrammetry scan stage: phone photos -> textured mesh.

Pipeline: phone photos (20-60 circling the subject) -> SfM (pycolmap:
feature extraction, matching, incremental mapping) -> dense MVS
(PatchMatch, CUDA) -> Poisson mesh -> texture -> GLB.

HARD GATE (binding): dense MVS needs CUDA. Without a GPU -- or without
pycolmap / the COLMAP binaries -- scan_photos() raises ScanError LOUDLY.
It NEVER returns a fake, placeholder, or synthetic mesh. The failure message
names exactly what is missing and points at docs/SCAN_PATH.md (Kaggle
free-GPU path).

License: COLMAP/pycolmap are BSD-3-Clause (ETH Zurich) -- commercial-safe.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

MIN_PHOTOS = 8
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


class ScanError(Exception):
    """Raised loudly whenever scanning cannot run for real."""


def _has_cuda() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _has_pycolmap() -> tuple[bool, str]:
    try:
        import pycolmap  # noqa
        return True, "ok"
    except ImportError as e:
        return False, f"pycolmap not installed ({e}); pip install pycolmap"


def _has_colmap_bin() -> tuple[bool, str]:
    if shutil.which("colmap"):
        return True, "ok"
    return False, "COLMAP binary not on PATH (needed for poisson_mesher)"


def check_requirements() -> tuple[bool, list[str]]:
    """Return (ok, [missing-reason, ...]). Empty reasons == runnable."""
    missing: list[str] = []
    ok_pc, why_pc = _has_pycolmap()
    if not ok_pc:
        missing.append(why_pc)
    ok_bin, why_bin = _has_colmap_bin()
    if not ok_bin:
        missing.append(why_bin)
    if not _has_cuda():
        missing.append("no CUDA GPU (torch.cuda.is_available() is False) -- "
                       "dense PatchMatch MVS is impractically slow without one")
    return (len(missing) == 0), missing


def is_available() -> tuple[bool, str]:
    ok, missing = check_requirements()
    if ok:
        return True, "ok"
    return False, "; ".join(missing)


def validate_photos(photo_dir: str | Path, min_photos: int = MIN_PHOTOS) -> list[Path]:
    """Return sorted photo paths, or raise ScanError (too few / none)."""
    photo_dir = Path(photo_dir)
    if not photo_dir.is_dir():
        raise ScanError(f"photo dir not found: {photo_dir}")
    photos = sorted(p for p in photo_dir.iterdir()
                    if p.suffix.lower() in PHOTO_EXTS and p.is_file())
    if len(photos) < min_photos:
        raise ScanError(
            f"only {len(photos)} usable photos in {photo_dir} "
            f"(need >= {min_photos} circling the subject)")
    return photos


def _run(cmd: list[str], cwd: Path) -> None:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       timeout=6 * 3600)
    if r.returncode != 0:
        raise ScanError(f"command failed: {' '.join(cmd)}\n"
                        f"--- stdout ---\n{r.stdout[-2000:]}\n"
                        f"--- stderr ---\n{r.stderr[-2000:]}")


def scan_photos(photo_dir: str | Path, out_dir: str | Path,
                camera_model: str = "OPENCV",
                min_photos: int = MIN_PHOTOS) -> Path:
    """Run the full scan. Returns the textured mesh GLB path.

    Raises ScanError loudly if the requirements gate fails -- never a fake mesh.
    """
    photos = validate_photos(photo_dir, min_photos=min_photos)

    ok, missing = check_requirements()
    if not ok:
        raise ScanError(
            "SCAN BLOCKED -- refusing to fake a mesh. Missing:\n  - "
            + "\n  - ".join(missing)
            + "\nSee docs/SCAN_PATH.md for the Kaggle free-GPU runner path.")

    import pycolmap  # noqa  (gate above guarantees importability)

    out = Path(out_dir)
    work = out / "colmap_work"
    sparse_dir = work / "sparse"
    dense_dir = work / "dense"
    for d in (sparse_dir, dense_dir):
        d.mkdir(parents=True, exist_ok=True)

    # --- SfM ---
    db = work / "database.db"
    if db.exists():
        db.unlink()
    pycolmap.extract_features(db, photos[0].parent,
                              camera_model=camera_model)
    pycolmap.match_exhaustive(db)
    maps = pycolmap.incremental_mapping(db, photos[0].parent, sparse_dir)
    if not maps:
        raise ScanError("SfM failed: incremental mapping produced no model "
                        "(photos may not overlap enough)")
    # keep the largest reconstruction
    rec = max(maps.values(), key=lambda m: len(m.images))
    if len(rec.images) < max(3, len(photos) // 3):
        raise ScanError(f"SfM registered only {len(rec.images)}/{len(photos)} "
                        "images -- reshoot with more overlap")
    rec.write(sparse_dir / "0")

    # --- dense MVS (CUDA) ---
    pycolmap.undistort_images(dense_dir, sparse_dir / "0",
                              photos[0].parent)
    pycolmap.patch_match_stereo(dense_dir)   # needs CUDA; gate guarantees it
    pycolmap.stereo_fusion(dense_dir / "fused.ply", dense_dir)

    # --- Poisson mesh via COLMAP binary ---
    _run(["colmap", "poisson_mesher",
          "--input_path", str(dense_dir / "fused.ply"),
          "--output_path", str(dense_dir / "meshed-poisson.ply")], dense_dir)

    # --- to textured GLB ---
    import trimesh
    mesh = trimesh.load(dense_dir / "meshed-poisson.ply", process=True)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) < 100:
        raise ScanError("Poisson meshing produced an unusable mesh")
    glb = out / "scan.glb"
    mesh.export(glb)
    (out / "scan_stats.txt").write_text(
        f"photos={len(photos)} registered={len(rec.images)} "
        f"verts={len(mesh.vertices)} tris={len(mesh.faces)}\n")
    return glb
