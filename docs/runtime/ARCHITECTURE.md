# APR Runtime MVP v0.1 — Architecture

## Control plane

```text
Goal
  ↓
WorldState ←→ EvidenceStore
  ↓
Freshness / Conflict
  ↓
PolicyController
  ├─ ModalityRouter
  ├─ ReadingMode
  └─ Budget
  ↓
Adapter.observe()
  ↓
Evidence
  ↓
WorldState.revise()
```

## Design rule

The MVP intentionally avoids a real VLM.

The code validates the control plane independently from model quality.
A VLM, DOM reader, camera, audio model, or robot sensor is an adapter.

## Current behaviors

- A fresh, high-confidence fact returns `NO_OBSERVATION`.
- A stale / uncertain fact triggers `INSPECT`.
- A contradicted fact triggers `REVISIT`.
- High risk increases perceptual urgency.
- Modality routing uses reliability / cost heuristics.
- Every revision preserves evidence provenance.
- Budget is spent only when an observation is actually executed.
