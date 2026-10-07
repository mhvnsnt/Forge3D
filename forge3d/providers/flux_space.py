"""FLUX.1-schnell text-to-image via official HuggingFace Space.

Keyless Gradio REST, stateless single call:
  /infer(prompt, seed, randomize_seed, width, height, num_inference_steps)
    -> (image, seed)
Runs on HF's free GPU — no local GPU needed. FLUX.1-schnell weights are
Apache-2.0 licensed, so outputs are commercial-safe.

Space: https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell

Concept stage only (like pollinations-image): fetch_image() produces the
concept PNG; feed it to an image-to-3D provider. generate() raises loudly
per the provider contract (no fake GLB from a 2D image).
"""
from __future__ import annotations

from pathlib import Path

from .hf_space import (SpaceError, call_endpoint, download_filedata,
                       find_filedata)

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class FluxSpaceProvider(ModelProvider):
    info = ProviderInfo(
        name="flux-space",
        kind="api",
        capabilities=[Capability.TEXT_TO_IMAGE],  # concept-image stage
        license="Apache-2.0 (black-forest-labs/FLUX.1-schnell); Space terms apply",
        commercial_ok=True,
        needs_gpu=False,   # GPU lives on HF's side
        needs_key=False,   # keyless
        quota_note="free; HF Spaces queue/rate limits apply (ZeroGPU fair use)",
    )

    SPACE_HOST = "black-forest-labs-flux-1-schnell.hf.space"

    def is_available(self) -> tuple[bool, str]:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://{self.SPACE_HOST}/gradio_api/info",
                headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                info = r.read(64)
            if b"infer" in info or r.status == 200:
                return True, "space reachable (keyless)"
            return False, "space API info unexpected"
        except Exception as e:  # noqa: BLE001
            return False, f"space unreachable: {e}"

    def fetch_image(self, prompt: str, out_path: Path,
                    width: int = 1024, height: int = 1024,
                    seed: int = 42, steps: int = 4,
                    timeout_min: int = 10) -> Path:
        """Generate a concept image; returns the saved PNG path."""
        try:
            res = call_endpoint(
                self.SPACE_HOST, "/infer",
                [prompt, seed, False, width, height, steps],
                timeout_min=timeout_min)
        except SpaceError as e:
            raise ProviderError(f"flux-space failed: {e}")
        fds = list(find_filedata(res))
        if not fds:
            raise ProviderError(
                f"flux-space: no image in /infer result: {str(res)[:300]}")
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            download_filedata(self.SPACE_HOST, fds[0], out_path)
        except SpaceError as e:
            raise ProviderError(f"flux-space download failed: {e}")
        if out_path.stat().st_size < 1024:
            raise ProviderError("flux-space: downloaded image suspiciously small")
        return out_path

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 **kwargs) -> GenerateResult:
        raise ProviderError(
            "flux-space is a concept stage, not a 3D provider; "
            "use fetch_image() then run an image-to-3d provider")
