# APR Runtime Status

## Current release

**v0.10.0 — 0.x engineering convergence / locally accepted public-site release candidate**

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

## Not claimed by this status

- production readiness;
- a merge of Draft PR #1; runtime evidence `source_ref` remains
  `d1722eca845353acd3ce1f7241283bfa16263e93`, and final-fix wave 2 did not
  inspect or mutate remote PR/CI state;
- a live deployment of `apr.evemisslab.com`; only exact-head local build/Node validation and
  Wrangler dry-run packaging, plus earlier local-browser evidence, have been recorded. Production
  headers and custom-domain behavior remain unverified;
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
