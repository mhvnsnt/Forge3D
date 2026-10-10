# Infra Resilience Tools

Copied from `~/workspace/3d-toolkit/infra/`. These solve the fragility that kept
breaking Blender renders:

- **`egl-restore.sh`** — Restores the EGL stack after daemon restarts wipe it.
  Run with sudo. Also runs automatically on boot via systemd
  (`blender-egl-restore.service`).
- **`monitoring/safe-watcher.py`** — Monitor-ONLY process watcher. NEVER kills,
  deletes, or restarts anything — it only writes alerts.
- **xvfb-run** — All Blender invocations in this repo now use
  `xvfb-run -a blender` instead of bare `blender`, so renders survive EGL breakage.

See `~/workspace/3d-toolkit/infra/INFRA.md` for the full wire-up guide.
