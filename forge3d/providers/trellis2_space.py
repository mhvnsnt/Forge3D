"""TRELLIS.2 via official HuggingFace Space (microsoft/TRELLIS.2).

Keyless Gradio REST: upload -> /image_to_3d -> /extract_glb -> download GLB.
Runs on HF's free GPU — no local GPU needed. Microsoft TRELLIS.2 weights
are MIT-licensed (code + weights), so outputs are commercial-safe.

Space: https://huggingface.co/spaces/microsoft/TRELLIS.2
"""
from __future__ import annotations

from pathlib import Path


from .hf_space import (SpaceError, call_endpoint, download_filedata,  # noqa: E402
                      file_data, find_filedata, upload_file)

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,  # noqa: E402
                   ProviderInfo)


class Trellis2SpaceProvider(ModelProvider):
    info = ProviderInfo(
        name="trellis2-space",
        kind="api",
        capabilities=[Capability.IMAGE_TO_3D],
        license="MIT (microsoft/TRELLIS.2 code + weights); Space terms apply",
        commercial_ok=True,
        needs_gpu=False,   # GPU lives on HF's side
        needs_key=False,   # keyless
        quota_note="free; HF Spaces queue/rate limits apply (ZeroGPU fair use)",
    )

    SPACE_HOST = "microsoft-trellis-2.hf.space"

    def is_available(self) -> tuple[bool, str]:
        # light check: space serves its API info (no generation, no key)
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://{self.SPACE_HOST}/gradio_api/info",
                headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                info = r.read(64)
            if b"image_to_3d" in info or r.status == 200:
                return True, "space reachable (keyless)"
            return False, "space API info unexpected"
        except Exception as e:  # noqa: BLE001
            return False, f"space unreachable: {e}"

    def generate(self, *, prompt=None, image: Path | None = None,
                 out_dir: Path, seed: int = 0, resolution: str = "1024",
                 decimation_target: int = 200000, texture_size: int = 2048,
                 timeout_min: int = 25, **kwargs) -> GenerateResult:
        if image is None or not Path(image).exists():
            raise ProviderError("trellis2-space needs --image <file>")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            server_path = upload_file(self.SPACE_HOST, Path(image))
            fd = file_data(server_path, Path(image).name)
            # image_to_3d(image, seed, resolution, ss_*, shape_*, tex_*)
            # defaults from the space UI; 12 steps is the space default
            call_endpoint(self.SPACE_HOST, "/image_to_3d",
                          [fd, seed, resolution,
                           7.5, 0.7, 12, 3.0,      # sparse-structure stage
                           3.0, 0.7, 12, 3.0,      # shape stage
                           3.0, 0.7, 12, 3.0],     # texture stage
                          timeout_min=timeout_min)
            res = call_endpoint(self.SPACE_HOST, "/extract_glb",
                                [decimation_target, texture_size],
                                timeout_min=10)
        except SpaceError as e:
            raise ProviderError(f"trellis2-space failed: {e}")
        fds = list(find_filedata(res))
        if not fds:
            raise ProviderError(f"trellis2-space: no GLB in extract_glb result: {str(res)[:300]}")
        out = out_dir / "trellis2-space.glb"
        try:
            download_filedata(self.SPACE_HOST, fds[0], out)
        except SpaceError as e:
            raise ProviderError(f"trellis2-space download failed: {e}")
        if out.stat().st_size < 1024:
            raise ProviderError("trellis2-space: downloaded GLB suspiciously small")
        return GenerateResult(glb_path=out, provider="trellis2-space",
                              meta={"seed": seed, "resolution": resolution})
