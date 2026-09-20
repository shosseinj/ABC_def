# Phase acceptance contracts

The agent must read this file at the start of each phase. All values must be measured; unavailable values remain absent and prevent PASS.

## Phase 0 — repository inspection

Inventory source tree, models, checkpoints with hashes, datasets and split metadata, loaders/preprocessing, event representations, attacks, defenses, audit code, experiment entry points, dependency versions, GPU/PyTorch/CUDA state, disk needs, and gaps. Update `readme_jafar.md`, `Reports/repository_inventory.json`, and `Reports/phase_0_report.md`.

## Phase 0.5 — benchmark contract

Implement/test B_inf, B1, and B0 measurement and projection; timeline, packet identity, per-line rate/amplitude/polarity, and capacity-1 auditors; result schema; clean-correct ASR; deterministic subset selection; checkpoint/config hashing; atomic run manifests. The attack implementation must be tested independently against `ResearchLoop/core/audit.py`. Produce `Reports/result_schema.json`, `Reports/contract_test_report.json`, and `Reports/phase_0_5_report.md`.

## Phase 0.75 — freeze

Copy and resolve `ResearchLoop/reference/benchmark_specification_template.json` to `Reports/benchmark_specification.json`; do not leave unresolved model/checkpoint fields. Freeze timestamp unit, T, packetization, binary/integer encodings, preprocessing, exact test indices or their deterministic hash, model/checkpoint hashes, ASR, seeds, queries/iterations, and reference provenance. Human-readable mirror: `Reports/benchmark_specification.md` and phase report.

## Phases 1–3 — datasets

Run every frozen seed × representation × budget type × beta for the repository's own model. Resume per configuration; never rerun a valid completion marker. Store summary CSV using every column in `ResearchLoop/reference/result_columns.txt`, per-sample audit evidence, run configs, stdout/stderr, timings, and hashes. Compute clean/adversarial accuracy, ASR, B metrics, timestamp mean/max/changed ratio, frame L0/L1/L2/Linf, queries, wall attack time, and GPU time. Audit every sample before aggregation. Reports: N-MNIST, DVS-Gesture, CIFAR10-DVS as named in `phases.json`.

## Phase 4 — reference comparison

Join our seed-level summaries and `ResearchLoop/reference/reference_results.csv`. Include Dataset, Representation, Model, Accuracy, Attack, Budget Type, Beta, ASR, Distortion, provenance, and `PAPER_COMPARABLE`/`NON_COMPARABLE`. Never compare unmatched configurations as if equivalent. Produce `Reports/benchmark_comparison.csv`, `.md`, and phase report.

## Phase 5 — statistics

Across the five seeds compute n, mean, sample SD (ddof=1), and two-sided 95% Student-t CI for every metric/configuration. Explain paired comparisons and multiple comparisons if inferential claims are made. Produce the statistics report and machine-readable CSV.

## Phase 6 — stealth

Compute clean vs adversarial ISI histograms with fixed bins, class-logit change (delta-cls, precisely defined), timestamp distortion, frame distortion, polarity-specific shift distributions, and rate-preservation summaries. Save plot source data as CSV plus figures and the report.

## Phase 7 — QSNN

Only execute if the repository contains a real QSNN path and defined mapping from event input to quantum state. Compute valid density matrices, Hermiticity, trace-one, positive semidefinite checks, fidelity, and trace distance with conventions stated. If the scientific mapping/checkpoint is missing, issue a true blocker rather than inventing quantum results.

## Phase 8 — defenses

Evaluate temporal/refractory filtering, temporal smoothing, spatial smoothing where applicable, and timing-aware adversarial training if computationally feasible and defined. Report ASR reduction, clean-accuracy loss, residual distortion, matched seeds/configs, and defense cost. Do not call ordinary non-timing training timing-aware AT.

## Phase 9 — final package

Cross-check all reports and manifests; include all datasets/seeds/attacks/defenses/audits/comparisons, negative/blocked results, threats to validity, reproducibility commands, environment, hashes, and a machine-readable artifact index. Generate `Reports/final_report.md`. PASS requires every prior phase PASS.

