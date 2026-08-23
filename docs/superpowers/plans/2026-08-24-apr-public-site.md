# APR Public Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a bilingual, static APR research site at `apr.evemisslab.com`, with an offline deterministic APR lab and a verified bilingual entry on `evemisslab.com`.

**Architecture:** A standard-library Python compiler inside the APR repository produces static HTML, CSS, JavaScript and machine-discovery files. The browser lab looks up a finite scenario matrix exported by the real APR Python runtime at build time; it never reimplements APR policy or calls a remote service. Cloudflare serves assets only, while the existing `evemisslab.com` Pages repository receives a separate minimal index change.

**Tech Stack:** Python 3.10+, `unittest`, static HTML/CSS/JavaScript, Wrangler 4.92.0, Cloudflare Workers Static Assets, Cloudflare Pages for the parent index.

**Spec:** `docs/superpowers/specs/2026-08-24-apr-public-site-design.md`

## Global Constraints

- Execution is paused while the user's no-test boundary remains active. Do not implement this plan until the user explicitly permits non-interactive tests.
- Do not open, foreground, capture or control a desktop window during Tasks 1–6.
- Do not call OpenAI, Anthropic, Google Vertex or any other paid Provider.
- Do not read Provider credentials, ADC files, browser profiles or unrelated local files.
- Human pages are English at `/` and Traditional Chinese under `/zh-TW/`.
- The public site has no backend API, authentication, cookies, analytics, telemetry, uploads or remote fonts.
- The public site never connects to localhost, MCP, desktop adapters or browser adapters.
- Generated output contains no absolute local path, credential, raw hosted response or private evidence.
- APR repository licensing remains unspecified; site copy must not claim an open-source licence.
- Production deployment requires a separate explicit user instruction after browser validation.
- Preserve unrelated changes in both repositories; never stage them into an APR website commit.
- APR release work starts from the approved design commit `dba5aa2` and runtime baseline `d1722ec`.
- The parent index is a separate repository at `D:\Ai\網站群\evemisslab`; it remains on its existing Cloudflare Pages project.

---

## File map

APR repository:

- `site/build.py` — deterministic site compiler and command-line output selection.
- `site/src/content.py` — bilingual navigation, page copy, evidence and paper metadata.
- `site/src/demo_export.py` — sanitized finite scenario matrix generated from APR core.
- `site/src/assets/styles.css` — APR visual tokens, responsive layout and accessibility states.
- `site/src/assets/app.js` — locale-neutral navigation and offline lab lookup/rendering.
- `site/public/_headers` — static security headers.
- `site/package.json` — pinned Wrangler-only deployment scripts.
- `site/package-lock.json` — exact Wrangler dependency resolution.
- `site/wrangler.jsonc` — assets-only Worker and `apr.evemisslab.com` route.
- `site/dist/` — generated output; ignored by Git.
- `tests/test_site_build.py` — compiler, route, translation, machine-index and security tests.
- `tests/test_site_demo.py` — scenario completeness, APR provenance and sanitization tests.
- `.gitignore` — generated website and Wrangler state.
- `README.md`, `docs/README.md`, `STATUS.md` — public-site documentation and measured release status.

Parent index repository:

- `src/content.py` — one APR entry in each language.
- `src/assets/styles.css` — APR tone in light and both dark token blocks.
- `tests/test_apr_entry.py` — bilingual entry, generated-link and tone tests.

---

### Task 1: Deterministic static compiler and locale contract

**Files:**

- Create: `site/build.py`
- Create: `site/src/content.py`
- Create: `site/src/assets/styles.css`
- Create: `site/src/assets/app.js`
- Create: `tests/test_site_build.py`
- Modify: `.gitignore`

**Interfaces:**

- Produces: `site/build.py --output <directory>` with exit code `0` on a complete build.
- Produces: `content.ROUTES: tuple[Route, ...]`, `content.LOCALES`, `content.SITE`.
- Produces: `site/dist/<route>/index.html` plus copied same-origin assets.
- Consumes: only repository source files and Python standard library.

- [ ] **Step 1: Write the failing compiler contract tests**

