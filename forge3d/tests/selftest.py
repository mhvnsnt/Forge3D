"""Forge3D install selftest: verifies pipeline wiring WITHOUT generating.

Checks: package imports, registry discovery, base interface contract,
pipeline stage recording, CLI entry points. No network, no GPU, no keys.
"""
from __future__ import annotations

import tempfile
from pathlib import Path


def _check(name, fn) -> bool:
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {name}: {e}")
        return False
    print(f"ok   {name}")
    return True


def test_imports():
    import forge3d  # noqa
    from forge3d.providers import base, registry  # noqa
    from forge3d.pipelines import pipeline, postprocess  # noqa
    from forge3d import __main__  # noqa


def test_provider_contract():
    from forge3d.providers.base import Capability, ModelProvider, ProviderInfo

    class Dummy(ModelProvider):
        info = ProviderInfo(name="dummy-test", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            glb = Path(out_dir) / "dummy.glb"
            glb.write_bytes(b"glTF-test-double")
            from forge3d.providers.base import GenerateResult
            return GenerateResult(glb_path=glb, provider="dummy-test")

    d = Dummy()
    assert d.is_available()[0]
    assert Capability.IMAGE_TO_3D in d.info.capabilities


def test_pipeline_records_stages():
    from forge3d.providers.base import (Capability, GenerateResult,
                                        ModelProvider, ProviderInfo)
    from forge3d.pipelines.pipeline import Pipeline
    import json

    class Dummy(ModelProvider):
        info = ProviderInfo(name="dummy-pipe", kind="local",
                            capabilities=[Capability.IMAGE_TO_3D])

        def is_available(self):
            return True, "test double"

        def generate(self, *, prompt=None, image=None, out_dir, **kw):
            glb = Path(out_dir) / "m.glb"
            glb.write_bytes(b"glTF")
            return GenerateResult(glb_path=glb, provider="dummy-pipe")

    with tempfile.TemporaryDirectory() as td:
        res = Pipeline(Dummy(), Path(td)).run(prompt="test orc")
        assert res.glb_path.exists()
        manifest = json.loads(res.run_manifest.read_text())
        stages = [s["stage"] for s in manifest["stages"]]
        for want in ("concept", "mesh", "cleanup", "export", "handoff"):
            assert want in stages, f"missing stage {want}: {stages}"


def test_registry_discovers():
    from forge3d.providers.registry import discover
    found = discover()
    assert isinstance(found, dict)
    # real providers register here once wired; empty is fine pre-inventory


def test_cli_parses():
    from forge3d.__main__ import main
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["providers"])
    assert rc == 0


def run() -> bool:
    checks = [
        ("imports", test_imports),
        ("provider-contract", test_provider_contract),
        ("pipeline-stages", test_pipeline_records_stages),
        ("registry-discovery", test_registry_discovers),
        ("cli-parses", test_cli_parses),
    ]
    results = [_check(n, f) for n, f in checks]
    print(f"{sum(results)}/{len(results)} selftest checks passed")
    return all(results)
