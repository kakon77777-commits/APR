# Contributing

APR is currently a research MVP. Keep changes small, evidence-backed, and explicit about whether they affect theory, policy, adapters, or runtime safety.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Before submitting a change, run:

```powershell
ruff format --check apr_runtime tests examples
ruff check apr_runtime tests examples
python -m unittest discover -s tests -v
python -m build
```

## Expectations

- Preserve the distinction between event, evidence, and current belief.
- Do not turn unknown state into false or silently invent post-action evidence.
- New retries or compensations must declare reversibility and idempotency assumptions.
- Add tests for policy, persistence, and failure-path changes.
- Keep optional desktop/browser/provider dependencies out of the dependency-free core.
- State empirical limits plainly; a passing synthetic test is not a live-system benchmark.

Plugin authors should follow `docs/PLUGIN_API.md` and avoid side effects during registration.
