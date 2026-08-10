# Action Outcome Verification — APR Runtime v0.9

## Invariant

```text
Expected state != observed state
```

An action contract may declare what should happen. APR must still observe the
world after execution.

## Verification rule

By default, matching state supported only by evidence older than the action
returns:

```text
VERIFY
```

not:

```text
SUCCESS
```

## Decisions

```text
SUCCESS
VERIFY
RETRY
REPLAN
ROLLBACK
FAILED
```

## Postcondition example

```python
PostconditionRequirement(
    "door.state",
    expected_values=("open",),
    min_confidence=0.9,
    must_change_from_pre_state=True,
)
```

## Evidence provenance

Every completed execution may be linked to evidence IDs in the Execution
Ledger.

This makes success auditable:

```text
execution -> post-action evidence -> postconditions
```
