"""TRELLIS v1 via community HuggingFace Space (trellis-community/TRELLIS).

Keyless Gradio REST, SINGLE stateless call:
  /generate_and_extract_glb(image, multiimages, seed, ss_*, slat_*,
                            multiimage_algo, mesh_simplify, texture_size)
    -> (info dict, turntable video, GLB, GLB download)
Runs on HF's free GPU — no local GPU needed. Microsoft TRELLIS weights
are MIT-licensed (code + weights), so outputs are commercial-safe.

Space: https://huggingface.co/spaces/trellis-community/TRELLIS

Unlike the official TencentARC/InstantMesh and microsoft/TRELLIS.2 spaces
(which need session-pinned gr.State chaining that is broken over REST on
their Gradio versions — see instantmesh_space.py / trellis2_space.py),
this space takes every input explicitly and returns the GLB in one call,
so it works fully stateless.

LIVE-TEST STATUS 2026-10-07: endpoint schema verified (/gradio_api/info +
upstream app.py); stateless endpoints on this space work
(/preprocess_image, /get_seed return complete). The /generate_and_extract_glb
GPU run itself is QUOTA-BLOCKED for anonymous users right now — the official
gradio_client reports: "You have exceeded your ZeroGPU quota (120s requested
vs. 44s left). Try again in 22:17:58." (reset ~22h). Raw REST surfaces this
as SSE `event: error, data: null` (message lost). generate() raises that
loudly; re-run after the quota reset to complete the end-to-end GLB proof.
"""
from __future__ import annotations

from pathlib import Path

from .hf_space import (SpaceError, call_endpoint, download_filedata,
                       file_data, find_filedata, upload_file)

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class Trellis1SpaceProvider(ModelProvider):
    info = ProviderInfo(
        name="trellis1-space",
        kind="api",
        capabilities=[Capability.IMAGE_TO_3D],
        license="MIT (microsoft/TRELLIS code + weights); Space terms apply",
        commercial_ok=True,
        needs_gpu=False,   # GPU lives on HF's side
        needs_key=False,   # keyless
        quota_note="free; HF Spaces queue/rate limits apply (ZeroGPU fair use)",
    )

    SPACE_HOST = "trellis-community-trellis.hf.space"

    def is_available(self) -> tuple[bool, str]:
        # light check: space serves its API info (no generation, no key)
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://{self.SPACE_HOST}/gradio_api/info",
                headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                info = r.read(128)
            if b"generate_and_extract_glb" in info or r.status == 200:
                return True, "space reachable (keyless)"
            return False, "space API info unexpected"
        except Exception as e:  # noqa: BLE001
            return False, f"space unreachable: {e}"

    def generate(self, *, prompt=None, image: Path | None = None,
                 out_dir: Path, seed: int = 0,
                 ss_guidance_strength: float = 7.5,
                 ss_sampling_steps: int = 12,
                 slat_guidance_strength: float = 3.0,
                 slat_sampling_steps: int = 12,
                 multiimage_algo: str = "multidiffusion",
                 mesh_simplify: float = 0.95,
                 texture_size: int = 1024,
                 timeout_min: int = 30, **kwargs) -> GenerateResult:
        if image is None or not Path(image).exists():
            raise ProviderError("trellis1-space needs --image <file>")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            server_path = upload_file(self.SPACE_HOST, Path(image))
            fd = file_data(server_path, Path(image).name)
            res = call_endpoint(
                self.SPACE_HOST, "/generate_and_extract_glb",
                [fd, [], seed,
                 ss_guidance_strength, ss_sampling_steps,
                 slat_guidance_strength, slat_sampling_steps,
                 multiimage_algo, mesh_simplify, texture_size],
                timeout_min=timeout_min)
        except SpaceError as e:
            raise ProviderError(f"trellis1-space failed: {e}")
        fds = list(find_filedata(res))
        glb_candidates = [f for f in fds
                          if (f.get("path") or "").endswith(".glb")
                          or "glb" in (f.get("url") or "")]
        if not glb_candidates:
            raise ProviderError(
                "trellis1-space: no GLB in generate_and_extract_glb result: "
                f"{str(res)[:300]}")
        out = out_dir / "trellis1-space.glb"
        try:
            download_filedata(self.SPACE_HOST, glb_candidates[0], out)
        except SpaceError as e:
            raise ProviderError(f"trellis1-space download failed: {e}")
        if out.stat().st_size < 1024:
            raise ProviderError("trellis1-space: downloaded GLB suspiciously small")
        # keep the turntable video too if present (proof artifact)
        video_paths = []
        for f in fds:
            p = (f.get("path") or "")
            if p.endswith((".mp4", ".webm")):
                dest = out_dir / "trellis1-space-turntable.mp4"
                try:
                    download_filedata(self.SPACE_HOST, f, dest)
                    video_paths.append(dest)
                except SpaceError:
                    pass
                break
        return GenerateResult(
            glb_path=out, provider="trellis1-space",
            meta={"seed": seed, "mesh_simplify": mesh_simplify,
                  "texture_size": texture_size, "video": str(video_paths[0]) if video_paths else ""})
