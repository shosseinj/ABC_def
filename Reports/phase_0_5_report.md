# Phase 0.5 Report — Benchmark Contract

STATUS: PASS

**Date:** 2026-09-20  
**Experiments run:** None

## Phase status

PASS — the benchmark budget contract, deterministic projectors, independent budget auditor, frozen budget grid, and per-sample result schema are implemented and unit-tested. This is implementation readiness, not scientific benchmark evidence.

## Completed tasks

- Added `attacks/benchmark_contract.py`.
- Froze dataset-specific `B∞`, `B1`, and `B0` grids from `AGENT.md`.
- Defined all displacement metrics in native integer timestamp units:
  - `B∞ = max_i |t'_i - t_i|`;
  - `B1 = sum_i |t'_i - t_i|`;
  - `B0 = count_i(t'_i != t_i)`.
- Implemented deterministic projection for each budget independently and for intersections.
- Added optional timestamp-domain bounds; clipping can only reduce displacement.
- Added an independent auditor that recomputes event count, timestamp integrality, domain validity, and realized budgets without calling the projector.
- Added a required per-sample result schema with requested and realized budgets, clean correctness, predictions, attack success, runtime, hashes, and audit status.
- Preserved prior attack implementations and artifacts unchanged.

## Validation results

Command:

```text
C:\Users\jafari.h.SPADANACO\Desktop\ai_project\.venv\Scripts\python.exe -m pytest tests\test_benchmark_contract.py -q
```

Result: `6 passed`.

Validated cases include independent `B∞/B1/B0` enforcement, intersected constraints, timestamp-domain clipping, deterministic ties, explicit violation detection, fail-closed inputs, frozen dataset grids, and schema-level requested-budget checks.

## Metrics and audit contract

Every future record must retain:

- requested budget family and value;
- realized `B∞`, `B1`, and `B0` regardless of the active family;
- clean-correct status, clean/adversarial predictions, and attack success;
- checkpoint and split hashes, runtime, seed, sample ID, and audit outcome.

ASR aggregation remains restricted to clean-correct samples. Phase 1 must preserve a frozen common-clean-correct manifest for paired comparisons.

## Errors and blockers

- The externally supplied v3 directory was unavailable; matching, newer repository-local v3 instructions were used.
- No unresolved Phase 0.5 implementation blocker remains.
- Dataset adapters must still demonstrate that coordinates, polarity, event count, preprocessing, and timestamp units are preserved. That integration belongs to each dataset phase and cannot be inferred from projector tests alone.

## Decision for next phase

Phase 0.5 passes. Phase 1 is permitted by the transition rule, but was **not started** in this task. No training, model evaluation, or attack experiment was executed.
