# FREE_RUNNER_GUIDE.md — run Forge3D at $0

## This VM (CPU-only)
- `python3 -m forge3d selftest` — always works.
- `generate` with local providers: TripoSR CAN run on CPU (2–10 min/image) once
  torch + the vendored repo are installed. Slow but real.
- Free APIs (Meshy, Tripo3D, HF Inference) work fine from CPU — the heavy lifting
  is server-side. This is the fastest $0 path on this box.

## Free GPU runners (for TRELLIS / Hunyuan3D-class models)
1. **Kaggle** — free GPU ~30h/week (verify current quota; needs his account).
   Setup: notebook, `pip install -r requirements-local.txt`, clone Forge3D,
   vendor model repos into `forge3d/providers/_vendor/`.
2. **Google Colab** — free tier GPU with time limits; same setup.
3. **Hugging Face Spaces (ZeroGPU)** — free serverless GPU; good for demos, not
   long batch runs.
4. **Lightning AI** — free tier GPU hours.

Owner has standing API-sweep + account-creation authorization; GPU-runner
accounts (Kaggle/Colab) are queued under that permission — no manual homework
for him.

## API keys
Never in the repo. `export FORGE3D_MESHY_KEY=...` etc. Keys live in the Secure
Vault; the provider reads env vars only.