```python
# tests/test_site_build.py
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SiteBuildTests(unittest.TestCase):
    def build(self, output: Path) -> None:
        subprocess.run(
            [sys.executable, "-B", "site/build.py", "--output", str(output)],
            cwd=ROOT,
            check=True,
        )

    def test_build_emits_every_bilingual_route(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            routes = ("", "runtime", "lab", "papers", "mcp", "status")
            for route in routes:
                english = output / route / "index.html" if route else output / "index.html"
                chinese = output / "zh-TW" / route / "index.html"
                self.assertTrue(english.is_file(), english)
                self.assertTrue(chinese.is_file(), chinese)

    def test_build_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as left_raw, tempfile.TemporaryDirectory() as right_raw:
            left, right = Path(left_raw), Path(right_raw)
            self.build(left)
            self.build(right)
            left_files = {p.relative_to(left): p.read_bytes() for p in left.rglob("*") if p.is_file()}
            right_files = {p.relative_to(right): p.read_bytes() for p in right.rglob("*") if p.is_file()}
            self.assertEqual(left_files, right_files)

    def test_machine_index_is_valid_json(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            self.build(output)
            data = json.loads((output / "ai/site.json").read_text(encoding="utf-8"))
            self.assertEqual("apr-site-index/v1", data["schema"])
```

- [ ] **Step 2: Run the focused test and verify the expected failure**

Run:

```powershell
python -m unittest discover -s tests -p test_site_build.py -v
```

Expected: FAIL because `site/build.py` does not exist.

- [ ] **Step 3: Add the minimal compiler and typed content contract**

Implement these public shapes in `site/src/content.py`:

```python
from dataclasses import dataclass
from typing import Mapping

LOCALES = ("en", "zh-TW")
SITE = {
    "origin": "https://apr.evemisslab.com",
    "name": "APR",
    "version": "0.10.0",
    "source_ref": "d1722eca845353acd3ce1f7241283bfa16263e93",
    "release_status": "candidate",
}


@dataclass(frozen=True)
class Route:
    slug: str
    title: Mapping[str, str]
    description: Mapping[str, str]


ROUTES = (
    Route("", {"en": "APR", "zh-TW": "APR"}, {"en": "Adaptive Perceptual Reading", "zh-TW": "自適應感知閱讀"}),
    Route("runtime", {"en": "Runtime", "zh-TW": "Runtime"}, {"en": "APR runtime architecture", "zh-TW": "APR Runtime 架構"}),
    Route("lab", {"en": "Lab", "zh-TW": "實驗室"}, {"en": "Offline APR decision lab", "zh-TW": "離線 APR 決策實驗室"}),
    Route("papers", {"en": "Papers", "zh-TW": "論文"}, {"en": "APR theory index", "zh-TW": "APR 理論索引"}),
    Route("mcp", {"en": "Local MCP", "zh-TW": "本機 MCP"}, {"en": "Local-only architecture", "zh-TW": "僅限本機的架構"}),
    Route("status", {"en": "Status", "zh-TW": "狀態"}, {"en": "Evidence and boundaries", "zh-TW": "證據與邊界"}),
)
```

Implement `site/build.py` with:

- `parse_args() -> argparse.Namespace` requiring optional `--output`;
- `route_path(output: Path, locale: str, slug: str) -> Path`;
- `render_page(route: Route, locale: str) -> str`;
- `build(output: Path) -> dict[str, object]`;
- sorted writes, UTF-8, LF endings and no build timestamp;
- `shutil.copyfile` for `styles.css` and `app.js`;
- complete removal of only the caller-selected output directory before generation.

Add to `.gitignore`:

