"""Convert TripoSR fp32 checkpoint to bf16 safetensors, in small chunks."""
import os, gc
os.environ["no_proxy"] = "localhost,127.0.0.1"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
import torch
from safetensors.torch import save_file

print("mmap loading fp32 ckpt...", flush=True)
ckpt = torch.load('/home/hatch/.forge3d/weights/triposr/model.ckpt',
                   map_location='cpu', mmap=True, weights_only=False)
keys = list(ckpt.keys())
print(f"{len(keys)} tensors", flush=True)

out_path = '/home/hatch/.forge3d/weights/triposr/model.bf16.safetensors'
# Convert in chunks of 50 tensors to bound memory
CHUNK = 50
converted = {}
for i in range(0, len(keys), CHUNK):
    chunk_keys = keys[i:i+CHUNK]
    for k in chunk_keys:
        converted[k] = ckpt[k].to(torch.bfloat16)
    print(f"converted {min(i+CHUNK, len(keys))}/{len(keys)}", flush=True)
    gc.collect()

print("saving...", flush=True)
save_file(converted, out_path)
print(f"saved {out_path}", flush=True)
del converted
gc.collect()
import os as _os
print(f"size: {_os.path.getsize(out_path)/1e9:.2f}GB", flush=True)
print("CONVERT DONE", flush=True)
