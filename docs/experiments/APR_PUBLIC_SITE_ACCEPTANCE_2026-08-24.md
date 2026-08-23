# APR public-site candidate acceptance — 2026-08-24

## Status and evidence scope

**Status:** locally accepted release candidate. This is not a merged or live release.

- Final APR HEAD before this documentation commit: `71ba8c00de4831c1f0018ddf6a9a2136e163abeb`.
- Runtime evidence `source_ref` remains `d1722eca845353acd3ce1f7241283bfa16263e93`.
- Draft PR #1 remains **OPEN/Draft**, with **3/3 CI success**, clean/mergeable, and **not merged**.
- No Provider call, credential access, live Cloudflare deploy, push, PR mutation, or merge occurred during candidate acceptance.

## Measured local validation

| Gate | Measured result |
| --- | --- |
| Python unittest | 149/149 pass |
| pytest | 149/149 pass |
| Node client behavior | 6/6 pass |
| Node syntax | pass |
| Required Ruff scope `apr_runtime tests examples site` | 106 files formatted; lint pass |
| Python package | sdist/wheel build pass |
| npm audit | 0 vulnerabilities |
| Wrangler | 4.125.0 |
| Wrangler dry-run | 35 assets observed, 0 bindings, no deployment |
| Generated site | deterministic; 12/12 bilingual routes, 64/64 scenarios, public leakage scan 0 |

Repository-wide Ruff over Markdown code fences is not the release gate and is not reported as a failure. The required scoped Ruff gate is green.

## Parent candidate evidence

The parent candidate is `e950753f1ef71812c2da98bde4a4c99ff7865a37`: 6/6 tests, 2 pages, 18 EN/18 ZH sites, and it is not merged or deployed. The parent index commit exists only on its local branch.

## Local browser acceptance

Browser pass 1 verified readable EN/ZH home, EN/ZH Lab, MCP, and 404 pages. The default Lab state was `search/unknown/structured/10→9/true/verify`; conflict was `revisit/contradicted/block`; exhausted budget was `0→0/false/block`. At 390×844 there was no horizontal overflow; resources were same-origin only; console warnings/errors were 0. This pass found a favicon fallback 404.

The scoped favicon fix `71ba8c0` then passed review. Browser pass 2 observed `/favicon.svg` 200 and no `/favicon.ico`; the home resource inventory was same-origin CSS/JS/favicon; the Lab static JSON result was correct; console warnings/errors were 0.

## Remaining boundaries

- `apr.evemisslab.com` is not yet deployed.
- Browser acceptance used Python's local static server. Production headers and custom-domain behavior remain unverified.
- This record neither merges Draft PR #1 nor changes its `source_ref`; it records measured candidate evidence only.
