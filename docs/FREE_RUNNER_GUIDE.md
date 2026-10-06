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

## Weight downloads behind a throttled proxy (learned 2026-10-06)
`huggingface_hub`'s Xet client can stall at 0 B/s behind some egress proxies
even when plain HTTPS works. The xet-bridge CDN URL itself is fine — follow
the `/resolve/` redirect with plain curl and download directly:

```bash
mkdir -p ~/.forge3d/weights/triposr
curl -sL --retry 3 -o ~/.forge3d/weights/triposr/model.ckpt \
  "https://huggingface.co/stabilityai/TripoSR/resolve/main/model.ckpt"
```

The TripoSR provider prefers `~/.forge3d/weights/triposr/` (env
`FORGE3D_TRIPOSR_WEIGHTS` to override) and only hits HF when the local dir is
missing. Also: this VM's `no_proxy` contains bracketed IPv6 (`[::1]`) that
crashes some HTTP clients with `Invalid port: ':1]'` — the provider strips
IPv6 literals from `no_proxy` at runtime (proxy itself still used).
