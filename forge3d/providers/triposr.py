"""TripoSR local provider (Stability AI, MIT license).

Fast single-image -> textured mesh. Runs on GPU; CPU fallback works
(~45s/mesh on a 2-core VM per May-2026 test). Model weights downloaded on
first use from the official repo (stabilityai/TripoSR).

Adapted from AshLanev2 tools/generative/3d/triposr_generate.py
(see docs/PROVENANCE.md): mc_resolution 128-256, optional bg removal.
"""
from __future__ import annotations

from pathlib import Path

from .base import (Capability, GenerateResult, ModelProvider, ProviderError,
                   ProviderInfo)


class TripoSRProvider(ModelProvider):
    info = ProviderInfo(
        name="triposr",
        kind="local",
        capabilities=[Capability.IMAGE_TO_3D],
        license="MIT",
        commercial_ok=True,
        needs_gpu=True,  # works on CPU (~45s), just slow
        needs_key=False,
        quota_note="unlimited (your hardware)",
    )

    VENDOR = Path(__file__).parent / "_vendor" / "triposr"
    # Local weights staged by an earlier Forge3D session; avoids re-downloading
    # (and the HF Xet stall) on every run. Override with FORGE3D_TRIPOSR_WEIGHTS.
    WEIGHTS_ENV = "FORGE3D_TRIPOSR_WEIGHTS"
    WEIGHTS_DEFAULT = Path.home() / ".forge3d" / "weights" / "triposr"
    SHIM = Path(__file__).parent / "_vendor"  # torchmcubes CPU shim lives here

    def _ensure_path(self):
        import sys
        for p in (str(self.VENDOR), str(self.SHIM)):
            if p not in sys.path:
                sys.path.insert(0, p)

    @staticmethod
    def _sanitize_proxy_env():
        """Drop IPv6 literals from no_proxy.

        This VM's no_proxy contains bare '::1' AND bracketed '[::1]'.
        requests/curl tolerate them, but this httpx version crashes parsing
        either ("Invalid port: ':1]'"). IPv6 no_proxy entries are irrelevant
        here (egress is IPv4 proxy). Sanitizing is env-hygiene, not a bypass:
        the egress proxy itself is still used.
        """
        import os
        for var in ("no_proxy", "NO_PROXY"):
            val = os.environ.get(var, "")
            if not val:
                continue
            parts = [p for p in val.split(",") if "::" not in p]
            os.environ[var] = ",".join(parts)

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # noqa
        except ImportError:
            return False, "torch not installed (pip install -r requirements-local.txt)"
        if not (self.VENDOR / "run.py").exists():
            return False, "TripoSR repo not vendored (see docs/FREE_RUNNER_GUIDE.md)"
        # deep check: the imports generate() actually needs (incl. the
        # torchmcubes CPU shim) — a shallow check lied once already
        self._ensure_path()
        try:
            from tsr.system import TSR  # noqa
            from tsr.utils import remove_background  # noqa
            import torchmcubes  # noqa  (vendored CPU shim)
        except Exception as e:  # noqa: BLE001
            return False, f"TripoSR deps incomplete: {e}"
        return True, "ok"

    def generate(self, *, prompt=None, image=None, out_dir: Path,
                 mc_resolution: int = 256, remove_bg: bool = True,
                 foreground_ratio: float = 0.85,
                 **kwargs) -> GenerateResult:
        if image is None:
            raise ProviderError("triposr needs --image (image-to-3D only)")
        ok, reason = self.is_available()
        if not ok:
            raise ProviderError(reason)

        import sys
        sys.path.insert(0, str(self.VENDOR))
        sys.path.insert(0, str(self.SHIM))  # torchmcubes CPU shim
        try:
            import torch
            from PIL import Image
            from tsr.system import TSR
            from tsr.utils import remove_background, resize_foreground
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"TripoSR imports failed: {e}")

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        try:
            self._sanitize_proxy_env()  # httpx vs no_proxy quirk (see above)
            import os
            local = Path(os.environ.get(self.WEIGHTS_ENV, self.WEIGHTS_DEFAULT))
            if (local / "config.yaml").is_file() and (local / "model.ckpt").is_file():
                src = str(local)  # local dir wins: no HF download at all
                # Memory-efficient load for small VMs: mmap (no RAM dup) +
                # bfloat16 halves the 1.68GB fp32 checkpoint (CPU-native, norm-safe). Chunked state-dict
                # load keeps peak ~1.3GB instead of ~3.4GB.
                from omegaconf import OmegaConf
                _cfg = OmegaConf.load(str(local / "config.yaml"))
                OmegaConf.resolve(_cfg)
                _use_fp16 = os.environ.get("FORGE3D_TRIPOSR_BF16", "1") == "1" and device == "cpu"
                if _use_fp16:
                    # construct directly in bf16 (840MB) instead of fp32 (1.94GB)
                    torch.set_default_dtype(torch.bfloat16)
                model = TSR(_cfg)
                if _use_fp16:
                    torch.set_default_dtype(torch.float32)
                _ckpt = torch.load(str(local / "model.ckpt"), map_location="cpu",
                                   mmap=True, weights_only=False)
                _keys = list(_ckpt.keys())
                _mid = len(_keys) // 2
                for _chunk in (_keys[:_mid], _keys[_mid:]):
                    _part = {k: (_ckpt[k].to(torch.bfloat16) if _use_fp16 else _ckpt[k])
                             for k in _chunk}
                    model.load_state_dict(_part, strict=False)
                    del _part
                del _ckpt
            else:
                src = "stabilityai/TripoSR"
                model = TSR.from_pretrained(
                    src,
                    config_name="config.yaml",
                    weight_name="model.ckpt",
                )
            model.renderer.set_chunk_size(8192)
            model.to(device)
            # CPU dtype unification (2026-10-07): the bf16 fast path can leave
            # mixed dtypes (norms/buffers stay fp32) -> "mixed dtype (CPU)"
            # at inference. Force the whole model to one dtype.
            if device == "cpu":
                try:
                    _tgt = torch.bfloat16 if _use_fp16 else torch.float32
                except NameError:
                    _tgt = torch.float32
                model = model.to(_tgt)

            pil = Image.open(image)
            if remove_bg:
                from rembg import new_session
                # pin u2net: rembg 2.x defaults to the 1GB bria-rmbg model
                _sess = new_session("u2net")
                pil = remove_background(pil, rembg_session=_sess)
            pil = resize_foreground(pil, foreground_ratio)
            if pil.mode == "RGBA":
                bg = Image.new("RGB", pil.size, (255, 255, 255))
                bg.paste(pil, mask=pil.split()[3])
                pil = bg
            else:
                pil = pil.convert("RGB")

            with torch.no_grad():
                scene_codes = model([pil], device=device)
            # has_vertex_color=True: triplane-queried RGB per vertex.
            # (Upstream run.py passes `not args.bake_texture` positionally;
            # we always take vertex colors — texture baking is a later stage.)
            meshes = model.extract_mesh(scene_codes, True,
                                        resolution=mc_resolution)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"TripoSR inference failed: {e}")

        out = Path(out_dir) / f"triposr-{Path(image).stem}.glb"
        try:
            meshes[0].export(out)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"TripoSR mesh export failed: {e}")
        if not out.exists() or out.stat().st_size < 1000:
            raise ProviderError("TripoSR produced no usable mesh")
        return GenerateResult(
            glb_path=out, provider="triposr",
            meta={"device": device, "mc_resolution": mc_resolution,
                  "remove_bg": remove_bg})
