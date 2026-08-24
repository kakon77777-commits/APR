from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apr_runtime import (  # noqa: E402
    DEFAULT_VERTEX_IMAGE_MODEL,
    DEFAULT_VERTEX_LOCATION,
    GoogleVertexImageGenerationPlugin,
    PluginRegistry,
)

DEFAULT_OUTPUT = (
    ROOT / "artifacts" / "vertex-image-generation" / "apr-measured-evidence-v2-20260810.png"
)
DEFAULT_PROMPT = """Use case: stylized-concept
Asset type: APR research infrastructure concept art
Primary request: an original visual metaphor for measured evidence and restrained action
Scene/backdrop: a quiet, dark observatory-like research room with simple empty architecture; no shelves, jars, displays, or background objects
Subject: one compact autonomous brass-and-glass research instrument examining a single luminous crystal specimen; exactly three concentric translucent rings around the specimen suggest direct observation, uncertainty, and the boundary before action
Style/medium: cinematic editorial illustration with grounded materials and fine painterly detail
Composition/framing: square composition, instrument and specimen clearly readable, balanced negative space
Lighting/mood: one warm focused beam, calm and contemplative, restrained contrast
Color palette: deep blue-black, muted brass, soft amber and cyan light
Constraints: exactly one instrument, exactly one crystal specimen, and exactly three rings in the entire image; the background contains no other containers, crystals, instruments, or props; no people; no text; no letters; no logos; no watermark"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate one real image through the APR Google Vertex plugin."
    )
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    parser.add_argument("--location", default=DEFAULT_VERTEX_LOCATION)
    parser.add_argument("--model", default=DEFAULT_VERTEX_IMAGE_MODEL)
    parser.add_argument("--credentials", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--image-size", default="1K")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = args.output.expanduser().resolve()
    metadata_path = output.with_suffix(".json")
    safe_config = {
        "provider": "google_vertex",
        "model": args.model,
        "location": args.location,
        "aspect_ratio": args.aspect_ratio,
        "image_size": args.image_size,
        "output": str(output),
        "metadata_output": str(metadata_path),
        "prompt": args.prompt,
        "credentials_configured": bool(
            args.credentials or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        ),
    }
    if args.dry_run:
        print(json.dumps(safe_config, ensure_ascii=False, indent=2))
        return 0
    if metadata_path.exists() and not args.overwrite:
        raise FileExistsError(f"Generation metadata already exists: {metadata_path}")

    registry = PluginRegistry()
    registry.install(GoogleVertexImageGenerationPlugin())
    generator = registry.create_component(
        "image_generator",
        "google_vertex",
        project_id=args.project,
        location=args.location,
        model=args.model,
        credentials_path=args.credentials,
        aspect_ratio=args.aspect_ratio,
        image_size=args.image_size,
    )
    result = generator.generate(args.prompt, output_path=output, overwrite=args.overwrite)
    report = {
        **safe_config,
        "requested_output": str(output),
        "output": str(result.path),
        "mime_type": result.mime_type,
        "width": result.width,
        "height": result.height,
        "byte_count": result.byte_count,
        "sha256": result.sha256,
        "metadata": result.metadata,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if args.overwrite else "x"
    with metadata_path.open(mode, encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
