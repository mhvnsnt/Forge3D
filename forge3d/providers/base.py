"""Forge3D provider interface.

Every backend (local model or free API) implements ModelProvider.
Providers NEVER return placeholder/fake meshes: on failure they raise
ProviderError. (Owner law: no fake outputs.)
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Capability(Enum):
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    MULTIVIEW = "multiview"
    TEXTURE = "texture"
    TEXT_TO_IMAGE = "text_to_image"


class ProviderError(RuntimeError):
    """Raised when a provider genuinely fails. Never swallowed into a fake mesh."""


@dataclass
class ProviderInfo:
    name: str
    kind: str  # "local" | "api"
    capabilities: list[Capability] = field(default_factory=list)
    license: str = ""            # SPDX id of the backend software / API terms summary
    commercial_ok: bool = False
    needs_gpu: bool = False
    needs_key: bool = False
    quota_note: str = ""         # free-tier quota, from docs/API_INVENTORY


@dataclass
class GenerateResult:
    glb_path: Path
    provider: str
    texture_paths: list[Path] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


class ModelProvider(abc.ABC):
    info: ProviderInfo

    @abc.abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """(ok, reason). Checks deps/GPU/key/quota without generating."""

    @abc.abstractmethod
    def generate(self, *, prompt: str | None, image: Path | None,
                 out_dir: Path, **kwargs) -> GenerateResult:
        """Run the backend. Must produce a real GLB or raise ProviderError."""

    def estimate_cost(self) -> str:
        return "free" if self.info.kind == "local" else self.info.quota_note
