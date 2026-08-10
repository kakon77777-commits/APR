# Unified Event Scheduler — APR v0.6

## Input channels

```text
Browser CDP native events
Windows WinEvents
screen-delta StreamEvents
semantic events
periodic refresh events
```

## Deduplication

Identical event fingerprint inside `duplicate_window` is counted as duplicate.

## Coalescing

Same source/kind/target/node identity inside `coalesce_window` becomes one work item.

## Priority

```text
base = significance * source_weight
priority_now = base + bounded_age_boost
```

## Backpressure

When queue is full:

```text
critical incoming -> evict lowest
materially higher priority incoming -> evict lowest
low-value incoming -> drop
```

## Periodic refresh

Refreshes enter the same scheduler as synthetic native events.

## Important rule

Event Ledger may persist all received native signals while Scheduler processes a smaller coalesced work set.

```text
historical event fidelity != processing workload size
```
