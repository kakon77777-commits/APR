# APR Runtime Status

## Current release

**v0.10.0 — 0.x engineering convergence / live public research site / runtime release candidate**

The original cumulative v0.10 snapshot has been integrated into a standalone repository and hardened as reusable research infrastructure.

## Verified locally

- 178/178 offline Python unit and integration-style tests under both unittest and pytest,
  plus 101 passing pytest subtests;
- 9/9 dependency-free Node client-behavior tests;
- deterministic bilingual static-site output, machine discovery, restrictive static headers,
  a production publication validator, fail-closed transactional replacement, and an
  entrypoint-free Wrangler 4.125.0 assets-only dry run with no bindings; Wrangler reports 36
  entries while the filesystem census is separately 22 files plus 14 directories;
- package import and explicit public export surface;
- transactional plugin registration and entry-point failure reporting;
- finite/range validation for core confidence, risk, TTL, cost, and budget values;
- UTF-8 integrity across source, theory, papers, and runtime documentation;
- source distribution and wheel build;
- synthetic closed-loop recovery demonstration;
- bounded live OpenAI/Anthropic semantic-inspector validation on one generated destructive-confirmation fixture, including structured evidence ingestion and reported token/cost metadata.
- bounded live Google Vertex image generation at `global`, including a persisted 1K JPEG, byte-level format validation, usage/cost metadata, and human visual inspection.
- prior locally accepted browser evidence on Python's local static server: readable EN/ZH home and
  Lab, MCP and 404 pages; correct Lab transition cases; 390×844 without horizontal overflow;
  same-origin resources; and 0 console warnings/errors after the scoped favicon fix
  (`/favicon.svg` 200 and no `/favicon.ico`). Browser evidence was not rerun at the final-fix
  wave-2 HEAD;
  see [`docs/experiments/APR_PUBLIC_SITE_ACCEPTANCE_2026-08-24.md`](docs/experiments/APR_PUBLIC_SITE_ACCEPTANCE_2026-08-24.md).

## Repository integration

- Runtime/provider baseline PR #1 is merged as
  `60d3f9caeca9b1a8e555a6a580cd7cf238402aa5`.
- Public evidence links are pinned to that immutable merge commit.
- Public-site PR #2 is merged as `64cefe270f55b31bf684145105342fbd57e8116b`.
- The production RUM-blocking fix is merged as
  `b7bb18b077b67a1339e3bb811ce091c58b1a7052`.
- The parent `evemisslab.com` APR index is merged as
  `f3c34a78322ed061ed4834ca7925656ff8683b32`.

## Published website verification

- `apr.evemisslab.com` is live on Cloudflare Worker version
  `6b32fb1f-392b-4574-8887-4b9ee26c43e5`.
- EN/ZH routes, Lab routes, MCP, status, `llms.txt`, `ai/site.json`, and a 404 route returned
  their expected production status codes.
- Production responses carried the restrictive CSP, `nosniff`, no-referrer,
  Permissions-Policy, and `Cache-Control: public, max-age=0, must-revalidate, no-transform`.
- Exact live Chrome verification at 390×844 observed same-origin resources only, reduced-motion
  preference, no horizontal overflow, correct default and conflict/exhausted Lab transitions,
  and zero console warnings/errors.
- `evemisslab.com/` and `/zh/` each expose one APR link after the parent Pages deployment.

## Not claimed by this status

- production readiness;
- continuous availability, an uptime guarantee, or a hosted APR runtime/API behind the static site;
- empirical proof of the full APR theory;
- broad or repeated live VLM/image-generation validation, and any live audio, sensor, or robot validation;
- unattended high-risk desktop/browser action safety;
- distributed durability, authentication, authorization, or process isolation;
- benchmark superiority over full-processing baselines.

## Next tracks

1. Live integration validation on isolated desktop and browser fixtures.
2. APR benchmark and ablation suite.
3. Stable v1 service boundaries and persistence migration strategy.
4. Learned routing, value-of-information, and recovery policies.
5. Explicit licensing decision before third-party reuse.
