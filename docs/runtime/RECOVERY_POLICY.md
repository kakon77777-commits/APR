# Recovery Policy — APR Runtime v0.9

## Decision order

```text
postconditions satisfied
  -> SUCCESS

evidence incomplete and timeout not reached
  -> VERIFY

failure + configured rollback
  -> ROLLBACK

failure + retry-safe + retry budget remains
  -> RETRY

otherwise
  -> REPLAN
```

## Retry is declarative

APR never assumes every action is safe to repeat.

```text
retry_safe = false
```

must be used for non-idempotent or potentially duplicating actions unless the
tool/action layer provides its own idempotency control.

Examples requiring caution:

```text
send payment
submit order
delete resource
send email
physical irreversible manipulation
```

## Rollback is a separate action

`rollback_action_id` identifies a separately registered action. v0.9 returns
the directive; v0.10 should execute rollback through the same readiness and
postcondition gates.
