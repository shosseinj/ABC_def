# Phase 0 Report — TEMP-DRIFT Benchmark Framework Preparation

STATUS: PASS

**Date:** 2026-09-20  
**Phase status:** PASS — repository inspection and readiness audit complete  
**Experiments run in this phase:** None

## 1. Scope and instruction source

The benchmark scope is SNN + TEMP-DRIFT on N-MNIST, DVS-Gesture, and CIFAR10-DVS, followed by comparison with *Time Is All It Takes: Spike-Retiming Attacks on Event-Driven Spiking Neural Networks*. QSNN is explicitly outside this benchmark phase.

The requested external v3 directory was not present when inspected. The newer repository-local untracked files `AGENT.md` and `ROADMAP.md` identify themselves as v3 and contain the matching benchmark instructions; they were therefore used and were not modified.

## 2. Repository and version-control status

- Repository: `C:\Users\jafari.h.SPADANACO\Desktop\ai_project\testing\qsnn_temp_drift_project`
- Branch: `main`, aligned with `origin/main` at inspected commit `8d6b5f7`.
- Pre-existing untracked files: `AGENT.md`, `ROADMAP.md`.
- Required interpreter for future execution: `C:\Users\jafari.h.SPADANACO\Desktop\ai_project\.venv\Scripts\python.exe`.
- Existing structure includes `attacks/`, `models/`, `scripts/`, `tests/`, `data/`, `checkpoints/`, `results/`, and reporting documentation.
- This audit performed read-only inspection plus documentation edits. No training, attack, evaluation, or test command was run.

## 3. Dataset and model readiness

| Dataset | Data evidence | Model/checkpoint evidence | Current benchmark readiness |
|---|---|---|---|
| N-MNIST | `data/nmnist/` and frozen split artifacts | Five `nmnist_snn_clean_seed*_best.pt` checkpoints for seeds 42, 123, 777, 2026, 6543 | Best starting point, but required budget attacks are absent |
| DVS-Gesture | `data/dvs_gesture/` exists | No DVS-Gesture model, checkpoint, runner, or result found | Not ready |
| CIFAR10-DVS | `data/cifar10_dvs/` and seed-42 split exist | Seed-42 checkpoints at 64×64 and 128×128; validation comparison exists | Baseline partially ready; attack benchmark absent |

Saved N-MNIST SNN evidence reports five-seed validation accuracy `0.98132 ± 0.00241` and official-test accuracy `0.98346 ± 0.00184` (sample SD), with one recorded test evaluation per seed. These are prior saved results, not Phase 0 outputs. CIFAR10-DVS resolution work is validation-only; its artifact states that held-out test data was not accessed.

## 4. Attack-pipeline verification

### Reusable components found

- Event-timestamp perturbation and canonical event-to-frame reconstruction exist in the N-MNIST attack scripts.
- Frozen-victim checks, timestamp-window clipping, monotonic projection, coordinate/polarity preservation, prediction reconstruction, and distortion measurements are present in the audited N-MNIST workflow.
- `scripts/run_nmnist_budget_matched_comparison_v2_seed42.py` supports validated resume state, atomic record writing, progress percentage, ETA, logs, interruption handling, and a final audit.
- Its saved status is complete and fully audited; `audit.json` reports 3,200 checked records, including 2,400 hash-verified source records and 1,600 new records, with zero failures.

### Blocking incompatibility with the new benchmark

The existing completed N-MNIST attack studies use fractional per-event epsilon and query/wall-clock conditions. They do **not** implement the reference benchmark's three independent budget families:

- `B∞`: maximum absolute timestamp displacement;
- `B1`: total absolute timestamp displacement;
- `B0`: number of modified event timestamps.

Existing fields such as normalized maximum shift, normalized mean shift, timestamps changed, frame `L0/L1/L∞`, and candidate-query counts are useful audit measurements but are not substitutes for enforcing the required event-space `B∞`, `B1`, and `B0` constraints. Prior results must not be relabeled as benchmark results.

