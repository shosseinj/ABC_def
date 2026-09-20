# Phase 0.75 — Specification freeze

**Status: BLOCKED; independent gate not passed.**

Phase 0 and Phase 0.5 passed their independent gates. The specification freeze cannot be completed without inventing missing scientific choices or checkpoint provenance. DVS-Gesture has no repository model or checkpoint, CIFAR10-DVS lacks four required seed checkpoints, N-MNIST event data is absent, and the locked PIL-PGD attack path is not implemented.

No `Reports/benchmark_specification.json` was emitted because the phase contract prohibits unresolved model/checkpoint fields. No attack experiment was run. Full evidence, impact, commands tried, and exact remediation are in `Reports/diagnostic_blocker.md` and `Reports/logs/phase_0_75_preflight.log`.
