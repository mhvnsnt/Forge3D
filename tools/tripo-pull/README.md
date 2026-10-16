# tripo-pull — download your Tripo3D Studio models, any time

Tripo Studio locked free exports behind a paywall, and their site has
Cloudflare / auth weirdness that blocks exports even when you have them.
`tripo-pull` gets your models anyway: it resolves a public share link to
Tripo's own download URL and pulls the file. No browser, no sign-in needed
for public links.

## Quick start

```bash
# one model (share link or bare UUID)
python tripo-pull.py https://studio.tripo3d.ai/3d-model/67a6f309-0ac2-4c56-92b8-a4ea3e72bf46

# several at once, custom output dir
python tripo-pull.py <uuid1> <uuid2> -o ./my-models

# also grab point-cloud model + preview render
python tripo-pull.py <uuid> --all

# convert to FBX after download (needs Blender, see below)
python tripo-pull.py <uuid> --to fbx

# multiple formats
python tripo-pull.py <uuid> --to fbx,obj,usdz
```

## What you get per model

- `<name>.glb` — PBR textured model (meshopt-compressed: albedo + ORM + normal)
- `<name>.manifest.json` — project name/UUID, share URL, direct file URL,
  byte size, structural verification
- `<name>.fbx` / `.obj` / … — converted formats (only with `--to`)

The tool verifies every download (GLB magic bytes + mesh/texture counts).
Exit code is `1` if any model fails — failed models never leave partial files.

## How it works

Three strategies, tried in order:

1. **Public project-detail API** — `GET
   api.tripo3d.ai/v2/studio/project/detail/v3/<uuid>` returns the signed
   download URL. Works with no sign-in for any model that has a public
   share link (free-tier Tripo models are public by default).
2. **Page HTML scrape** — fallback that extracts embedded model URLs from
   the Studio page itself.
3. **Official Tripo API** — uses `TRIPO_API_KEY` for private models.

User-Agents rotate automatically if Tripo rate-limits one.

## API key (optional)

Only needed for **private** (unshared) models. Public share links work
without any key.

1. Go to https://platform.tripo3d.ai/ → sign in → API keys
2. `export TRIPO_API_KEY='tsk_...'`
3. Re-run — the official-API strategy will pick it up

Never commit the key to a repo. Env var or secure vault only.

## Format conversion (`--to`)

Tripo serves GLB. `--to` converts locally with headless Blender:

```bash
python tripo-pull.py <uuid> --to fbx
```

Supported: `fbx obj usdz stl ply x3d` (whatever your Blender can export).

Blender is found automatically from common install locations
(`blender` on PATH, `~/workspace/tools/blender/`, etc.) or set
`BLENDER_BIN=/path/to/blender`.

Note: meshopt-compressed GLBs need Blender 4.2+ for direct import.

## Troubleshooting

| Problem | Fix |
|---|---|
| `no Tripo project UUID found` | Pass the full share link or the bare UUID from it |
| `model may not have a public share link` | In Tripo Studio, open the model → Share → copy the new link |
| `download URL expired (HTTP 403)` | Signed URLs are short-lived — just re-run tripo-pull |
| `Cloudflare-blocking` | Complete the "verify you are human" check in a browser once, then re-run |
| `BLENDER_BIN not found` | Install Blender or set `BLENDER_BIN`; conversion is skipped without it |
| All strategies failed | Model may be deleted/private — Share it publicly in Tripo Studio first |

## Requirements

Python 3.8+, stdlib only. No `pip install` needed.
Optional: Blender 4.2+ (only for `--to` conversion).

## License note

No third-party code is vendored. The public API endpoint was found by
inspecting Tripo Studio's own page bundles. Your models, your files —
this tool just automates what the Share button already exposes.
