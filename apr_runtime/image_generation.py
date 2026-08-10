from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Protocol, runtime_checkable


@dataclass(frozen=True)
class ImageGenerationResult:
    """A generated image persisted as a provenance-bearing local artifact."""

    path: Path
    prompt: str
    provider: str
    model: str
    mime_type: str
    width: int
    height: int
    byte_count: int
    sha256: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ImageGenerator(Protocol):
    """Minimal APR protocol for opt-in hosted or local image generators."""

    name: str

    def generate(
        self,
        prompt: str,
        *,
        output_path: str | Path,
        overwrite: bool = False,
    ) -> ImageGenerationResult: ...
