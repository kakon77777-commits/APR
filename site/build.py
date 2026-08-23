from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SOURCE))

from content import EVIDENCE, LOCALES, PAGES, ROUTES, SITE, Route  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the APR public site.")
    parser.add_argument("--output", type=Path, default=Path("site/dist"))
    return parser.parse_args()


def route_path(output: Path, locale: str, slug: str) -> Path:
    prefix = output if locale == "en" else output / locale
    return prefix / slug / "index.html" if slug else prefix / "index.html"


def public_path(locale: str, slug: str) -> str:
    parts = [part for part in (("zh-TW" if locale == "zh-TW" else ""), slug) if part]
    return "/" + "/".join(parts) + ("/" if parts else "")


def source_url(evidence_id: str) -> str:
    root = f"https://github.com/kakon77777-commits/APR/blob/{SITE['source_ref']}/"
    return root + EVIDENCE[evidence_id]


def render_sections(page: dict[str, object]) -> str:
    rendered = []
    for index, section in enumerate(page["sections"]):
        section_id = f"section-{index + 1}"
        items = section.get("items", ())
        item_html = ""
        if items:
            cards = []
            for label, text, tone in items:
                cards.append(
                    f'        <li class="signal signal--{html.escape(tone)}">\n'
                    f'          <span class="state-label">{html.escape(label)}</span>\n'
                    f"          <span>{html.escape(text)}</span>\n"
                    "        </li>"
                )
            item_html = '      <ul class="signal-grid">\n' + "\n".join(cards) + "\n      </ul>\n"
        rendered.append(
            f'    <section class="content-section" aria-labelledby="{section_id}">\n'
            f'      <h2 id="{section_id}">{html.escape(section["title"])}</h2>\n'
            f"      <p>{html.escape(section['body'])}</p>\n"
            f"{item_html}"
            "    </section>"
        )
    return "\n".join(rendered)


def render_evidence(page: dict[str, object], locale: str) -> str:
    title = "Source evidence" if locale == "en" else "來源證據"
    description = (
        "Immutable links pinned to the candidate source reference."
        if locale == "en"
        else "固定於候選來源版本的不可變連結。"
    )
    links = []
    for evidence_id in page["evidence_ids"]:
        path = EVIDENCE[evidence_id]
        links.append(
            "        <li>"
            f'<a href="{html.escape(source_url(evidence_id), quote=True)}">'
            f'<span class="evidence-id">{html.escape(evidence_id)}</span>'
            f"<code>{html.escape(path)}</code></a></li>"
        )
    return (
        '    <section class="content-section evidence" aria-labelledby="source-evidence">\n'
        f'      <h2 id="source-evidence">{title}</h2>\n'
        f"      <p>{description}</p>\n"
        '      <ul class="evidence-list">\n' + "\n".join(links) + "\n      </ul>\n"
        "    </section>"
    )


def render_page(route: Route, locale: str) -> str:
    title = html.escape(route.title[locale])
    description = html.escape(route.description[locale])
    page = PAGES[locale][route.slug]
    language = "zh-Hant" if locale == "zh-TW" else "en"
    canonical = SITE["origin"] + public_path(locale, route.slug)
    english_url = SITE["origin"] + public_path("en", route.slug)
    chinese_url = SITE["origin"] + public_path("zh-TW", route.slug)
    switch_locale = "en" if locale == "zh-TW" else "zh-TW"
    switch_url = public_path(switch_locale, route.slug)
    ui = {
        "en": {
            "skip": "Skip to main content",
            "nav": "Primary navigation",
            "home": "APR home",
            "brandline": "Perceive · Verify · Recover",
            "language": "閱讀繁體中文",
            "source": "Candidate source",
            "lab": "Open the lab",
            "runtime": "Read the runtime guide",
            "github": "View on GitHub",
        },
        "zh-TW": {
            "skip": "跳至主要內容",
            "nav": "主要導覽",
            "home": "APR 首頁",
            "brandline": "感知 · 驗證 · 復原",
            "language": "Read in English",
            "source": "候選來源",
            "lab": "開啟實驗室",
            "runtime": "閱讀 Runtime 指南",
            "github": "在 GitHub 查看",
        },
    }[locale]
    navigation = []
    for item in ROUTES:
        current = ' aria-current="page"' if item.slug == route.slug else ""
        navigation.append(
            f'        <li><a href="{public_path(locale, item.slug)}"{current}>'
            f"{html.escape(item.title[locale])}</a></li>"
        )
    commit_url = f"https://github.com/kakon77777-commits/APR/commit/{SITE['source_ref']}"
    sections = render_sections(page)
    evidence = render_evidence(page, locale)
    return (
        "<!doctype html>\n"
        f'<html lang="{language}">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{title} | {SITE['name']}</title>\n"
        f'  <meta name="description" content="{description}">\n'
        f'  <link rel="canonical" href="{canonical}">\n'
        f'  <link rel="alternate" hreflang="en" href="{english_url}">\n'
        f'  <link rel="alternate" hreflang="zh-Hant" href="{chinese_url}">\n'
        f'  <link rel="alternate" hreflang="x-default" href="{english_url}">\n'
        '  <meta property="og:type" content="website">\n'
        f'  <meta property="og:site_name" content="{SITE["name"]}">\n'
        f'  <meta property="og:title" content="{title} | {SITE["name"]}">\n'
        f'  <meta property="og:description" content="{description}">\n'
        f'  <meta property="og:url" content="{canonical}">\n'
        '  <link rel="stylesheet" href="/assets/styles.css">\n'
        "</head>\n"
        "<body>\n"
        f'  <a class="skip-link" href="#main">{ui["skip"]}</a>\n'
        '  <header class="site-header">\n'
        f'    <a class="brand" href="{public_path(locale, "")}" aria-label="{ui["home"]}"><span>APR</span><small>{ui["brandline"]}</small></a>\n'
        f'    <nav aria-label="{ui["nav"]}">\n'
        '      <ul class="nav-list">\n' + "\n".join(navigation) + "\n      </ul>\n"
        "    </nav>\n"
        f'    <a class="language-switch" href="{switch_url}" hreflang="{("en" if switch_locale == "en" else "zh-Hant")}">{ui["language"]}</a>\n'
        "  </header>\n"
        '  <main id="main" tabindex="-1">\n'
        '    <section class="hero" aria-labelledby="page-title">\n'
        f'      <p class="kicker">{html.escape(page["kicker"])}</p>\n'
        f'      <h1 id="page-title">{html.escape(page["heading"])}</h1>\n'
        f'      <p class="lede">{html.escape(page["summary"])}</p>\n'
        f'      <p class="status status--{html.escape(page["status_tone"])}"><span class="state-label">{html.escape(page["status_label"])}</span><span>{html.escape(page["status_text"])}</span></p>\n'
        '      <div class="hero-actions">\n'
        f'        <a class="control" href="{public_path(locale, "lab")}">{ui["lab"]}</a>\n'
        f'        <a class="control" href="{public_path(locale, "runtime")}">{ui["runtime"]}</a>\n'
        f'        <a class="control control--quiet" href="https://github.com/kakon77777-commits/APR">{ui["github"]}</a>\n'
        "      </div>\n"
        "    </section>\n"
        f"{sections}\n"
        f"{evidence}\n"
        "  </main>\n"
        '  <footer class="site-footer">\n'
        f'    <p>{ui["source"]}: <a href="{commit_url}"><code>{SITE["source_ref"]}</code></a></p>\n'
        "  </footer>\n"
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
