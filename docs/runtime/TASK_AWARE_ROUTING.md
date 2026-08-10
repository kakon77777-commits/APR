# Task-Aware Event Routing — APR Runtime v0.7

## Core problem

v0.6 can rank event work by event significance, source, age, and queue pressure.
v0.7 adds the missing task dimension:

```text
Which current task fact could this event invalidate?
```

## Data path

```text
Goal / Task
  ↓
Perceptual Need Graph
  ↓
required facts + confidence + risk + dependencies
  ↓
Event-Fact Dependency Map
  ↓
Native Event
  ↓
Task-aware significance
  ↓
Unified Event Scheduler
```

## Perceptual Need Graph

A need is an information contract:

```text
fact_key
minimum confidence
risk
mandatory/optional
prerequisite needs
```

A need can be:

```text
SATISFIED
UNKNOWN
STALE
UNCERTAIN
CONTRADICTED
BLOCKED
```

`BLOCKED` means prerequisite information has not yet been established.

## Event-Fact dependency

Rules describe what an event *may* invalidate. They do not claim the fact is
actually changed.

Example:

```text
browser_dom_changed
  -> download.failed
  -> confirmation.dialog.visible
```

A targeted reader still has to verify the state before World State revision.

## Priority transform

For raw significance `s` and current need relevance `r`:

```text
relevant event:
  s' = s + (1-s) * alpha * r

unrelated non-critical event:
  s' = beta * s
```

Critical raw events retain a floor and are never downweighted below their
source significance.

## Raw history remains raw

Task relevance is transient. Therefore:

```text
Event Ledger
  stores original source significance

Scheduler Work Set
  stores task-aware routed significance
```

This prevents today's task from rewriting the historical meaning of yesterday's
event stream.

## Need-driven refresh

Perception can now be initiated by an information deficit:

```text
required fact is stale / unknown / uncertain / contradicted
  -> apr.need.refresh
```

So APR has both:

```text
environment-driven perception
and
goal-driven perception
```

## Query routing

Current query:

```text
fresh state -> answer from World State
insufficient state -> refresh current
```

Historical query:

```text
archived revisitable evidence -> Historical Revisit
```

## Safety

High-risk needs receive a critical refresh floor. This means a very small raw
event can outrank a visually large but task-irrelevant event if it threatens a
fact required for a high-risk action.
