"""InstantMesh via official HuggingFace Space (TencentARC/InstantMesh).

Keyless Gradio REST, chained with a session_hash:
  /preprocess (bg removal) -> /generate_mvs (multiview) -> /make3d (GLB+OBJ).
Runs on HF's free GPU — no local GPU needed. Apache-2.0 licensed.

Space: https://huggingface.co/spaces/TencentARC/InstantMesh
Fast (~10s on GPU) but lower fidelity than TRELLIS.2 — good for quick
iterations and props; TRELLIS.2-space is the quality anchor.
"""
from __future__ import annotations

import uuid
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
        license="Apache-2.0 (TencentARC/InstantMesh); Space terms apply",
        commercial_ok=True,
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

    def generate(self, *, prompt=None, image: Path | None = None,
                 out_dir: Path, sample_steps: int = 75, sample_seed: int = 42,
                 remove_bg: bool = True, timeout_min: int = 20,
                 **kwargs) -> GenerateResult:
        if image is None or not Path(image).exists():
            raise ProviderError("instantmesh-space needs --image <file>")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        session = uuid.uuid4().hex[:12]
        try:
            server_path = upload_file(self.SPACE_HOST, Path(image))
            fd = file_data(server_path, Path(image).name)

            def call(ep: str, data: list, tmin: int = 10):
                # session-pinned call (stateful chain: preprocess->mvs->make3d)
                import json, time, urllib.request
                url = f"https://{self.SPACE_HOST}/gradio_api/call/{ep.lstrip('/')}"
                payload = json.dumps({"data": data, "session_hash": session}).encode()
                req = urllib.request.Request(
                    url, data=payload, headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        event_id = json.loads(r.read())["event_id"]
                except Exception as e:  # noqa: BLE001
                    raise SpaceError(f"/{ep} submit failed: {e}")
                surl = (f"https://{self.SPACE_HOST}/gradio_api/call/"
                        f"{ep.lstrip('/')}/{event_id}")
                deadline = time.time() + tmin * 60
                sreq = urllib.request.Request(surl, headers={"Accept": "text/event-stream"})
                try:
                    resp = urllib.request.urlopen(sreq, timeout=30)
                except Exception as e:  # noqa: BLE001
                    raise SpaceError(f"/{ep} SSE connect failed: {e}")
                buf = ""
                try:
                    while time.time() < deadline:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        buf += chunk.decode("utf-8", "replace")
                        while "\n\n" in buf:
                            block, buf = buf.split("\n\n", 1)
                            et, pl = None, None
                            for line in block.splitlines():
                                if line.startswith("event:"):
                                    et = line[6:].strip()
                                elif line.startswith("data:"):
                                    pl = line[5:].strip()
                            if et == "complete" and pl:
                                return json.loads(pl)
                            if et == "error" and pl:
                                raise SpaceError(f"/{ep} error: {pl[:300]}")
                finally:
                    resp.close()
                raise SpaceError(f"/{ep} timed out after {tmin} min")

            call("/preprocess", [fd, remove_bg], tmin=5)
            call("/generate_mvs", [fd, sample_steps, sample_seed], tmin=10)
            res = call("/make3d", [], tmin=10)
        except SpaceError as e:
            raise ProviderError(f"instantmesh-space failed: {e}")
        fds = list(find_filedata(res))
        if not fds:
            raise ProviderError(f"instantmesh-space: no model in /make3d result: {str(res)[:300]}")
        # prefer GLB over OBJ
        pick = next((f for f in fds
                     if (f.get("path") or "").endswith(".glb")
                     or "glb" in (f.get("url") or "")), fds[0])
        out = out_dir / "instantmesh-space.glb"
        try:
            download_filedata(self.SPACE_HOST, pick, out)
        except SpaceError as e:
            raise ProviderError(f"instantmesh-space download failed: {e}")
        if out.stat().st_size < 1024:
            raise ProviderError("instantmesh-space: downloaded model suspiciously small")
        return GenerateResult(glb_path=out, provider="instantmesh-space",
                              meta={"seed": sample_seed, "steps": sample_steps})
