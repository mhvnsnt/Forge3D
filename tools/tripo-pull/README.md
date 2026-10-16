# tripo-pull — recover your Tripo Studio models without paying for export

Tripo Studio locked model export behind a paywall, but models you shared via
public links (`https://studio.tripo3d.ai/3d-model/<uuid>`) expose their files
through Tripo's own public project-detail API. `tripo_pull.py` resolves each
link to the direct PBR GLB download and pulls it. No sign-in, no browser, no
credits.

## Usage

```bash
python tripo_pull.py <share-url-or-uuid> [more ...] [-o OUTDIR] [--all]
```

```bash
# one model
python tripo_pull.py https://studio.tripo3d.ai/3d-model/bfd5233e-4451-4494-8643-fdceceb2e184

# several, bare UUIDs work too
python tripo_pull.py bfd5233e-4451-4494-8643-fdceceb2e184 0309c453-c6df-4077-87b6-346d14cad382 -o ./models

# also grab the point-cloud GLB + preview render
python tripo_pull.py <uuid> --all
```

## What you get per model

- `<slug>.glb` — the PBR textured model (meshopt-compressed GLB: albedo + ORM + normal maps)
- `<slug>.manifest.json` — project name/UUID, source share URL, direct file URL,
  byte size, and structural verification (mesh/material/texture counts)

The tool verifies every download: GLB magic bytes plus a structural parse
(requires `pygltflib`, optional). Exit code is 1 if any model fails.

## How it works

`GET https://api.tripo3d.ai/v2/studio/project/detail/v3/<project-uuid>`
returns JSON including `model_url` — the signed CloudFront URL for the
`tripo_pbr_model_*_meshopt.glb`. Signed URLs expire, so download promptly;
re-run the tool for fresh URLs.

## Notes

- Only works for models with public share links (free-tier Tripo models are
  public by default). Private/unshared models are not reachable.
- The GLBs are meshopt-compressed; Blender 4.2+ imports them directly.
  Older Blender needs the file decoded first.
- No third-party code is vendored here; the API endpoint was found by
  inspecting Tripo Studio's own page bundles. Your models, your files.
