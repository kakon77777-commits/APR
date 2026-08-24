# Changelog

All notable changes to this repository are documented here.

## [Unreleased]

### Added

- Standalone repository structure for theory, papers, runtime documentation, examples, and tests.
- Explicit `apr_runtime.plugins` registry and `apr_runtime.plugins` Python entry-point group.
- Transactional plugin installation, duplicate protection, strict loading, and structured failure reports.
- Core numeric and identity validation for evidence, goals, actions, budgets, channel profiles, and TTL values.
- CI, package metadata, citation metadata, security guidance, and source provenance manifest.
- Standard-library OpenAI Responses and Anthropic Messages semantic-inspector components, exposed through an explicit built-in plugin.
- A bounded cross-provider visual smoke test with structured facts, token/cost reporting, and a synthetic destructive-confirmation fixture.
- A provider-neutral image-generation protocol and an explicit Google Vertex image-generator plugin with lazy OAuth authentication, bounded outputs, truthful MIME persistence, provenance hashes, and usage/cost metadata.
- A real Vertex 1K image-generation experiment with a committed final visual artifact and human prompt-adherence review.
- A bilingual Why APR plain-language guide that explains the multimodal Token, latency, API-cost, context-pressure, and scaling case without inventing a universal savings percentage.

### Changed

- Unified Python formatting and import ordering across the cumulative runtime.
- Completed the package-level `__all__` export list while preserving existing direct imports.
- Removed generated cache files and the empty `tests/test_task_runtime.py.tmp` artifact from the integrated tree.
- Moved semantic fact volatility and TTL out of model output and into deterministic inspector configuration.
- Added canonical candidate labels to the cross-provider experiment so equivalent concepts merge consistently without disclosing ground truth.
- Added an optional `vertex` dependency group for Google Application Default Credentials while keeping the core runtime dependency-free.
- Added a visually primary Why APR homepage entry while preserving the professional technical site and explicitly separating visual-causal-projection theory from implemented v0.10 capabilities.

### Fixed

- Negative perceptual costs can no longer credit a budget or bypass affordability checks.
- Failed plugin registration no longer leaves partially registered components behind.
- Vertex image output no longer assumes SDK-only REST fields, regional catalog visibility, or PNG responses; live failures now drive global routing and validated PNG/JPEG persistence.

## [0.10.0] - 2026-08-09

- Closed-loop recovery orchestration.
- Retry lineage, compensation, idempotency guards, cooperative timeout/cancellation, and trace export.
- Cumulative v0.1–v0.9 belief, stream, semantic evidence, revisit, event, scheduler, need-graph, action-gate, and outcome capabilities.

See `docs/releases/` for the version-by-version engineering notes.
