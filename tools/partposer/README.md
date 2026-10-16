# PartPoser

Interactive 3D part-positioning tool for character models. Move, rotate, and pose individual model parts with a Blender-style gizmo plus precision sliders.

## What it does
- Load any GLB model with separable parts
- Tap a part to select it, drag the gizmo arrows/rings to move/rotate directly
- 10 precision sliders: spread, shift, up/down, fwd/back, pitch, yaw, roll, individual nudges, scale
- Wing (mirrored) and Together move modes
- Presets for common poses
- Copy values to lock poses into render pipelines

## Built on
- Three.js TransformControls (industry-standard gizmo, same as Blender)
- Three.js OrbitControls
- GLTFLoader

## Usage
Open `partposer.html` in the widget. Models load from the repo via raw.githubusercontent.com (CORS-friendly).

To use with a different model: export the model as GLB with parts as separate objects, host on the repo, update the loader URL.
