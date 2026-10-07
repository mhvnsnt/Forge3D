"""Concept-image stage: text prompt -> reference image for image-to-3D.

This is the owner's tweak point in the full loop: the generated concept
image lands at <out>/concept.png, the owner can swap in their own image
(--image) and re-run from there. Never silently substitutes a prompt-only
run into an image-to-3D provider that needs pixels — that path raises loudly.
"""
from __future__ import annotations

from pathlib import Path

from ..providers.base import Capability, ProviderError


def _text_to_image_providers():
    from ..providers.registry import discover
    out = {}
    for name, p in discover().items():
        if Capability.TEXT_TO_IMAGE in p.info.capabilities:
            ok, _ = p.is_available()
            if ok:
                out[name] = p
    return out


def concept_image(prompt: str, out_dir: Path, backend: str = "auto",
                  seed: int = 42) -> Path:
    """Generate a concept image from a text prompt. Returns the image path.

    Raises ProviderError if no text-to-image provider is available.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    providers = _text_to_image_providers()
    if not providers:
        raise ProviderError(
            "concept stage: no text-to-image provider available "
            "(pollinations-image needs network)")
    if backend != "auto":
        if backend not in providers:
            raise ProviderError(
                f"concept stage: backend '{backend}' not available "
                f"(have: {sorted(providers)})")
        order = [backend]
    else:
        # prefer pollinations-image (keyless, Flux-class); extend as backends land
        order = sorted(providers, key=lambda n: 0 if n == "pollinations-image" else 1)
    errors = []
    for name in order:
        p = providers[name]
        out = out_dir / "concept.png"
        try:
            if hasattr(p, "fetch_image"):
                return p.fetch_image(prompt, out, seed=seed)
            raise ProviderError(f"{name}: no fetch_image() method")
        except ProviderError as e:
            errors.append(f"{name}: {e}")
    raise ProviderError("concept stage: all text-to-image providers failed: "
                        + "; ".join(errors))
