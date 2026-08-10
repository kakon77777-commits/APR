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

### Changed

- Unified Python formatting and import ordering across the cumulative runtime.
- Completed the package-level `__all__` export list while preserving existing direct imports.
- Removed generated cache files and the empty `tests/test_task_runtime.py.tmp` artifact from the integrated tree.
- Moved semantic fact volatility and TTL out of model output and into deterministic inspector configuration.
- Added canonical candidate labels to the cross-provider experiment so equivalent concepts merge consistently without disclosing ground truth.

### Fixed

- Negative perceptual costs can no longer credit a budget or bypass affordability checks.
- Failed plugin registration no longer leaves partially registered components behind.

## [0.10.0] - 2026-08-09

- Closed-loop recovery orchestration.
- Retry lineage, compensation, idempotency guards, cooperative timeout/cancellation, and trace export.
- Cumulative v0.1–v0.9 belief, stream, semantic evidence, revisit, event, scheduler, need-graph, action-gate, and outcome capabilities.

See `docs/releases/` for the version-by-version engineering notes.
