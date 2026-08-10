# Historical Revisit — APR Runtime v0.4

## Definition

Historical Revisit means re-reading the exact evidence that was available at a
past time.

It differs from current re-observation.

```text
Current re-observation:
  What is true now?

Historical revisit:
  What did this archived evidence actually show then?
```

## Data path

```text
WorldState fact
 -> evidence_ids[]
 -> EvidenceArchive.by_ids()
 -> asset_path
 -> SemanticInspector
 -> SemanticFact
 -> new Evidence
 -> WorldState revision
```

## Provenance

The new evidence contains:

```text
historical_revisit: true
revisit_of: <source evidence id>
source_asset: <archived asset path>
```

The old evidence is not overwritten.

## Use cases

- repair a bad old caption;
- answer a new question about old footage;
- inspect an overlooked detail;
- resolve a contradiction;
- verify why a historical world-state belief was formed.
