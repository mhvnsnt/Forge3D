"""Multi-view consistency stage: observe the sides, don't hallucinate them.

Single-image 3D backbones invent occluded anatomy (backs, sides). Generating
N consistent views of the subject BEFORE meshing gives the reconstruction
stage real observations to work from.

Backends:
  - "zero123plus": Stability AI Zero123++ — single image -> 6 views.
    License: CC-BY-NC 4.0 (NON-COMMERCIAL). Wired as research-only, clearly
    marked, NEVER in the default auto path for money work (see LICENSES.md).
  - "mv-adapter": MV-Adapter (license under verification 2026-10-06).
  - "provider-native": some providers (TRELLIS.2, SF3D, pollinations-3d)
    do multi-view internally; this backend is a documented no-op that
    records the fact.

Until a backend is wired, requesting this stage raises ProviderError —
no fake views, ever.
"""
from __future__ import annotations

from pathlib import Path

from ..providers.base import ProviderError

# license status as of 2026-10-06 verification
BACKEND_LICENSE = {
    "zero123plus": "CC-BY-NC-4.0 (research-only, non-commercial)",
    "mv-adapter": "UNVERIFIED (2026-10-06)",
    "provider-native": "n/a (provider-internal)",
}


def generate_views(image: Path, out_dir: Path,
                   backend: str = "zero123plus") -> list[Path]:
    """Generate multi-view images of the subject. Returns view PNG paths.

    Raises ProviderError if the backend is not wired or its license status
    does not permit the requested use.
    """
    if backend == "provider-native":
        return []  # provider handles views internally; recorded by caller
    if backend == "mv-adapter":
        raise ProviderError(
            "multiview backend 'mv-adapter' not wired yet "
            f"(license: {BACKEND_LICENSE[backend]})")
    if backend == "zero123plus":
        raise ProviderError(
            "multiview backend 'zero123plus' not wired yet "
            f"(license: {BACKEND_LICENSE[backend]} — research-only)")
    raise ProviderError(f"unknown multiview backend: {backend}")
