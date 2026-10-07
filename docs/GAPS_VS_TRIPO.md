# GAPS_VS_TRIPO.md — honest gap list (owner law: no hype)

Where Forge3D's free pipeline stands vs Tripo3D, and what closes each gap.

## Known gaps

1. **Topology / rig-readiness.** Tripo3D outputs relatively clean, quad-ish meshes.
   Open image-to-3D models (TripoSR, TRELLIS, InstantMesh) output dense triangle
   soups that need cleanup + retopology before rigging. *Closer:* our cleanup
   stage + existing Bannon/AshLanev2 retarget + mesh-repair tooling; quad
   remeshing (open-source) is the missing piece to research.
2. **Texture quality.** Tripo3D bakes crisp PBR textures. Local free models are
   weakest here — blurry backs/sides, baked-in lighting. *Closer:* Hunyuan3D-Paint
   texture stage, multi-view-consistent texturing, texture upscalers.
3. **Anatomy.** Single-image reconstruction hallucinates occluded parts (backs,
   hands). *Closer:* multi-view stage (Zero123++ / provider-native views) with
   character-specific view prompts; owner eyes-on iteration loop.
4. **Speed.** Tripo3D cloud: seconds–minutes. Local TripoSR on CPU: 2–10 min;
   TRELLIS/Hunyuan need a GPU. *Closer:* free GPU runners (Kaggle/Colab/HF Spaces)
   — see FREE_RUNNER_GUIDE.md.
5. **Text-to-3D direct.** Best free path is text→concept image→image-to-3D, not
   native text-to-3D (Shap-E/Point-E quality lags badly). The concept-image
   quality caps everything downstream.

## What "beats Tripo" means here
Not beating it on raw cloud speed — beating it on **owner-judged character
quality at $0**, with full pipeline ownership (no per-model fees, no vendor
lock-in). The eyes-on loop ("that sucked" / "that was good") is the training
signal no API gives us.

## Gap-closing round (2026-10-07) — owner: "solve the blocks before I send the image"
- **Backs (GAP 1):** multi-view synthesis stage wired (`pipelines/multiview.py`,
  `--multiview` flag). Zero123++ via public HF Space, single image → 6-view
  grid → split views, fed to mesh providers that accept them. License reality:
  Zero123++ is CC-BY-NC 4.0 — research-only, NEVER in the commercial auto path.
  All public Zero123++ Spaces were paused as of 2026-10-07; the backend retries
  with backoff then fails loudly. Commercial-safe explicit multi-view synthesis
  does not exist in open-source (every generative NVS model is research-licensed);
  the money path stays provider-native internal multiview (TRELLIS.2/InstantMesh,
  MIT/Apache) + fan-out multi-seed + owner eyes-on.
- **Topology (GAP 2):** quad-remesh stage wired (`pipelines/quadremesh.py`,
  `--quadremesh` flag, default target 30k quads). Headless Blender 4.2
  Quadriflow: triangle soup → animation-ready quad-dominant mesh, UVs
  smart-projected, original texture baked best-effort (loud on skip). Runs
  INSTEAD of densify (upsampling clean quads back to soup would undo it).
  No new license burden (Blender tool-use, already a dependency). Instant
  Meshes evaluated and rejected: BSD-3-Clause but interactive-GUI-only, no
  CLI for headless pipelines.
- **Latency (GAP 3):** two mitigations, both wired. (1) Parallel fan-out
  (`--fanout N`): race N providers simultaneously on the mesh stage, first
  good mesh wins, losers cancelled — worst case drops from sum-of-queues to
  max-of-queues. (2) Latency learning (`pipelines/latency.py`): every attempt
  recorded to `~/.forge3d/latency.json`, auto order tries historically-fastest
  first. Honest floor: without paid compute, latency = fastest free queue
  available (observed 2–15 min on HF Spaces). This finds that floor; it
  doesn't lower it.
- **Remaining honest gaps:** Pixal3D not yet wired; texture backs still the
  weakest link on local runs; quad-remesh texture bake is best-effort
  (8-sample CPU Cycles — good enough for game characters, not hero assets).
