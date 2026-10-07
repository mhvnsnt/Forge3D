"""TRELLIS.2 via official HuggingFace Space (microsoft/TRELLIS.2).

Keyless Gradio REST. WORKING state (verified 2026-10-07):
  /image_to_3d (stateless)   [WORK — returns turntable-preview HTML]
  /extract_glb (GLB export)   [BROKEN over REST]

Space: https://huggingface.co/spaces/microsoft/TRELLIS.2
License: MIT (microsoft/TRELLIS.2 code + weights) — commercial-safe.

WHY /extract_glb IS BROKEN (verified 2026-10-07):
  image_to_3d returns (output_buf: gr.State, preview_html). extract_glb
  takes that state dict as its first input. Over REST:
  - stateless: the gr.State comes back `null` in the complete payload, so
    /extract_glb has nothing to decode (`unpack_state(None)` fails);
  - session-pinned (session_hash in POST payload): the SSE stream returns
    `event: error` on /image_to_3d, and /extract_glb returns
    `event: error, data: "404: Not Found"` — the same session-state breakage
    seen on the TencentARC/InstantMesh space's Gradio version.

What generate() does: runs stateless /image_to_3d, saves the real preview
HTML (48 rendered views of the generated 3D model — genuine evidence the
3D inference ran), then raises ProviderError loudly at the /extract_glb
step. No fake GLB, ever.

NOTE 2026-10-07: ZeroGPU anonymous quota is ALSO a factor on this space
(official gradio_client: "exceeded your ZeroGPU quota (120s requested vs.
174s left). Try again in 4:54:25") — raw REST surfaces quota errors as
`event: error, data: null`, identical to the state failure mode, so the two
cannot be fully disentangled until quota resets. The gr.State=null
observation over stateless REST stands regardless.

For a WORKING keyless TRELLIS path use trellis1-space (trellis-community
space, single stateless /generate_and_extract_glb call -> GLB).
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
            # Stateless /image_to_3d — verified working 2026-10-07. Returns
            # (state=None over REST, preview HTML with 48 model renders).
            res = call_endpoint(self.SPACE_HOST, "/image_to_3d",
                                [fd, seed, resolution,
                                 7.5, 0.7, 12, 3.0,      # sparse-structure stage
                                 3.0, 0.7, 12, 3.0,      # shape stage
                                 3.0, 0.7, 12, 3.0],     # texture stage
                                timeout_min=timeout_min)
            for item in (res if isinstance(res, list) else [res]):
                if isinstance(item, str) and "<div" in item:
                    (out_dir / "trellis2-preview.html").write_text(item)
                    break
            # /extract_glb needs the gr.State dict, which is null over
            # stateless REST and 404s with session_hash (see docstring).
            try:
                call_endpoint(self.SPACE_HOST, "/extract_glb",
                              [decimation_target, texture_size],
                              timeout_min=10)
            except SpaceError as e:
                raise ProviderError(
                    "trellis2-space: /extract_glb is unusable over REST on "
                    "this space's Gradio version — the gr.State from "
                    "/image_to_3d comes back null stateless, and "
                    "session-pinned calls fail with SSE `error: 404: Not "
                    f"Found` ({e}). The 3D inference itself ran (preview "
                    f"HTML saved to {out_dir}); no GLB can be exported until "
                    "the space is fixed. Use trellis1-space for a working "
                    "keyless TRELLIS GLB path.")
        except (SpaceError, ProviderError):
            raise
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"trellis2-space failed: {e}")
        # Unreachable: /extract_glb always raises above.
        raise ProviderError(
            "trellis2-space: unexpected — /extract_glb returned without "
            "error; update this provider to download the GLB.")
