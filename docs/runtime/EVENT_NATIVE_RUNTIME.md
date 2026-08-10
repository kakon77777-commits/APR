# Event-Native Runtime — APR v0.5

## Core invariant

```text
NativeEvent != Evidence != WorldState
```

A native event tells APR where information may have changed.
A targeted read verifies it.
Only verified evidence changes the persistent belief state.

## Browser route

```text
CDP event
 -> EventLedger
 -> nodeId/backendNodeId
 -> TargetedBrowserReader
 -> DOM.describeNode
 -> DOM.getOuterHTML
 -> Accessibility.getPartialAXTree
 -> Evidence
 -> WorldState
```

## Document lifecycle

`DOM.documentUpdated` invalidates old frontend node IDs.
APR increments a document generation counter and reseeds the document before
further targeted reads.

## Windows route

```text
SetWinEventHook
 -> HWND
 -> EventLedger
 -> bounded UIA subtree
 -> Evidence
 -> WorldState
```

## Why polling remains

Event systems can be noisy, incomplete or lossy. APR keeps periodic polling as
a recovery and consistency-check mechanism.

## Persistent Event Ledger

Events are append-only and searchable by kind, target, significance and time.
Low-significance old events may be compacted while preserving high-value
historical events.
