# Retention Policy — APR v0.6

## Event Ledger

Old events below a significance threshold can be deleted. High-significance events survive longer.

## Evidence Archive

Low-confidence old evidence can be removed, except when its evidence ID is still referenced by the current Persistent World State.

## Asset deletion

An ROI/audio/etc. asset file is deleted only when no remaining evidence row references it.

## Principle

```text
Storage pressure must not silently destroy the provenance of current beliefs.
```