```gitignore
site/dist/
site/node_modules/
site/.wrangler/
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run:

```powershell
python -m unittest discover -s tests -p test_site_build.py -v
```

Expected: PASS for route existence, deterministic bytes and JSON parsing.

- [ ] **Step 5: Commit the compiler foundation**

```powershell
git add .gitignore site tests/test_site_build.py
git commit -m "Add deterministic APR site compiler"
```

---

### Task 2: Bilingual pages, evidence-grounded content and visual system

**Files:**

- Modify: `site/src/content.py`
- Modify: `site/build.py`
- Modify: `site/src/assets/styles.css`
- Modify: `tests/test_site_build.py`

**Interfaces:**

- Consumes: `content.ROUTES`, APR repository source links and fixed `SITE` metadata.
- Produces: equivalent EN/zh-TW navigation and factual identifiers on every route.
- Produces: `render_page()` with canonical, alternate-language, Open Graph and accessible navigation metadata.

- [ ] **Step 1: Add failing parity, provenance and accessibility tests**

Add tests that assert:

```python
def test_locales_share_route_and_evidence_identifiers(self):
    # Import content through importlib.util from site/src/content.py.
    self.assertEqual(set(content.PAGES["en"]), set(content.PAGES["zh-TW"]))
    for slug in content.PAGES["en"]:
        self.assertEqual(
            content.PAGES["en"][slug]["evidence_ids"],
            content.PAGES["zh-TW"][slug]["evidence_ids"],
        )

def test_pages_have_canonical_language_and_skip_navigation(self):
    # Build to a temporary directory first.
    self.assertIn('hreflang="zh-Hant"', english)
    self.assertIn('lang="zh-Hant"', chinese)
    self.assertIn('class="skip-link"', english)
    self.assertIn('id="main"', english)

def test_public_copy_does_not_claim_open_source_or_production_readiness(self):
    joined = "\n".join(path.read_text(encoding="utf-8") for path in output.rglob("*.html"))
    self.assertNotIn("production-ready", joined.lower())
    self.assertNotIn("open-source licence", joined.lower())
```

- [ ] **Step 2: Run tests and confirm the new assertions fail**

Run:

```powershell
python -m unittest discover -s tests -p test_site_build.py -v
```

Expected: FAIL because `PAGES`, evidence IDs and full metadata do not exist.

- [ ] **Step 3: Implement the six page families**

Add `PAGES` entries for:

- overview: APR definition, Perceive → Verify → Recover loop and current research status;
- runtime: evidence/event/belief separation, need graph, budget, action gate, outcome and recovery;
- lab: control labels, output labels and educational-projection notice;
- papers: APR-01–APR-07, unified whitepaper and three ACR root documents;
- MCP: local-only stdio/loopback architecture, human allowlist authority and `not_implemented` badge;
- status: v0.10, test/evidence references, Draft PR truth, licence status and non-claims.

Use repository-relative source identifiers, for example:

```python
EVIDENCE = {
    "runtime_architecture": "docs/runtime/ARCHITECTURE.md",
    "action_gate": "docs/runtime/ACTION_READINESS_GATES.md",
    "recovery": "docs/runtime/CLOSED_LOOP_RECOVERY.md",
    "whitepaper": "docs/theory/WHITEPAPER_APR_Runtime_v1.0.md",
}
```

`build.py` must turn these into immutable GitHub links rooted at `https://github.com/kakon77777-commits/APR/blob/{SITE['source_ref']}/`. Task 7 updates `source_ref` to the accepted merge commit before production deployment. Until then, status copy says the site is a release candidate and links to the immutable candidate commit.

Implement the CSS tokens and layout described by the spec:

```css
:root {
  color-scheme: dark light;
  --canvas: #07090d;
  --surface: #10151d;
  --ink: #f2f6fb;
  --muted: #a7b0bd;
  --line: #27313d;
  --observe: #4cd8e8;
  --budget: #f5c451;
  --uncertain: #a78bfa;
  --verified: #59d88e;
  --danger: #ff6b8a;
  --shell: 72rem;
}
```

Add visible focus, reduced-motion behavior, a 40 px minimum control height, responsive one-column layout and text labels beside every colour state.

- [ ] **Step 4: Run the site build tests**

Run:

```powershell
python -m unittest discover -s tests -p test_site_build.py -v
```

Expected: PASS with equal route/evidence identities in both languages.

- [ ] **Step 5: Commit bilingual content and styling**

```powershell
git add site tests/test_site_build.py
git commit -m "Add bilingual APR research pages"
```

---

### Task 3: Export the deterministic APR scenario matrix

**Files:**

- Create: `site/src/demo_export.py`
- Create: `tests/test_site_demo.py`
- Modify: `site/build.py`

**Interfaces:**

