# Closed-Loop Recovery — APR Runtime v0.10

## Main loop

```text
Action Gate
  -> Execute
  -> Post-action Observation
  -> Verify Outcome
  -> SUCCESS
     or
     RETRY / REPLAN / COMPENSATE
```

## Retry safety

Automatic retry is not a generic default.

```text
RetryMode.NEVER
RetryMode.IDEMPOTENT
RetryMode.DEDUPLICATED
```

Irreversible actions require deduplicated retry plus an idempotency key.

## Compensation

`rollback` means an explicit compensating action.

The compensating action:
- is separately registered;
- passes its own readiness gate;
- has its own postconditions;
- is itself verified.

## Trace

Every run produces a RecoveryTrace that can be exported to JSON or Markdown.

## Production timeout semantics

The included `RecoveryContext` supports cooperative deadline/cancellation.

External adapters should still use native timeout/cancellation mechanisms for:
- network requests;
- subprocesses;
- robot control;
- browser actions.
