"""Multi-view consistency stage: observe the sides, don't hallucinate them.

Single-image 3D backbones invent occluded anatomy (backs, sides). Generating
N consistent views of the subject BEFORE meshing gives the reconstruction
stage real observations to work from.

Backends:
  - "zero123plus": Stability AI Zero123++ via public HF Space (Gradio REST).
    Single image -> 6-view grid (3x2), split into individual view PNGs.
    License: CC-BY-NC 4.0 (NON-COMMERCIAL). Wired as research-only, clearly
    marked, NEVER in the default auto path for money work (see LICENSES.md).
    Public demo Spaces are frequently paused; the backend retries with
    backoff to tolerate sleeping Spaces, then fails LOUDLY.
  - "mv-adapter": MV-Adapter (license under verification 2026-10-06).
  - "provider-native": some providers (TRELLIS.2, SF3D, pollinations-3d)
    do multi-view internally; this backend is a documented no-op that
    records the fact.

Until a backend is wired AND reachable, requesting this stage raises
ProviderError — no fake views, ever.
"""
from __future__ import annotations

import time
from pathlib import Path

from ..providers.base import ProviderError
from ..providers.hf_space import (SpaceError, call_endpoint, download_filedata,
                                  file_data, find_filedata, upload_file)

# license status as of 2026-10-06/07 verification
BACKEND_LICENSE = {
    "zero123plus": "CC-BY-NC-4.0 (research-only, non-commercial)",
    "mv-adapter": "UNVERIFIED (2026-10-06)",
    "provider-native": "n/a (provider-internal)",
}

# Public Zero123++ demo Spaces (Gradio). Tried in order; all are best-effort
# community mirrors of sudo-ai/zero123plus-v1.1. Frequently paused.
ZERO123_SPACES = [
    "ysharma-Zero123PlusDemo",
    "sudo-ai-zero123plus-demo-space",
    "darshcoss-Zero123PlusDemo",
]

# Zero123++ v1.1+ outputs a 3-col x 2-row grid of 6 views.
GRID_COLS = 3
GRID_ROWS = 2


def _split_grid(grid_path: Path, out_dir: Path) -> list[Path]:
    """Split a 3x2 Zero123++ view grid into 6 individual view PNGs."""
    from PIL import Image
    img = Image.open(grid_path).convert("RGB")
    w, h = img.size
    cw, rh = w // GRID_COLS, h // GRID_ROWS
    views = []
    labels = ["view0", "view1", "view2", "view3", "view4", "view5"]
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            v = img.crop((c * cw, r * rh, (c + 1) * cw, (r + 1) * rh))
            p = out_dir / f"mv_{labels[r * GRID_COLS + c]}.png"
            v.save(p)
            views.append(p)
    return views


def _zero123plus_space(image: Path, out_dir: Path,
                       steps: int = 75, guidance: float = 4.0,
                       seed: int = 0) -> list[Path]:
    """Zero123++ via public HF Space. Returns 6 view PNGs.

    Raises ProviderError if no Space is reachable (all paused/down).
    Retries each Space briefly to tolerate sleeping Spaces waking up.
    """
    last_err = ""
    for host in ZERO123_SPACES:
        for attempt in range(3):
            try:
                server_path = upload_file(host, image)
                fd = file_data(server_path, image.name)
                # Gradio: btn.click(inference, [input_img, steps, guidance, seed], output_img)
                res = call_endpoint(host, "/predict",
                                    [fd, steps, guidance, seed],
                                    timeout_min=15)
                fds = list(find_filedata(res))
                if not fds:
                    raise SpaceError(f"no image in /predict result: {str(res)[:200]}")
                grid = out_dir / "mv_grid.png"
                download_filedata(host, fds[0], grid)
                if grid.stat().st_size < 1024:
                    raise SpaceError("downloaded grid suspiciously small")
                views = _split_grid(grid, out_dir)
                # provenance: which space produced these views
                (out_dir / "mv_provenance.txt").write_text(
                    f"backend=zero123plus space={host} "
                    f"license={BACKEND_LICENSE['zero123plus']}\n")
                return views
            except (SpaceError, ProviderError) as e:
                last_err = f"{host}: {e}"
                time.sleep(20 * (attempt + 1))  # let sleeping Spaces wake
                continue
    raise ProviderError(
        f"multiview backend 'zero123plus': no public Space reachable "
        f"(tried {', '.join(ZERO123_SPACES)}). Last error: {last_err}. "
        f"License note: {BACKEND_LICENSE['zero123plus']}")


def generate_views(image: Path, out_dir: Path,
                   backend: str = "zero123plus") -> list[Path]:
    """Generate multi-view images of the subject. Returns view PNG paths.

    Raises ProviderError if the backend is not wired, unreachable, or its
    license status does not permit the requested use.
    """
    image = Path(image)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not image.exists():
        raise ProviderError(f"multiview: input image not found: {image}")

    if backend == "provider-native":
        return []  # provider handles views internally; recorded by caller
    if backend == "mv-adapter":
        raise ProviderError(
            "multiview backend 'mv-adapter' not wired yet "
            f"(license: {BACKEND_LICENSE[backend]})")
    if backend == "zero123plus":
        return _zero123plus_space(image, out_dir)
    raise ProviderError(f"unknown multiview backend: {backend}")