- Produces: `DemoScenarioInput.key() -> str`.
- Produces: `export_scenarios() -> dict[str, dict[str, object]]` containing exactly 64 entries.
- Produces: generated `data/demo-scenarios.json` with schema `apr-demo-scenarios/v1`.
- Consumes: `APRRuntime`, `ActionReadinessGate`, `PolicyController`, `WorldState` and deterministic `SimulatorAdapter` fixtures.

- [ ] **Step 1: Write the failing scenario contract tests**

```python
# tests/test_site_demo.py
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "site/src/demo_export.py"


class SiteDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("apr_site_demo_export", MODULE_PATH)
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def test_matrix_covers_every_control_combination(self):
        matrix = self.module.export_scenarios()
        self.assertEqual(64, len(matrix))
        self.assertEqual(64, len(set(matrix)))

    def test_known_fresh_low_risk_fact_skips_observation(self):
        row = self.module.evaluate_scenario(self.module.DemoScenarioInput(
            freshness="fresh", uncertainty="low", risk="low",
            conflict="absent", budget="available", goal="satisfied",
        ))
        self.assertEqual("no_observation", row["disposition"])
        self.assertEqual("allow", row["action_readiness"])

    def test_conflict_blocks_action_and_requests_revisit(self):
        row = self.module.evaluate_scenario(self.module.DemoScenarioInput(
            freshness="fresh", uncertainty="low", risk="high",
            conflict="present", budget="available", goal="satisfied",
        ))
        self.assertEqual("revisit", row["disposition"])
        self.assertEqual("block", row["action_readiness"])

    def test_export_has_no_sensitive_or_unbounded_fields(self):
        encoded = json.dumps(self.module.export_scenarios(), sort_keys=True)
        for forbidden in ("pointer", "path", "token", "credential", "raw_response", "evidence_id"):
            self.assertNotIn(forbidden, encoded.lower())
```

- [ ] **Step 2: Run the demo tests and verify failure**

Run:

```powershell
python -m unittest discover -s tests -p test_site_demo.py -v
```

Expected: FAIL because `demo_export.py` does not exist.

- [ ] **Step 3: Implement the scenario exporter using APR core**

Define:

```python
from dataclasses import dataclass
from itertools import product
from typing import Literal


@dataclass(frozen=True)
class DemoScenarioInput:
    freshness: Literal["fresh", "stale"]
    uncertainty: Literal["low", "high"]
    risk: Literal["low", "high"]
    conflict: Literal["absent", "present"]
    budget: Literal["available", "exhausted"]
    goal: Literal["unresolved", "satisfied"]

    def key(self) -> str:
        return ":".join((self.freshness, self.uncertainty, self.risk,
                         self.conflict, self.budget, self.goal))
```

`evaluate_scenario(input)` must:

1. construct a fresh `EvidenceStore`, `WorldState`, two deterministic channel profiles and `APRRuntime`;
2. represent `goal=satisfied` with supporting value `True`, otherwise leave the fact unknown;
3. apply confidence `0.95` for low uncertainty and `0.40` for high uncertainty;
4. force stale state with `ttl=0.0` and an old `last_verified` value;
5. create contradiction by revising two confidence-`0.95` values from independent sensor and vision sources;
6. map low/high risk to `0.25`/`0.90`;
7. map available/exhausted budget to `10.0`/`0.0` units;
8. call `runtime.decide(Goal("demo.ready", risk=0.90 if input.risk == "high" else 0.25, min_confidence=0.80))`;
9. call `runtime.budget_controller.affordable(action)` without executing the observation;
10. evaluate `ActionReadinessGate` with an `ActionSpec` requiring `demo.ready=True`;
11. serialize only stable enums, bounded numbers, translated reason keys and evidence counts.

Use a structured channel with reliability `0.99`, cost `1.0` and directness `1.0`, plus a vision channel with reliability `0.95`, cost `5.0` and directness `0.65`. Both use `SimulatorAdapter`; no semantic inspector or image generator is constructed.

Return this exact public row shape:

