# Security

## Research-runtime boundary

APR contains action gating and recovery logic, but it is not a security boundary and is not production-ready for unattended high-risk actions.

## Sensitive integrations

- Desktop and browser adapters can observe private on-screen or DOM content.
- Evidence archives, event ledgers, and recovery traces may contain sensitive values or local paths.
- `CommandSemanticInspector` launches the exact argument vector configured by the caller. It does not use a shell, but the configured executable and arguments must still be trusted.
- Python plugin entry points execute third-party Python code when `load_entry_points()` is called. Loading is intentionally explicit; only load trusted distributions.
- Hosted semantic inspectors read `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` lazily from the process environment. Do not pass keys in prompts, config files, command-line arguments, evidence metadata, or committed test fixtures.
- The Google Vertex image generator obtains a short-lived OAuth access token lazily. Keep service-account JSON outside the repository, restrict its IAM role and project scope, and prefer Application Default Credentials or an injected token provider. Common local service-account filenames are ignored, but `.gitignore` is not a substitute for secret scanning or key rotation.
- Compensating actions are new actions, not guaranteed reversal. They must pass the same readiness and outcome checks as ordinary actions.

Use isolated test accounts and disposable fixtures for live validation. Do not commit credentials, captured private evidence, SQLite runtime data, generated traces, or raw hosted responses that may contain private prompts or media.

## Reporting

Use the repository's private security-reporting channel when available. If it is not enabled, contact the repository owner without publishing exploit details in a public issue.