The general functions in `attacks/temp_drift.py` largely target earlier Iris/QSNN timing representations. The event-dataset TEMP-DRIFT logic currently lives in N-MNIST-specific scripts and is not yet a shared three-dataset benchmark implementation.

## 5. Metric-extraction verification

Existing code correctly supports ASR on clean-correct examples and records per-sample attack success, predictions, runtimes, timestamp changes, bin changes, frame distortion, and query accounting. Existing paired analysis infrastructure can also distinguish one-method-only success, both success, and neither success.

For this benchmark, the result schema still needs mandatory fields for:

- dataset, model, seed, sample ID, true label, and clean correctness;
- budget family and requested budget;
- realized event-space `B∞`, `B1`, and `B0`;
- clean and attacked predictions;
- ASR numerator and clean-correct denominator;
- attack runtime, progress/resume provenance, checkpoint hash, split hash, and audit status.

Every budget summary should report `Budget -> ASR` and retain numerator/denominator counts. Cross-model comparisons must use paired common-clean-correct samples when denominators differ.

## 6. Required budget matrix

| Dataset | `B∞` | `B1` | `B0` |
|---|---|---|---|
| N-MNIST | 1, 2, 3 | 500, 750, 1000, 1500 | 200, 300, 400, 600 |
| DVS-Gesture | 1, 2, 3 | 2000, 4000, 8000, 16000 | 1000, 2000, 4000, 8000 |
| CIFAR10-DVS | 1, 2, 3 | 2000, 4000, 8000, 16000 | 1000, 2000, 4000, 8000 |

No saved artifact was found that evaluates this complete matrix.

## 7. Reporting structure

Planned outputs follow the roadmap:

- `Reports/phase_0_report.md` — this readiness audit;
- `Reports/phase_0_5_report.md` — benchmark contract gate;
- `Reports/phase_1_NMNIST_report.md`;
- `Reports/phase_2_DVSGesture_report.md`;
- `Reports/phase_3_CIFAR10DVS_report.md`;
- `Reports/phase_4_final_comparison_report.md`.

Each phase report must include status, completed tasks, dataset, model, attack, completed seeds, clean accuracy, ASR by budget, runtime, errors/blockers, and next step. A phase is not scientifically complete merely because its code executes.

## 8. Errors and blockers for later phases

1. Requested external instruction directory was unavailable; repository-local copies were used.
2. Exact reference-paper `B∞/B1/B0` constraint semantics and units have not yet been independently verified against the paper.
3. No benchmark-specific projector/auditor enforces all three event-space budget families.
4. No DVS-Gesture training/evaluation pipeline or checkpoint was found.
5. CIFAR10-DVS has only seed-42 validation baseline evidence and no TEMP-DRIFT benchmark.
6. No complete required-budget N-MNIST result exists despite substantial reusable attack infrastructure.
7. Reference-paper comparison values have not been extracted and verified.

## 9. Phase 0 validation and transition decision

- Required Phase 0 inspection tasks: passed.
- Existing independent N-MNIST attack audit: passed with zero failed records.
- Repository state and saved evidence were inspected without executing experiments.
- Unresolved Phase 0 blockers: none. Listed implementation gaps are assigned to Phase 0.5 and later phases.

**Decision: proceed to Phase 0.5 only; do not run Phase 1 experiments.**

Before any experiment, implement and test a frozen benchmark contract that:

1. defines timestamp units and independently enforces `B∞`, `B1`, or `B0` exactly as in the reference paper;
2. records all three realized event-space budgets for every adversarial sample;
3. preserves event count, spatial coordinates, polarity, timestamp domain, and dataset preprocessing;
4. uses clean-correct ASR denominators and paired sample manifests;
5. reuses the proven atomic-write, resume, progress, ETA, logging, hashing, and independent-audit pattern;
6. freezes splits, checkpoints, seeds, and reporting schema before attack evaluation.

After that implementation passes unit and dry-run audit checks, Phase 1 should begin with N-MNIST seed 42, without modifying existing checkpoints or prior artifacts.