```python
{
    "scenario_key": input.key(),
    "disposition": action.mode.value,
    "reason_key": reason_key(action),
    "effective_fact_status": world.get("demo.ready").status.value,
    "selected_channel": action.modality.value if action.modality else None,
    "expected_gain": round(action.expected_gain, 3),
    "estimated_cost": round(action.estimated_cost, 3),
    "budget_before": round(runtime.budget.remaining, 3),
    "projected_budget_after": round(
        runtime.budget.remaining - action.estimated_cost
        if affordable and action.mode != ReadingMode.NO_OBSERVATION
        else runtime.budget.remaining,
        3,
    ),
    "affordable": affordable,
    "action_readiness": gate_decision.kind.value,
    "facts_to_verify": list(gate_decision.facts_to_verify),
    "blocking_facts": list(gate_decision.blocking_facts),
}
```

Precedence is explicit: contradiction overrides freshness and uncertainty; absent goal evidence remains unknown; stale applies only when evidence exists. Every row includes `effective_fact_status` so visually duplicated input combinations remain honest.

`site/build.py` writes:

```json
{
  "schema": "apr-demo-scenarios/v1",
  "runtime_version": "0.10.0",
  "controls": ["freshness", "uncertainty", "risk", "conflict", "budget", "goal"],
  "scenarios": {}
}
```

using sorted keys and compact deterministic JSON.

- [ ] **Step 4: Run focused demo and compiler tests**

Run:

```powershell
python -m unittest discover -s tests -p "test_site_*.py" -v
```

Expected: PASS; exactly 64 rows and no forbidden fields.

- [ ] **Step 5: Commit the APR-backed fixture exporter**

```powershell
git add site/src/demo_export.py site/build.py tests/test_site_demo.py
git commit -m "Add APR-backed offline lab fixtures"
```

---

### Task 4: Implement the browser-only interactive lab

**Files:**

- Modify: `site/src/assets/app.js`
- Modify: `site/src/assets/styles.css`
- Modify: `site/build.py`
- Modify: `tests/test_site_build.py`

**Interfaces:**

- Consumes: same-origin `/data/demo-scenarios.json` once at page load.
- Produces: `scenarioKey(state)`, `renderScenario(row)` and accessible form state.
- Produces no network request other than same-origin static assets.

- [ ] **Step 1: Add failing static client-boundary tests**

Add assertions that generated `lab/index.html` contains six labelled controls, one `aria-live="polite"` result region and the educational-projection notice. Add a JavaScript source test:

```python
def test_client_has_no_remote_or_local_runtime_endpoint(self):
    script = (ROOT / "site/src/assets/app.js").read_text(encoding="utf-8")
    for forbidden in ("localhost", "127.0.0.1", "api.openai.com", "anthropic.com", "aiplatform.googleapis.com"):
        self.assertNotIn(forbidden, script)
    self.assertIn("/data/demo-scenarios.json", script)
```

- [ ] **Step 2: Run the site build tests and verify failure**

Run:

```powershell
python -m unittest discover -s tests -p test_site_build.py -v
```

Expected: FAIL because the lab controls and client lookup are absent.

- [ ] **Step 3: Implement locale-neutral lab behavior**

Use data attributes emitted by `build.py`:

```html
<form data-apr-lab data-locale="en">
  <fieldset data-control="freshness"><legend>Evidence freshness</legend><label><input type="radio" name="freshness" value="fresh" checked>Fresh</label><label><input type="radio" name="freshness" value="stale">Stale</label></fieldset>
  <fieldset data-control="uncertainty"><legend>Uncertainty</legend><label><input type="radio" name="uncertainty" value="low" checked>Low</label><label><input type="radio" name="uncertainty" value="high">High</label></fieldset>
  <fieldset data-control="risk"><legend>Action risk</legend><label><input type="radio" name="risk" value="low" checked>Low</label><label><input type="radio" name="risk" value="high">High</label></fieldset>
  <fieldset data-control="conflict"><legend>Evidence conflict</legend><label><input type="radio" name="conflict" value="absent" checked>Absent</label><label><input type="radio" name="conflict" value="present">Present</label></fieldset>
  <fieldset data-control="budget"><legend>Observation budget</legend><label><input type="radio" name="budget" value="available" checked>Available</label><label><input type="radio" name="budget" value="exhausted">Exhausted</label></fieldset>
  <fieldset data-control="goal"><legend>Goal evidence</legend><label><input type="radio" name="goal" value="unresolved" checked>Unresolved</label><label><input type="radio" name="goal" value="satisfied">Satisfied</label></fieldset>
  <output data-lab-output aria-live="polite"></output>
</form>
```

