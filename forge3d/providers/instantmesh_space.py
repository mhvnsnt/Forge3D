"""InstantMesh via official HuggingFace Space (TencentARC/InstantMesh).

Keyless Gradio REST. WORKING state (verified 2026-10-07):
  /preprocess (bg removal) -> /generate_mvs (multiview)   [stateless: WORK]
  /make3d (GLB+OBJ)                                       [BROKEN over REST]

Space: https://huggingface.co/spaces/TencentARC/InstantMesh
License: Apache-2.0 (TencentARC/InstantMesh code + weights).
NOTE: the Zero123++ multiview stage inside InstantMesh ships weights under
CC-BY-NC 4.0 (non-commercial) per upstream research — see LICENSES.md.

WHY /make3d IS BROKEN (proven three independent ways 2026-10-07):
  The space chains preprocess -> generate_mvs -> make3d through gr.State
  (mv_images). Over REST that requires a session-pinned call chain, but this
  space's Gradio version breaks every session-pinned call:
  1. hand-rolled REST with "session_hash" in the POST payload: submit 200,
     then the SSE stream returns `event: error, data: "404: Not Found"`.
     The identical call WITHOUT session_hash completes fine.
  2. official gradio_client (sends session_hash): AppError on /preprocess.
  3. stateless /make3d (no session): `event: error, data: null` — there is
     no state for it to read, and the named endpoint declares 0 params so a
     reconstructed input cannot be passed either (tested: extra `data` items
     are ignored -> same error).
  All community InstantMesh space copies are paused (HTTP 503), so there is
  no alternate host. /make3d is therefore documented UNUSABLE until the
  space upgrades Gradio or exposes a stateless single-call endpoint.

What generate() does: runs the two working stateless stages and saves the
real artifacts (bg-removed image + 6-view grid — directly usable by the
Forge3D MULTIVIEW stage), then raises ProviderError loudly at the /make3d
step with this explanation. No fake GLB, ever.
"""
from __future__ import annotations

from pathlib import Path


from .hf_space import (SpaceError, call_endpoint, download_filedata,  # noqa: E402
                      file_data, find_filedata, upload_file)

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,  # noqa: E402
                   ProviderInfo)


class InstantMeshSpaceProvider(ModelProvider):
    info = ProviderInfo(
        name="instantmesh-space",
        kind="api",
        capabilities=[Capability.IMAGE_TO_3D, Capability.MULTIVIEW],
        license="Apache-2.0 (TencentARC/InstantMesh); Space terms apply; "
                "Zero123++ stage weights CC-BY-NC 4.0 — see LICENSES.md",
        commercial_ok=False,  # Zero123++ weights are CC-BY-NC; see LICENSES.md
        needs_gpu=False,
        needs_key=False,
        quota_note="free; HF Spaces queue/rate limits apply",
    )

    SPACE_HOST = "tencentarc-instantmesh.hf.space"

    def is_available(self) -> tuple[bool, str]:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"https://{self.SPACE_HOST}/gradio_api/info",
                headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                info = r.read(64)
            if b"make3d" in info or r.status == 200:
                return True, "space reachable (keyless)"
            return False, "space API info unexpected"
        except Exception as e:  # noqa: BLE001
            return False, f"space unreachable: {e}"

    def _stateless_stage(self, endpoint: str, data: list,
                         tmin: int) -> list:
        try:
            return call_endpoint(self.SPACE_HOST, endpoint, data,
                                 timeout_min=tmin)
        except SpaceError as e:
            raise ProviderError(f"instantmesh-space {endpoint} failed: {e}")

    def generate(self, *, prompt=None, image: Path | None = None,
                 out_dir: Path, sample_steps: int = 75, sample_seed: int = 42,
                 remove_bg: bool = True, **kwargs) -> GenerateResult:
        if image is None or not Path(image).exists():
            raise ProviderError("instantmesh-space needs --image <file>")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            server_path = upload_file(self.SPACE_HOST, Path(image))
            fd = file_data(server_path, Path(image).name)

            # Stage 1+2 (stateless — verified working 2026-10-07).
            pre = self._stateless_stage("/preprocess", [fd, remove_bg], tmin=5)
            pre_fds = list(find_filedata(pre))
            if pre_fds:
                download_filedata(self.SPACE_HOST, pre_fds[0],
                                  out_dir / "instantmesh-preprocessed.png")
            mvs = self._stateless_stage(
                "/generate_mvs", [fd, sample_steps, sample_seed], tmin=12)
            mvs_fds = list(find_filedata(mvs))
            if mvs_fds:
                download_filedata(self.SPACE_HOST, mvs_fds[-1],
                                  out_dir / "instantmesh-multiview.png")

            # Stage 3: /make3d needs session-pinned gr.State, which this
            # space's Gradio version breaks over REST (see module docstring).
            try:
                call_endpoint(self.SPACE_HOST, "/make3d", [], timeout_min=10)
            except SpaceError as e:
                raise ProviderError(
                    "instantmesh-space: /make3d is unusable over REST on this "
                    "space's Gradio version — every session-pinned call fails "
                    "with SSE `error: 404: Not Found`, and stateless /make3d "
                    f"has no state to read ({e}). Multiview artifacts were "
                    f"saved to {out_dir} (usable by the MULTIVIEW stage); no "
                    "GLB can be produced until the space is fixed.")
        except (SpaceError, ProviderError):
            raise
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"instantmesh-space failed: {e}")
        # Unreachable: /make3d always raises above. Kept explicit so a future
        # space fix lands here instead of silently changing behavior.
        raise ProviderError(
            "instantmesh-space: unexpected — /make3d returned without error; "
            "update this provider to download the GLB.")
