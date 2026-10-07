"""Forge3D CLI: generate / providers / selftest."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_providers(_args) -> int:
    from forge3d.providers.registry import discover
    for name, p in sorted(discover().items()):
        ok, reason = p.is_available()
        caps = ",".join(c.value for c in p.info.capabilities)
        print(f"{name:20s} [{p.info.kind:5s}] {'OK ' if ok else 'DOWN'} "
              f"caps={caps} license={p.info.license} {'' if ok else reason}")
    return 0


def cmd_generate(args) -> int:
    from forge3d.providers.registry import discover, available
    from forge3d.pipelines.pipeline import Pipeline, ProviderError

    providers = discover()
    if args.provider == "auto":
        pool = available()
        if not pool:
            print("no provider available; run `providers` for reasons", file=sys.stderr)
            return 2
        # Fallback chain for image-to-3d: best quality first, local CPU last.
        # A provider that raises ProviderError is skipped; the next is tried.
        # (Owner law: failures are loud, never masked into fake output.)
        QUALITY_ORDER = ["trellis2-space", "instantmesh-space",
                         "pollinations-3d", "tripo-api",
                         "triposg", "trellis2", "hi3dgen", "sf3d", "triposr"]
        def rank(item):
            name, p = item
            try:
                q = QUALITY_ORDER.index(name)
            except ValueError:
                q = len(QUALITY_ORDER)
            return (q,)
        chain = [name for name, _ in sorted(pool.items(), key=rank)]
    else:
        prov = providers.get(args.provider)
        name = args.provider
        if prov is None:
            print(f"unknown provider {name}", file=sys.stderr)
            return 2
        chain = [name]
    errors = []
    for name in chain:
        prov = providers[name]
        print(f"provider: {name}")
        try:
            result = Pipeline(prov, Path(args.out)).run(
                prompt=args.prompt, image=Path(args.image) if args.image else None,
                texture=None if args.texture == "none" else args.texture,
                densify=not args.no_densify,
                rig=args.rig)
        except ProviderError as e:
            print(f"provider {name} FAILED: {e}", file=sys.stderr)
            errors.append(f"{name}: {e}")
            continue
        print(f"GLB: {result.glb_path}")
        print(f"manifest: {result.run_manifest}")
        return 0
    print(f"ALL PROVIDERS FAILED (no fake output produced):", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    return 1


def cmd_selftest(_args) -> int:
    from forge3d.tests.selftest import run
    ok = run()
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="forge3d")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("providers")
    g = sub.add_parser("generate")
    g.add_argument("--prompt", default=None)
    g.add_argument("--image", default=None)
    g.add_argument("--provider", default="auto")
    g.add_argument("--out", default="out")
    g.add_argument("--texture", default="lanczos",
                   choices=["lanczos", "realesrgan", "hunyuan-paint", "none"],
                   help="texture refinement backend (none = skip)")
    g.add_argument("--no-densify", action="store_true",
                   help="skip geometry densification")
    g.add_argument("--rig", action="store_true",
                   help="auto-rig the output (instance-rig, CPU)")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    # allow running from repo root without install
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    return {"providers": cmd_providers, "generate": cmd_generate,
            "selftest": cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
