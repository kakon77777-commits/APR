# Evidence Preconditions — APR Runtime v0.8

A FactRequirement can constrain:

```text
min_confidence
max_age
allowed_values
forbidden_values
min_independent_evidence
min_modalities
min_evidence_confidence
require_revisitable_asset
contradiction_blocks
```

## Current state is not enough

A fact can be `KNOWN` but still be insufficient for a specific action.

Example:

```text
fact TTL = 60s
robot move action max_age = 2s
```

The world-state fact remains generally known, but the motion action must
refresh it.

## Action-specific epistemic standards

Different actions can require different confidence for the same fact.

```text
show UI hint:
  min confidence = 0.70

send payment:
  min confidence = 0.95
  independent evidence >= 2
```

The World State remains shared. The action gate owns execution-specific
standards.

## Explicit authorization / singleton channels

Some preconditions are authoritative singleton signals rather than facts that
benefit from source diversity, for example an explicit user confirmation.
Such a requirement can set:

```text
inherit_risk_floor = false
```

and declare its own confidence/evidence threshold. This prevents a global
high-risk diversity rule from manufacturing fake "independence" by asking the
same authority twice.
