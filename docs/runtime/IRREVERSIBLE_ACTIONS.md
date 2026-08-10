# Irreversible Actions — APR Runtime v0.10

## Rule

Do not pretend every side effect can be undone.

Classify actions:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
```

## Examples

Potentially irreversible:
- sending a message outside the system;
- publishing externally;
- transferring funds;
- destructive physical manipulation;
- deleting data without recovery;
- triggering a one-shot external process.

## Retry

An irreversible operation is not automatically retried merely because the
postcondition was not observed.

If the external tool supports a real idempotency/deduplication key:

```text
RetryMode.DEDUPLICATED
```

may be explicitly configured.

Otherwise APR returns:

```text
REPLAN_REQUIRED
```

rather than risking duplicated side effects.

## Compensation

A compensating action is not equivalent to restoring history.

Example:

```text
charge card
 -> refund card
```

A refund is a new side effect with its own risks, preconditions, outcome, and
audit trail. It must therefore pass APR gates like any other action.
