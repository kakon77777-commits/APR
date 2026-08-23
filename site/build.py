from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SOURCE))

from content import LOCALES, ROUTES, SITE, Route  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the APR public site.")
    parser.add_argument("--output", type=Path, default=Path("site/dist"))
    return parser.parse_args()


def route_path(output: Path, locale: str, slug: str) -> Path:
    prefix = output if locale == "en" else output / locale
    return prefix / slug / "index.html" if slug else prefix / "index.html"


def render_page(route: Route, locale: str) -> str:
    title = html.escape(route.title[locale])
    description = html.escape(route.description[locale])
    return (
        "<!doctype html>\n"
        f'<html lang="{locale}">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{title} | {SITE['name']}</title>\n"
        f'  <meta name="description" content="{description}">\n'
        '  <link rel="stylesheet" href="/assets/styles.css">\n'
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        f"    <h1>{title}</h1>\n"
        f"    <p>{description}</p>\n"
        "  </main>\n"
        '  <script src="/assets/app.js"></script>\n'
        "</body>\n"
        "</html>\n"
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build(output: Path) -> dict[str, object]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    pages: list[dict[str, str]] = []
    for locale in LOCALES:
        for route in ROUTES:
            destination = route_path(output, locale, route.slug)
            write_text(destination, render_page(route, locale))
            pages.append({"locale": locale, "path": destination.relative_to(output).as_posix()})

    assets = SOURCE / "assets"
    for asset in sorted(assets.iterdir()):
        if asset.is_file():
            destination = output / "assets" / asset.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset, destination)

    index: dict[str, object] = {"schema": "apr-site-index/v1", "site": SITE, "pages": pages}
    write_text(
        output / "ai" / "site.json", json.dumps(index, ensure_ascii=False, sort_keys=True) + "\n"
    )
    return index


if __name__ == "__main__":
    build(parse_args().output)
