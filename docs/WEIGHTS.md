# WEIGHTS.md — model weight sources (canonical manifest)

Every weight the Forge3D free pipeline can fetch. Weights are NEVER committed
to the repo. They download lazily into `~/.forge3d/weights/<name>/` on first
use. Disk rule: at most ONE active weight set stays on local disk; everything
else streams (download → use → prune) or lives on the GPU runner.

## License-strict pipeline (MIT/Apache-2.0 only)

| Weights | Source | License | Size | VRAM |
|---|---|---|---|---|
| TripoSR `model.ckpt` + `config.yaml` | https://huggingface.co/stabilityai/TripoSR | MIT | ~1.3 GB ckpt (fp32); 838 MB bf16 safetensors (pre-converted, preferred) | ~6 GB (CPU fallback works) |
| TRELLIS.2-4B (safetensors repo) | https://huggingface.co/microsoft/TRELLIS.2-4B | MIT (code + weights) | ~8.5 GB | 24 GB official (A100/H100); 16 GB fp16 community path (experimental) |
| DINOv3 ViT-L/16 (TRELLIS.2 dep) | https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m | DINOv3 License — **gated, accept Meta's terms first** | ~1.2 GB | — |

Notes:
- TripoSR bf16 safetensors: pre-converted `model.bf16.safetensors` (838 MB)
  loads faster and uses less RAM than the fp32 ckpt. The provider prefers it
  automatically when present.
- TRELLIS.2 also needs its custom CUDA ops built from source
  (`TRELLIS.2/setup.sh`: flash-attn, flexgemm, o-voxel, cumesh, nvdiffrast) —
  Linux only. Not weights, but part of the install.
- `transformers>=4.40,<5.0` is MANDATORY for TripoSR (5.x silently breaks
  192/549 checkpoint keys → random-weight encoder). See docs/FREE_RUNNER_GUIDE.md.

## EXCLUDED from the license-strict pipeline

| Weights | Source | License | Why excluded |
|---|---|---|---|
| Hunyuan3D 2.1 | https://huggingface.co/tencent/Hunyuan3D-2.1 | Tencent Hunyuan 3D 2.1 Community License | NOT MIT/Apache-2.0: excludes EU/UK/South Korea, >1M MAU needs a separate Tencent license, mandatory attribution. ~10 GB shape-only / ~21–29 GB full pipeline. |

Hunyuan3D 2.1 is documented here for transparency only. The pipeline does not
fetch it. Owner decision required before any integration (2026-10-16).

## Fetch commands

```bash
# TripoSR (the one weight set allowed on local disk)
mkdir -p ~/.forge3d/weights/triposr && cd ~/.forge3d/weights/triposr
wget https://huggingface.co/stabilityai/TripoSR/resolve/main/model.ckpt
wget https://huggingface.co/stabilityai/TripoSR/resolve/main/config.yaml

# TRELLIS.2 (GPU runner only — do NOT download to the CPU sandbox)
export FORGE3D_WEIGHTS=~/.forge3d/weights
huggingface-cli download microsoft/TRELLIS.2-4B --local-dir $FORGE3D_WEIGHTS/trellis2
```