Implement in `app.js`:

```javascript
const CONTROL_ORDER = ['freshness', 'uncertainty', 'risk', 'conflict', 'budget', 'goal'];

export function scenarioKey(state) {
  return CONTROL_ORDER.map((name) => state[name]).join(':');
}

export function renderScenario(output, row, labels) {
  const list = document.createElement('dl');
  for (const field of ['disposition', 'reason_key', 'effective_fact_status',
    'selected_channel', 'budget_before', 'projected_budget_after',
    'affordable', 'action_readiness']) {
    const term = document.createElement('dt');
    term.textContent = labels[field];
    const detail = document.createElement('dd');
    detail.textContent = String(row[field]);
    list.append(term, detail);
  }
  output.replaceChildren(list);
}
```

Do not use `innerHTML` for scenario data. Load `app.js` with `type="module"`. Fetch only `/data/demo-scenarios.json`, verify its schema, fail visibly when a key is absent, and make the default state render without user interaction.

CSS must preserve visible labels, 40 px controls, keyboard focus, reduced motion and responsive one-column output.

- [ ] **Step 4: Run site tests**

Run:

```powershell
python -m unittest discover -s tests -p "test_site_*.py" -v
```

Expected: PASS with no local/Provider endpoint strings.

- [ ] **Step 5: Commit the offline lab UI**

```powershell
git add site tests/test_site_build.py
git commit -m "Add interactive offline APR lab"
```

---

### Task 5: Machine discovery, static security and Cloudflare packaging

**Files:**

- Create: `site/public/_headers`
- Create: `site/package.json`
- Create: `site/wrangler.jsonc`
- Modify: `site/build.py`
- Modify: `tests/test_site_build.py`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `STATUS.md`

**Interfaces:**

- Produces: `/llms.txt`, `/ai/site.json`, `/sitemap.xml`, `/robots.txt`, `/404.html`, `/_headers`.
- Produces: `npm run build`, `npm run deploy:dry`, `npm run deploy` inside `site/`.
- Produces: assets-only Cloudflare service `apr-evemisslab` with custom domain `apr.evemisslab.com`.

- [ ] **Step 1: Add failing machine and security artifact tests**

```python
def test_machine_surfaces_and_security_headers_exist(self):
    for relative in ("llms.txt", "ai/site.json", "sitemap.xml", "robots.txt", "404.html", "_headers"):
        self.assertTrue((output / relative).is_file(), relative)
    headers = (output / "_headers").read_text(encoding="utf-8")
    self.assertIn("Content-Security-Policy:", headers)
    self.assertIn("default-src 'self'", headers)
    self.assertIn("connect-src 'self'", headers)

def test_generated_artifact_has_no_windows_absolute_path(self):
    joined = b"\n".join(path.read_bytes() for path in output.rglob("*") if path.is_file())
    self.assertNotRegex(joined.decode("utf-8", errors="ignore"), r"[A-Za-z]:\\")
```

- [ ] **Step 2: Run the compiler tests and verify failure**

Run:

```powershell
python -m unittest discover -s tests -p test_site_build.py -v
```

Expected: FAIL because machine/security files are incomplete.

- [ ] **Step 3: Generate discovery and security files**

`site/public/_headers`:

```text
/*
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors 'none'
  Referrer-Policy: no-referrer
  X-Content-Type-Options: nosniff
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
```

Generate `llms.txt` and `site.json` from the same `content.py` identifiers as human pages. Generate canonical absolute URLs in the sitemap. Render `/404.html` with concise English and Traditional Chinese recovery text, links to both locale roots and `noindex` metadata; do not include it in the sitemap.

`site/build.py` must recursively copy `site/public/` into the selected output after rendering generated files and must reject any source/public collision instead of silently overwriting it.

`site/package.json`:

