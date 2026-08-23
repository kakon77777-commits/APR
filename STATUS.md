# APR Runtime Status

## Current release

**v0.10.0 — 0.x engineering convergence / public-site release candidate**

The original cumulative v0.10 snapshot has been integrated into a standalone repository and hardened as reusable research infrastructure.

## Verified locally

- 148/148 offline Python unit and integration-style tests;
- 6/6 dependency-free Node client-behavior tests;
- deterministic bilingual static-site output, machine discovery, restrictive static headers,
  and an entrypoint-free Wrangler 4.92.0 assets-only dry run with no bindings;
- package import and explicit public export surface;
- transactional plugin registration and entry-point failure reporting;
- finite/range validation for core confidence, risk, TTL, cost, and budget values;
- UTF-8 integrity across source, theory, papers, and runtime documentation;
- source distribution and wheel build;
- synthetic closed-loop recovery demonstration;
- bounded live OpenAI/Anthropic semantic-inspector validation on one generated destructive-confirmation fixture, including structured evidence ingestion and reported token/cost metadata.
- bounded live Google Vertex image generation at `global`, including a persisted 1K JPEG, byte-level format validation, usage/cost metadata, and human visual inspection.

## Not claimed by this status

- production readiness;
- a live deployment of `apr.evemisslab.com`; only local build and Wrangler dry-run packaging
  have been validated;
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
