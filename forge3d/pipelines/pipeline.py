"""Forge3D pipeline: concept -> multiview -> mesh -> cleanup -> quadremesh
-> texture -> densify -> rig -> export -> handoff.

Each stage is swappable; the orchestrator runs them in order and records
provenance (provider, config, timestamps) into out_dir/run.json.

Stage order rationale (2026-10-06 gap-closing):
- multiview BEFORE mesh: give the reconstruction stage real observations
  of backs/sides instead of hallucinations.
- quadremesh BEFORE texture: remeshing destroys UVs, so topology is fixed
  first and texturing happens on the final topology.
- quadremesh and densify are mutually exclusive: densify upsamples triangle
  count toward the Tripo vanity metric; quadremesh produces animation-ready
  quads at game counts. For game characters (the actual use case),
  quadremesh wins and densify is skipped.
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

    def __init__(self, provider: ModelProvider | None, out_dir: Path):
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
        if self.provider is not None:
            data["provider"] = self.provider.info.name
        manifest.write_text(json.dumps(data, indent=2))

    def run(self, *, prompt: str | None = None,
            image: Path | None = None,
            multiview: str | None = None,
            texture: str | None = "lanczos",
            densify: bool = True,
            quadremesh: bool = False,
            quad_target: int = 30000,
            rig: bool = False,
            gates: bool = True) -> PipelineResult:
        """Full run: mesh generation + all post stages."""
        if not prompt and not image:
            raise ProviderError("need --prompt and/or --image")
        if self.provider is None:
            raise ProviderError("Pipeline needs a provider for run()")
        ok, reason = self.provider.is_available()
        if not ok:
            raise ProviderError(f"provider unavailable: {reason}")

        self._record("concept", prompt or str(image))

        # multi-view synthesis BEFORE meshing (backs are observed, not hallucinated)
        views: list[Path] = []
        if multiview and image:
            from .multiview import generate_views
            try:
                views = generate_views(image, self.out_dir, backend=multiview)
                self._record("multiview", f"{multiview}: {len(views)} views")
            except ProviderError as e:
                self._record("multiview", f"skipped: {e}")

        result: GenerateResult = self.provider.generate(
            prompt=prompt, image=image, out_dir=self.out_dir,
            views=views or None)
        self._record("mesh", str(result.glb_path))
        return self.run_from_mesh(result, texture=texture, densify=densify,
                                  quadremesh=quadremesh, quad_target=quad_target,
                                  rig=rig, gates=gates)

    def run_from_mesh(self, result: GenerateResult, *,
                      texture: str | None = "lanczos",
                      densify: bool = True,
                      quadremesh: bool = False,
                      quad_target: int = 30000,
                      rig: bool = False,
                      gates: bool = True) -> PipelineResult:
        """Post stages on an already-generated mesh (fan-out winner path)."""
        self._record("mesh", str(result.glb_path))

        # cleanup/normalize stage hooks the ported postprocessor
        current = self.cleanup(result.glb_path)
        self._record("cleanup", str(current))

        # quad remesh BEFORE texture (remeshing destroys UVs; texture lands
        # on final topology). Mutually exclusive with densify.
        if quadremesh:
            from .quadremesh import quad_remesh_glb
            try:
                current = quad_remesh_glb(current, self.out_dir,
                                          target_faces=quad_target)
                self._record("quadremesh", str(current))
            except ProviderError as e:
                self._record("quadremesh", f"skipped: {e}")
        # geometry densification (tessellation toward the ~1.9M Tripo bar).
        # Skipped when quadremesh ran: upsampling clean quads back into
        # triangle soup would undo the remesh.
        elif densify:
            from .densify import densify_glb
            current = densify_glb(current, self.out_dir)
            self._record("densify", str(current))

        # texture refinement (attacks blurry-back weakness)
        if texture:
            from .texture import refine_textures
            try:
                current = refine_textures(current, self.out_dir, backend=texture)
                self._record("texture", f"{texture}: {current}")
            except ProviderError as e:
                # no embedded textures to refine: loud note, not a fake
                self._record("texture", f"skipped: {e}")
        # auto-rig (the beyond-Tripo edge: Tripo free output is unrigged)
        if rig:
            from .rig import rig_glb
            current = rig_glb(current, self.out_dir)
            self._record("rig", str(current))

        self._record("export", str(current))
        # quality gates: PASS ships, FLAG ships with warnings recorded,
        # FAIL raises loudly (fan-out retries next provider, or aborts)
        if gates:
            from .gates import run_gates, FAIL
            report = run_gates(current)
            self._record("gates", report.to_dict())
            if report.verdict == FAIL:
                raise ProviderError(
                    f"quality gates FAILED on {current}: " +
                    "; ".join(f"{r.name}: {r.detail}" for r in report.results
                              if r.verdict == FAIL))
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