```json
{
  "name": "apr-evemisslab-site",
  "private": true,
  "version": "0.10.0",
  "scripts": {
    "build": "python build.py",
    "deploy:dry": "npm run build && wrangler deploy --dry-run",
    "deploy": "npm run build && wrangler deploy"
  },
  "devDependencies": {
    "wrangler": "4.92.0"
  }
}
```

`site/wrangler.jsonc`:

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "apr-evemisslab",
  "compatibility_date": "2026-08-24",
  "assets": {
    "directory": "./dist",
    "binding": "ASSETS",
    "not_found_handling": "404-page"
  },
  "routes": [
    { "pattern": "apr.evemisslab.com", "custom_domain": true }
  ]
}
```

Update docs with local build, static preview, no-Provider boundary and the fact that production deployment remains separately authorized.

- [ ] **Step 4: Run website tests and package checks**

Run only after the user lifts the no-test boundary:

```powershell
python -m unittest discover -s tests -p "test_site_*.py" -v
Push-Location site
npm install
npm run deploy:dry
Pop-Location
```

Expected: all site tests PASS; Wrangler reports an assets-only dry run and no binding or secret.

- [ ] **Step 5: Commit the deployment package**

```powershell
git add site/package.json site/package-lock.json site/wrangler.jsonc site/public site/build.py README.md docs/README.md STATUS.md tests/test_site_build.py
git commit -m "Package APR static site for Cloudflare"
```

---

### Task 6: Add APR to the `evemisslab.com` bilingual index

**Files:**

- Create: `D:\Ai\網站群\evemisslab\tests\test_apr_entry.py`
- Modify: `D:\Ai\網站群\evemisslab\src\content.py`
- Modify: `D:\Ai\網站群\evemisslab\src\assets\styles.css`

**Interfaces:**

- Produces: exactly one `host="apr"` entry in each `GROUPS["en"]` and `GROUPS["zh"]` working-systems group.
- Produces: exactly three `--t-apr` declarations: one light and two equivalent dark declarations, matching the existing stylesheet structure.
- Consumes: live child URL `https://apr.evemisslab.com/` only after Task 7 deploy verification.

- [ ] **Step 1: Create an isolated parent-index branch and failing tests**

From `D:\Ai\網站群\evemisslab`, create branch `agent/add-apr-index`, then add:

```python
# tests/test_apr_entry.py
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import content  # noqa: E402


def entries(language):
    return [site for group in content.GROUPS[language]
            for site in group["sites"] if site["host"] == "apr"]


class AprIndexTests(unittest.TestCase):
    def test_both_languages_have_one_apr_entry(self):
        self.assertEqual(1, len(entries("en")))
        self.assertEqual(1, len(entries("zh")))
        self.assertEqual("apr", entries("en")[0]["tone"])
        self.assertEqual("apr", entries("zh")[0]["tone"])

    def test_rendered_pages_link_to_apr(self):
        subprocess.run([sys.executable, "-B", "build.py"], cwd=ROOT, check=True)
        for relative in ("dist/index.html", "dist/zh/index.html"):
            rendered = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("https://apr.evemisslab.com/", rendered)

    def test_apr_tone_exists_in_light_and_dark_palettes(self):
        css = (ROOT / "src/assets/styles.css").read_text(encoding="utf-8")
        self.assertEqual(3, css.count("--t-apr:"))
        self.assertRegex(css, r"--t-apr:\s+#[0-9a-f]{6}")
```

- [ ] **Step 2: Run the focused parent test and verify failure**

Run:

```powershell
python -m unittest discover -s tests -p test_apr_entry.py -v
```

Expected: FAIL because APR is not indexed.

- [ ] **Step 3: Add matching bilingual entries and colour tokens**

Add to the `Working systems` language groups:

```python
{
    "host": "apr", "name": "APR", "tone": "apr",
    "what": "A runtime for deciding when an agent should observe, what it should read, how deeply it should read, when it must reobserve, and when fresh evidence means it should stop reading.",
    "meta": "Research MVP · v0.10",
}
```

```python
{
    "host": "apr", "name": "APR", "tone": "apr",
    "what": "一套決定代理何時應觀察、該讀什麼、讀多深、何時必須重看，以及何時因證據仍新鮮而停止閱讀的 Runtime。",
    "meta": "研究型 MVP · v0.10",
}
```

