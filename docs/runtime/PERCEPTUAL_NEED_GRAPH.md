# Perceptual Need Graph — APR v0.7

## Purpose

A task does not require the entire world state. It requires a subset of facts
at sufficient confidence and freshness.

```text
Goal
 -> Required Facts
 -> Dependencies
 -> Current Need State
 -> Refresh / Observe / Revisit
```

## Need states

```text
SATISFIED
UNKNOWN
STALE
UNCERTAIN
CONTRADICTED
BLOCKED
```

## Core distinction

```text
World State = what the agent currently believes
Perceptual Need Graph = what the current task still needs to know
```

## Event routing

Events are mapped to facts they may invalidate. If those facts are active task
needs, the event is boosted before entering the v0.6 scheduler.

## Need-driven perception

A missing or stale need can emit `apr.need.refresh` even if the environment has
not generated a new external event.
