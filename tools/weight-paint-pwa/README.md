# Forge3D Weight Paint PWA

Mobile-first web tool for hand-painting skin weights on Forge3D's generated
characters. Same verified build already shipped to Bannon, AshLanev2,
ConcreteDragon, Brutal-Fist, AshLane-prototype, and URBAN-MAYHEM — now wired
to the statue factory.

## Use (on phone)

1. Open the link. The default model loads from this repo:
   `docs/stage-evidence/grunt-batch/grunt_onyx.glb` (the grunt batch's hero
   output, the roster-candidate statue).
2. Pick a bone (shoulders/arms pinned at top). Heat view: red = full weight, blue = none.
3. Drag on the model to paint. Add/Remove, radius, strength controls.
4. Drag the **Angle** slider (0–90°) to pose-test the arm raise live. Fix what tears.
5. **Export GLB** → send the file back to the pipeline.

**Note:** Forge3D's generated statues ship **unrigged** — rigging happens
downstream (Bannon's `tools/statue-to-game/` pipeline: rig → skin → probe →
paint-flag → animate). This tool shines on the **rigged** output: load a rigged
GLB via `?model=<url>` (or the 📁 upload button), then paint. On an unrigged
statue the tool still loads and previews; guided mode reports "unavailable"
until a skinned model is loaded.

## Send-back loop

1. Export downloads `FORGE3D_painted.glb` with new weights baked in.
2. Hand the file to the pipeline (chat attach or repo).
3. Pipeline runs the statue-to-game verifier
   (`tools/statue-to-game/verify_character.py`) — renders the painted weights
   at 15/30/45/60/90° to prove zero webbing.
4. Clean → lands as the new model via PR. Not clean → probe frames come back
   showing where it still tears.

## Tech

Single `index.html`, Three.js r160 (vendored in `lib/`), ES modules + importmap.
No build step. Painting edits `skinIndex`/`skinWeight` in place (bind pose),
renormalizes to sum 1.0, GLTFExporter writes the result.

## Guided fix mode (for first-timers)

Tap **🧭 Start guided fix**. It walks you through in plain language:

1. Drag the **Angle** slider up (try 45°) until the shoulder looks stretched.
2. Tap **🔍 Find bad spots** — the tool scans the shoulder region, finds verts
   that move differently from their neighbors (the tear signature), and makes
   them pulse. It auto-selects the right bone (usually the shoulder).
3. Paint the glowing spots. They turn red as you fix them.
4. Tap **🔍 Check again** — if the glow is gone, you fixed it. Export the GLB.

Detection: per-vertex displacement (posed vs rest, via CPU skinning) restricted
to a 0.38-unit radius around the shoulder joints; flags verts exceeding
mean + 2.5σ of neighbor-displacement variance. Headless test: `?autotest=1&model=<url>`.

## Self-test (2026-10-09, headless Chromium + SwiftShader, localhost)

Run on the Bannon build of this same code (all deploys are the identical build):

- Load: 12,633 verts / 58 bones, renders correct heat view.
- Paint: real pointer stroke changed 558 verts (max delta 0.82) on LeftArm.
- Pose: slider drives `LeftArm.rotation.x` to −1.047 rad at 60°, visually confirmed.
- Export: GLB re-parsed — 32,348 weight components differ, all vert weight sums = 1.0.
