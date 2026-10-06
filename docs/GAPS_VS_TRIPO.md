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
