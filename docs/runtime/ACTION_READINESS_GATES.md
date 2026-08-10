# Action Readiness Gates — APR Runtime v0.8

## Core contract

```text
ActionSpec
  -> FactRequirements[]
  -> ActionReadinessGate
  -> ALLOW / VERIFY / BLOCK
```

## ALLOW

All evidence preconditions are satisfied.

## VERIFY

A fact is unknown, stale, low-confidence, under-evidenced, lacks required
modality diversity, or lacks a revisitable asset.

VERIFY may emit `apr.action.verify` into the APR scheduler.

## BLOCK

The current verified value violates the action's semantic precondition, or a
blocking contradiction exists.

## Important distinction

```text
UNKNOWN != FALSE
```

Unknown should trigger perception.

Verified false should block the action when true is a required precondition.

## Evidence diversity

High-risk actions may require multiple independent evidence groups.

A historical re-read of the same archived image does not count as an
independent source.

## Guarded execution

```python
result = action_runtime.execute("send_payment", do_payment)
```

`do_payment` is called only when the gate returns `ALLOW`.
