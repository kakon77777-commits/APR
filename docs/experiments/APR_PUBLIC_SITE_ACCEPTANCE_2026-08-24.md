# APR public-site candidate acceptance — 2026-08-24

## Status and evidence scope

**Status:** locally accepted release candidate. This is not a merged or live release.

- Final APR HEAD before this documentation commit: `eb9d1138c4a40403e7d78226c20449e04b3422ab`.
- Runtime evidence `source_ref` remains `d1722eca845353acd3ce1f7241283bfa16263e93`.
- Draft PR #1 was not inspected or mutated during this final-fix pass; the local candidate remains
  unmerged and this record does not claim current remote PR or CI state.
- No Provider call, credential access, live Cloudflare deploy, push, PR mutation, or merge occurred during candidate acceptance.

## Measured local validation

| Gate | Measured result |
| --- | --- |
| Python unittest | 174/174 pass |
| pytest | 174/174 pass; 50 subtests pass |
| Node client behavior | 9/9 pass |
| Node syntax | pass |
| Required Ruff scope `apr_runtime tests examples site` | 107 files formatted; lint pass |
| Python package | sdist/wheel build pass |
| npm audit | 0 vulnerabilities |
| Wrangler | 4.125.0 |
| Installed Wrangler schema | draft-07 parsed by installed Wrangler; assets `./dist`; 1 route; 0 binding groups |
| Wrangler dry-run | Wrangler reports 36 entries after favicon; filesystem census is 22 files + 14 directories; bindings remain 0 and no deployment occurred |
| Generated site | two builds share manifest SHA-256 `12d73e38a8ccf8a95a431eb14f10529a3b36aa4a318a88212637a17d65d5d331`; 12/12 bilingual routes; 64/64 scenarios; public leakage scan 0 |

Repository-wide Ruff over Markdown code fences is not the release gate and is not reported as a failure. The required scoped Ruff gate is green.

## Parent candidate evidence

The parent candidate is `327859162a3bb8e9e1ad0ba9c4c2e0aef1d6acf8`: 6/6 tests, 2 pages,
18 EN/18 ZH sites, and it is not merged or deployed. The parent index commits exist only on
their local branch.

## Prior local browser acceptance

The observations below predate final-fix HEAD `eb9d1138c4a40403e7d78226c20449e04b3422ab`.
Browser and desktop automation were explicitly excluded from the final-fix pass, so they remain
historical evidence rather than an exact-head browser claim. Exact-head client behavior is covered
by the 9/9 dependency-free Node tests above.

Browser pass 1 verified readable EN/ZH home, EN/ZH Lab, MCP, and 404 pages. The default Lab state was `search/unknown/structured/10→9/true/verify`; conflict was `revisit/contradicted/block`; exhausted budget was `0→0/false/block`. At 390×844 there was no horizontal overflow; resources were same-origin only; console warnings/errors were 0. This pass found a favicon fallback 404.

The scoped favicon fix `71ba8c0` then passed review. Browser pass 2 observed `/favicon.svg` 200 and no `/favicon.ico`; the home resource inventory was same-origin CSS/JS/favicon; the Lab static JSON result was correct; console warnings/errors were 0.

## Remaining boundaries

- `apr.evemisslab.com` is not yet deployed.
- Exact-head browser behavior was not rerun. Earlier browser acceptance used Python's local static
  server. Production headers and custom-domain behavior remain unverified.
- This record neither merges Draft PR #1 nor changes its `source_ref`; it records measured candidate evidence only.