Use a cyan-derived APR tone that clears WCAG AA as text on the root site's light and dark papers. Preserve the existing duplicated `--t-mmrf` line as unrelated user history.

- [ ] **Step 4: Run parent tests and build**

Run:

```powershell
python -m unittest discover -s tests -v
python -B build.py
```

Expected: existing Axioglyph tests and new APR tests PASS; the build reports equal bilingual site counts.

- [ ] **Step 5: Commit only the parent-index change**

```powershell
git add src/content.py src/assets/styles.css tests/test_apr_entry.py
git commit -m "Add APR to EveMissLab index"
```

Do not deploy or merge this branch until the APR child site is live and verified.

---

### Task 7: Full validation, integration and publication gate

**Files:**

- Modify after measured results: `STATUS.md`
- Modify after measured results: `site/src/content.py`
- Generated only: `site/dist/`
- Generated only in parent repo: `dist/`

**Interfaces:**

- Consumes: all completed tasks and explicit permission to test/deploy.
- Produces: validated APR PR, live `apr.evemisslab.com`, validated parent-index PR and live root link.

- [ ] **Step 1: Resolve the runtime baseline before claiming canonical `main` links**

Inspect Draft PR #1 and current `origin/main`. Re-run its documented validation. If accepted, merge it first or rebase the website branch onto an equivalent reviewed main commit. Update site status metadata from `release_candidate` to `merged` only after GitHub confirms the merge.

- [ ] **Step 2: Run complete APR validation without live Providers**

```powershell
python -m unittest discover -s tests -v
python -m pytest
ruff format --check apr_runtime tests examples site
ruff check apr_runtime tests examples site
python -m build
Push-Location site
npm run build
npm run deploy:dry
Pop-Location
```

Expected: all offline tests and package checks PASS. No command may set or use Provider credentials.

- [ ] **Step 3: Scan the candidate and generated artifact**

Scan tracked files and `site/dist` for common API-key/private-key forms, bearer tokens, service-account fields, Windows absolute paths, `localhost`, `127.0.0.1` and Provider endpoints. Any hit in generated public output blocks publication until removed or proven to be an explicitly safe explanatory string outside executable/client configuration.

- [ ] **Step 4: Perform browser acceptance only when the user says the computer is available**

Serve `site/dist` on a loopback ephemeral port. Verify both locales and all six route families at desktop and mobile widths. Exercise every lab control combination class, keyboard navigation, visible focus, reduced motion, 404, `llms.txt` and `site.json`. Record warnings, errors and network requests. Acceptance requires zero console errors and zero requests outside the loopback origin.

- [ ] **Step 5: Commit measured status and publish the APR PR**

Update `STATUS.md` and website status copy with the exact observed test count, commit SHA and evidence boundaries. Regenerate the site and re-run focused tests. Commit:

```powershell
git add STATUS.md site tests
git commit -m "Finalize APR site evidence"
```

Push the APR branch and open a Draft PR. Wait for CI; inspect failures before marking ready. Merge only a clean, current head SHA.

- [ ] **Step 6: Deploy the child site after explicit production permission**

From the merged APR `main`:

```powershell
Push-Location site
npm run deploy
Pop-Location
```

Verify live status and body semantics at `/`, `/zh-TW/`, `/lab/`, `/zh-TW/lab/`, `/llms.txt`, `/ai/site.json` and a nonexistent route. Confirm the custom domain is `apr.evemisslab.com` and no Worker binding or secret exists.

- [ ] **Step 7: Publish the parent-index PR only after child verification**

Rebase `agent/add-apr-index` on current parent `main`, rerun all parent tests, push, open a Draft PR and wait for CI. Merge it, then use the existing parent repository `deploy.sh` so Cloudflare Pages retains the apex custom domain. Verify both `https://evemisslab.com/` and `/zh/` link to the live APR child.

- [ ] **Step 8: Final handoff**

Report:

- APR and parent merge commit SHAs;
- both PR URLs and CI conclusions;
- exact test counts;
- deployed Worker and Pages versions;
- live English/Chinese route checks;
- browser console/network result;
- the remaining deferred scope: local MCP and guarded desktop/browser control.
