"""Forge3D pipeline: concept -> multiview -> mesh -> texture -> export -> handoff.

Each stage is swappable; the orchestrator runs them in order and records
provenance (provider, config, timestamps) into out_dir/run.json.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..providers.base import GenerateResult, ModelProvider, ProviderError


@dataclass
class PipelineResult:
    glb_path: Path
    run_manifest: Path
    stages: list[str] = field(default_factory=list)


class Pipeline:
    """Single-provider pipeline: concept image -> provider -> cleanup -> export."""

    def __init__(self, provider: ModelProvider, out_dir: Path):
        self.provider = provider
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._stages: list[str] = []

    def _record(self, stage: str, detail: str = "") -> None:
        self._stages.append(stage)
        manifest = self.out_dir / "run.json"
        data = {}
        if manifest.exists():
            data = json.loads(manifest.read_text())
        data.setdefault("stages", []).append(
            {"stage": stage, "detail": detail, "ts": time.time()})
        data["provider"] = self.provider.info.name
        manifest.write_text(json.dumps(data, indent=2))

    def run(self, *, prompt: str | None = None,
            image: Path | None = None,
            texture: str | None = "lanczos",
            densify: bool = True,
            rig: bool = False) -> PipelineResult:
        if not prompt and not image:
            raise ProviderError("need --prompt and/or --image")
        ok, reason = self.provider.is_available()
        if not ok:
            raise ProviderError(f"provider unavailable: {reason}")

        self._record("concept", prompt or str(image))
        result: GenerateResult = self.provider.generate(
            prompt=prompt, image=image, out_dir=self.out_dir)
        self._record("mesh", str(result.glb_path))

        # cleanup/normalize stage hooks the ported postprocessor
        cleaned = self.cleanup(result.glb_path)
        self._record("cleanup", str(cleaned))

        current = cleaned
        # texture refinement (attacks blurry-back weakness)
        if texture:
            from .texture import refine_textures
            try:
                current = refine_textures(current, self.out_dir, backend=texture)
                self._record("texture", f"{texture}: {current}")
            except ProviderError as e:
                # no embedded textures to refine: loud note, not a fake
                self._record("texture", f"skipped: {e}")
        # geometry densification (tessellation toward the ~1.9M Tripo bar)
        if densify:
            from .densify import densify_glb
            current = densify_glb(current, self.out_dir)
            self._record("densify", str(current))
        # auto-rig (the beyond-Tripo edge: Tripo free output is unrigged)
        if rig:
            from .rig import rig_glb
            current = rig_glb(current, self.out_dir)
            self._record("rig", str(current))

        self._record("export", str(current))
        self._record("handoff",
                     "ready for retarget/rig tooling (Bannon/AshLanev2 generative)")
        return PipelineResult(glb_path=current,
                              run_manifest=self.out_dir / "run.json",
                              stages=list(self._stages))

    def cleanup(self, glb: Path) -> Path:
        """Mesh normalize pass. Ported postprocessor plugs in here (see pipelines/postprocess.py)."""
        try:
            from .postprocess import normalize_glb
            return normalize_glb(glb, self.out_dir)
        except ImportError:
            return glb  # postprocessor optional until ported
