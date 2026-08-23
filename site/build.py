from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = ROOT / "site"
SOURCE = SITE_ROOT / "src"
PUBLIC = SITE_ROOT / "public"
GIT_MARKER = ROOT / ".git"
DEFAULT_OUTPUT = SITE_ROOT / "dist"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SOURCE))

from content import EVIDENCE, LAB_UI, LOCALES, PAGES, ROUTES, SITE, Route  # noqa: E402
from demo_export import export_scenarios  # noqa: E402
from publication_validation import validate_publication  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the APR public site.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
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


def canonical_url(locale: str, slug: str) -> str:
    return SITE["origin"] + public_path(locale, slug)


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


def render_lab(locale: str) -> str:
    ui = LAB_UI[locale]
    fieldsets = []
    for name, legend, options in ui["controls"]:
        labels = []
        for index, (value, label) in enumerate(options):
            checked = " checked" if index == 0 else ""
            labels.append(
                '        <label class="lab-choice">'
                f'<input type="radio" name="{name}" value="{value}"{checked}>'
                f"<span>{label}</span></label>"
            )
        fieldsets.append(
            f'      <fieldset data-control="{name}">\n'
            f"        <legend>{legend}</legend>\n"
            '        <div class="lab-options">\n' + "\n".join(labels) + "\n        </div>\n"
            "      </fieldset>"
        )
    data_labels = " ".join(
        f'data-label-{field.replace("_", "-")}="{html.escape(label, quote=True)}"'
        for field, label in ui["fields"].items()
    )
    value_labels = html.escape(
        json.dumps(
            ui["value_labels"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        quote=True,
    )
    return (
        '    <section class="lab-panel" aria-labelledby="lab-controls-title">\n'
        f'      <h2 id="lab-controls-title">{html.escape(PAGES[locale]["lab"]["sections"][0]["title"])}</h2>\n'
        f'      <p id="lab-educational-notice" class="lab-notice" data-lab-notice>{html.escape(ui["notice"])}</p>\n'
        f'      <form class="apr-lab" data-apr-lab data-locale="{locale}" '
        f'data-load-error="{html.escape(ui["load_error"], quote=True)}" '
        f'data-missing-error="{html.escape(ui["missing_error"], quote=True)}" '
        f'data-value-labels="{value_labels}" '
        f'{data_labels} aria-describedby="lab-educational-notice">\n' + "\n".join(fieldsets) + "\n"
        f'      <output class="lab-output" data-lab-output aria-live="polite" aria-busy="true">{html.escape(ui["loading"])}</output>\n'
        "      </form>\n"
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
    lab = render_lab(locale) if route.slug == "lab" else ""
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
        '  <link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
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
        f"{lab}\n"
        f"{sections}\n"
        f"{evidence}\n"
        "  </main>\n"
        '  <footer class="site-footer">\n'
        f'    <p>{ui["source"]}: <a href="{commit_url}"><code>{SITE["source_ref"]}</code></a></p>\n'
        "  </footer>\n"
        '  <script type="module" src="/assets/app.js"></script>\n'
        "</body>\n"
        "</html>\n"
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def render_llms() -> str:
    lines = [
        f"# {SITE['name']}",
        "",
        "APR is a research architecture for bounded, evidence-governed perception.",
        f"Canonical site: {SITE['origin']}/",
        f"Version: {SITE['version']}",
        f"Release status: {SITE['release_status']}",
        "",
        "## Pages",
    ]
    for locale in LOCALES:
        language = "English" if locale == "en" else "Traditional Chinese"
        lines.append(f"### {language}")
        for route in ROUTES:
            lines.append(
                f"- {route.title[locale]}: {canonical_url(locale, route.slug)} — "
                f"{route.description[locale]}"
            )
        lines.append("")
    lines.extend(
        (
            "## Boundaries",
            "- Static research documentation and a deterministic offline educational lab.",
            "- No hosted agent, Provider call, API, authentication, analytics, or desktop control.",
            "- Local MCP is planned and not implemented; discovery grants no execution authority.",
            "- Release-candidate evidence is not a production-readiness claim.",
            "",
        )
    )
    return "\n".join(lines)


def render_sitemap() -> str:
    locations = [
        f"  <url><loc>{html.escape(canonical_url(locale, route.slug))}</loc></url>"
        for locale in LOCALES
        for route in ROUTES
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(locations)
        + "\n</urlset>\n"
    )


def render_404() -> str:
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <meta name="robots" content="noindex">\n'
        "  <title>Page not found · 找不到頁面 | APR</title>\n"
        '  <link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        '  <link rel="stylesheet" href="/assets/styles.css">\n'
        "</head>\n"
        "<body>\n"
        '  <main id="main" tabindex="-1">\n'
        '    <section class="hero" aria-labelledby="not-found-title">\n'
        '      <p class="kicker">404</p>\n'
        '      <h1 id="not-found-title">Page not found · 找不到頁面</h1>\n'
        "      <p>The requested APR page is unavailable. 請求的 APR 頁面不存在。</p>\n"
        '      <div class="hero-actions">\n'
        '        <a class="control" href="/">English home</a>\n'
        '        <a class="control" href="/zh-TW/">繁體中文首頁</a>\n'
        "      </div>\n"
        "    </section>\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def copy_public(source: Path, output: Path) -> None:
    if not source.exists():
        return
    files = sorted(path for path in source.rglob("*") if path.is_file())
    collisions = [
        path.relative_to(source) for path in files if (output / path.relative_to(source)).exists()
    ]
    if collisions:
        joined = ", ".join(path.as_posix() for path in collisions)
        raise FileExistsError(f"public asset collides with generated output: {joined}")
    for source_path in files:
        destination = output / source_path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)


def _git_metadata_paths() -> tuple[Path, ...]:
    paths = [GIT_MARKER.resolve(strict=False)]
    if not GIT_MARKER.is_file():
        return tuple(paths)
    try:
        pointer = GIT_MARKER.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return tuple(paths)
    if not pointer.startswith("gitdir:"):
        return tuple(paths)

    target = Path(pointer.removeprefix("gitdir:").strip())
    if not target.is_absolute():
        target = GIT_MARKER.parent / target
    target = target.resolve(strict=False)
    paths.append(target)
    common = next((path for path in (target, *target.parents) if path.name == ".git"), None)
    if common is not None:
        paths.append(common)
    return tuple(dict.fromkeys(paths))


def validate_output_path(output: Path) -> Path:
    try:
        candidate = Path(output).expanduser().resolve(strict=False)
    except OSError as exc:
        raise ValueError(f"cannot safely resolve output path: {output}") from exc

    if candidate == Path(candidate.anchor):
        raise ValueError(f"filesystem root cannot be a site output: {candidate}")

    protected = tuple(path.resolve(strict=False) for path in (ROOT, SITE_ROOT, SOURCE, PUBLIC))
    protected += _git_metadata_paths()
    for protected_path in protected:
        if candidate == protected_path or candidate in protected_path.parents:
            raise ValueError(f"output is a protected root or ancestor: {candidate}")

    for protected_path in (
        SOURCE.resolve(strict=False),
        PUBLIC.resolve(strict=False),
        *_git_metadata_paths(),
    ):
        if candidate == protected_path or protected_path in candidate.parents:
            raise ValueError(f"output is inside a protected source path: {candidate}")
    return candidate


def _is_valid_generated_index(index: object) -> bool:
    if type(index) is not dict or set(index) != {"schema", "site", "pages"}:
        return False
    if index.get("schema") != "apr-site-index/v1":
        return False
    site = index.get("site")
    if (
        type(site) is not dict
        or site.get("name") != SITE["name"]
        or site.get("origin") != SITE["origin"]
        or type(site.get("source_ref")) is not str
    ):
        return False
    pages = index.get("pages")
    if type(pages) is not list or len(pages) != len(LOCALES) * len(ROUTES):
        return False

    expected_pairs = {(locale, route.slug) for locale in LOCALES for route in ROUTES}
    actual_pairs: set[tuple[str, str]] = set()
    expected_page_fields = {
        "locale",
        "slug",
        "title",
        "description",
        "path",
        "url",
        "evidence_ids",
    }
    for page in pages:
        if type(page) is not dict or set(page) != expected_page_fields:
            return False
        locale = page["locale"]
        slug = page["slug"]
        if type(locale) is not str or type(slug) is not str:
            return False
        relative_path = page["path"]
        if type(relative_path) is not str:
            return False
        parsed_path = Path(relative_path)
        if parsed_path.is_absolute() or ".." in parsed_path.parts:
            return False
        if any(
            type(page[field]) is not str or not page[field]
            for field in ("title", "description", "url")
        ):
            return False
        evidence_ids = page["evidence_ids"]
        if type(evidence_ids) is not list or any(type(item) is not str for item in evidence_ids):
            return False
        actual_pairs.add((locale, slug))
    return actual_pairs == expected_pairs


def _existing_output_is_approved(output: Path) -> bool:
    if not output.exists():
        return False
    if not output.is_dir():
        raise ValueError(f"site output must be a directory: {output}")
    if next(output.iterdir(), None) is None:
        return True

    index_path = output / "ai" / "site.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"refusing to replace non-empty unowned output: {output}") from exc
    if not _is_valid_generated_index(index):
        raise ValueError(f"refusing to replace non-empty unowned output: {output}")
    return True


def _created_sibling(output: Path, kind: str, token: str) -> Path:
    return output.parent / f".{output.name}.apr-{kind}-{token}"


def _remove_created_tree(path: Path, *, output: Path, kind: str, token: str) -> None:
    expected = _created_sibling(output, kind, token)
    if path != expected or path.parent != output.parent:
        raise RuntimeError(f"refusing to delete an unvalidated build path: {path}")
    if not path.exists():
        return
    if not path.is_dir() or path.is_symlink():
        raise RuntimeError(f"refusing to recursively delete a non-directory build path: {path}")
    shutil.rmtree(path)


def _generate_tree(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)

    scenarios = export_scenarios()
    validate_publication(
        scenarios=scenarios,
        locales=LOCALES,
        routes=ROUTES,
        pages=PAGES,
        evidence=EVIDENCE,
        lab_ui=LAB_UI,
    )

    pages: list[dict[str, object]] = []
    for locale in LOCALES:
        for route in ROUTES:
            destination = route_path(output, locale, route.slug)
            write_text(destination, render_page(route, locale))
            pages.append(
                {
                    "locale": locale,
                    "slug": route.slug,
                    "title": route.title[locale],
                    "description": route.description[locale],
                    "path": destination.relative_to(output).as_posix(),
                    "url": canonical_url(locale, route.slug),
                    "evidence_ids": list(PAGES[locale][route.slug]["evidence_ids"]),
                }
            )

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
    demo_payload = {
        "schema": "apr-demo-scenarios/v1",
        "runtime_version": "0.10.0",
        "controls": ["freshness", "uncertainty", "risk", "conflict", "budget", "goal"],
        "scenarios": scenarios,
    }
    write_text(
        output / "data" / "demo-scenarios.json",
        json.dumps(
            demo_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
    )
    write_text(output / "llms.txt", render_llms())
    write_text(output / "sitemap.xml", render_sitemap())
    write_text(
        output / "robots.txt",
        f"User-agent: *\nAllow: /\nSitemap: {SITE['origin']}/sitemap.xml\n",
    )
    write_text(output / "404.html", render_404())
    copy_public(PUBLIC, output)
    return index


def _validate_generated_tree(output: Path, expected_index: dict[str, object]) -> None:
    try:
        index = json.loads((output / "ai/site.json").read_text(encoding="utf-8"))
        payload = json.loads((output / "data/demo-scenarios.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("generated site is missing valid machine-readable data") from exc

    if index != expected_index or not _is_valid_generated_index(index):
        raise ValueError("generated site index failed publication validation")
    if type(payload) is not dict or set(payload) != {
        "schema",
        "runtime_version",
        "controls",
        "scenarios",
    }:
        raise ValueError("generated scenario payload has an unapproved top-level shape")
    if payload["schema"] != "apr-demo-scenarios/v1" or payload["runtime_version"] != "0.10.0":
        raise ValueError("generated scenario payload has an unapproved schema or version")
    if payload["controls"] != [
        "freshness",
        "uncertainty",
        "risk",
        "conflict",
        "budget",
        "goal",
    ]:
        raise ValueError("generated scenario controls drifted from the public order")
    validate_publication(
        scenarios=payload["scenarios"],
        locales=LOCALES,
        routes=ROUTES,
        pages=PAGES,
        evidence=EVIDENCE,
        lab_ui=LAB_UI,
    )

    required_files = {
        route_path(output, locale, route.slug) for locale in LOCALES for route in ROUTES
    }
    required_files.update(
        {
            output / "ai/site.json",
            output / "data/demo-scenarios.json",
            output / "llms.txt",
            output / "sitemap.xml",
            output / "robots.txt",
            output / "404.html",
        }
    )
    source_assets = [path for path in SOURCE.joinpath("assets").iterdir() if path.is_file()]
    required_files.update(output / "assets" / path.name for path in source_assets)
    public_files = [path for path in PUBLIC.rglob("*") if path.is_file()]
    required_files.update(output / path.relative_to(PUBLIC) for path in public_files)
    missing = sorted(
        path.relative_to(output).as_posix() for path in required_files if not path.is_file()
    )
    if missing:
        raise ValueError(f"generated site is incomplete: {', '.join(missing)}")
    for source_path in source_assets:
        if source_path.read_bytes() != (output / "assets" / source_path.name).read_bytes():
            raise ValueError(f"generated asset differs from source: {source_path.name}")
    for source_path in public_files:
        destination = output / source_path.relative_to(PUBLIC)
        if source_path.read_bytes() != destination.read_bytes():
            raise ValueError(f"generated public asset differs from source: {source_path.name}")


def build(output: Path) -> dict[str, object]:
    output = validate_output_path(output)
    had_existing_output = _existing_output_is_approved(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    token = uuid.uuid4().hex
    temporary = _created_sibling(output, "build", token)
    backup = _created_sibling(output, "backup", token)
    if temporary.exists() or backup.exists():
        raise FileExistsError("unique site build sibling already exists")

    backup_created = False
    try:
        index = _generate_tree(temporary)
        _validate_generated_tree(temporary, index)

        if had_existing_output:
            output.replace(backup)
            backup_created = True
        try:
            temporary.replace(output)
        except BaseException:
            if backup_created:
                backup.replace(output)
                backup_created = False
            raise

        if backup_created:
            _remove_created_tree(backup, output=output, kind="backup", token=token)
            backup_created = False
        return index
    finally:
        if temporary.exists():
            _remove_created_tree(temporary, output=output, kind="build", token=token)
        if backup_created and backup.exists() and not output.exists():
            backup.replace(output)


if __name__ == "__main__":
    build(parse_args().output)
