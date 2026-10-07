# FREE_RUNNER_GUIDE.md — run Forge3D at $0

## This VM (CPU-only)
- `python3 -m forge3d selftest` — always works.
- `generate` with local providers: TripoSR CAN run on CPU (2–10 min/image) once
  torch + the vendored repo are installed. Slow but real.
- Free APIs (Meshy, Tripo3D, HF Inference) work fine from CPU — the heavy lifting
  is server-side. This is the fastest $0 path on this box.

## RAM hardening (learned 2026-10-07)
TripoSR inference needs ~2.5GB sustained RAM; this VM's free RAM swings
0.8–5GB as parallel agents come and go. Without protection that's OOM roulette.
What we did (all open-source, all in-repo):
- **`--wait-for-ram`** (`forge3d generate --image X --wait-for-ram`): waits until
  `--min-ram-gb` (default 2.5) GB is free, then takes a single-flight file lock
  (`~/.forge3d/inference.lock`) so two local runs never OOM each other.
  `--ram-timeout` (default 1800s) bounds the wait. Implementation:
  `forge3d/tools/ram_gate.py`.
- **Thread caps**: `FORGE3D_TRIPOSR_THREADS=1` (default) + `torch.set_num_threads(1)`
  bounds allocator arenas; `FORGE3D_TRIPOSR_CHUNK` (default 8192) sizes the
  triplane query chunks in `extract_mesh`.
- **Swap**: NOT available — `swapon` fails with "Operation not permitted"
  (container lacks the capability). Don't bother retrying.
- **Persistent venv** at `~/workspace/forge3d-venv/` (torch CPU + deps) survives
  VM restarts, unlike `/usr/local`.

### Disk footprint (measured 2026-10-07)
| Path | Size | Notes |
|---|---|---|
| `~/workspace/forge3d-venv/` | 1.7GB | torch CPU + TripoSR deps; keep |
| `~/.forge3d/weights/triposr/` | 2.4GB | model.ckpt (1.56GB fp32) + model.bf16.safetensors (838MB) + config; keep |
| `~/.cache/pip` | 721MB | safe to `pip cache purge` (done 2026-10-07) |
| `~/.cache/ms-playwright` | 1.6GB | browser automation — used by other agents, do NOT delete |
| `~/.cache/puppeteer` | 656MB | same — do NOT delete |
| `/usr/local/lib/python3.12/dist-packages` | 1.3GB | system python — leave alone |

### Evaluated but not pursued (2026-10-07)
- **ONNX export** (optimum/onnxruntime): code-inspected the TripoSR forward —
  DINO ViT tokenizer + Transformer1D backbone + triplane decoder MLP are all
  traceable modules, but marching cubes (torchmcubes CPU shim) is NOT
  exportable and would stay numpy. Estimated 2–4h work for ~20–30% RAM saving
  on a path the owner already quality-rejected. Not pursued; re-evaluate if
  local quality ever matters more than API/GPU backbones.
- **Quantization**: bf16 is already the quantization win (1.94GB → 840MB
  params). Dynamic int8 would risk further quality loss on a quality-rejected
  path — not pursued.
- **Chunked marching cubes**: the triplane query side already chunks
  (`FORGE3D_TRIPOSR_CHUNK`, default 8192); the density grid itself is only
  67MB at 256³ — true tiled marching-cubes would solve a problem we don't
  have. Not pursued.

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
