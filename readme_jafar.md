# Current Research Status — QSNN / TEMP-DRIFT

**Repository state audited:** 2026-09-20. This README is an evidence-bounded status record based on the saved N-MNIST artifacts and completed experiments. The official N-MNIST test partition was not accessed for QSNN-v3 or the attack studies.

## 1. Project status

The N-MNIST QSNN-v3 validation campaign is complete. Its architecture and training protocol were frozen across five seeds: 42, 123, 777, 2026, and 6543.

| Model | Accuracy | Macro-F1 | Evaluation |
|---|---:|---:|---|
| QSNN-v3 | **97.272% ± 0.212%** | **97.274% ± 0.212%** | five-seed validation |
| SNN reference | **98.132% ± 0.241%** | — | five-seed validation reference |

The SNN reference Macro-F1 validation aggregate is not available in the preserved SNN artifacts. The QSNN values are validation results, not official-test results.

The canonical seed-42 PGD/TEMP-DRIFT-v2 protocol is independently audited with 2,400/2,400 passing records. The completed budget-matched extension contains 1,600/1,600 valid records across 100 frozen samples.

## 2. Final QSNN-v3 architecture

The frozen configuration is `wide4 + project_measure2`:

- `wide4` Conv/LIF frontend with 16 then 32 channels and a 4×4 spatial summary;
- 32-dimensional latent representation;
- learned **32→8 angle projection**;
- `project_measure2` quantum circuit;
- RY/RZ two-axis data encoding;
- two variational re-upload blocks;
- CNOT-ring entanglement;
- learned measurement basis and 256-state probability readout;
- linear classifier from the quantum probabilities;
- **no classical bypass** from the latent representation to logits.

The promoted end-to-end model has 40,762 parameters. The five-seed campaign was validation-only and used frozen architecture/configuration across seeds.

## 3. Attack protocol

The attack studies use frozen SNN and QSNN models and a common clean-correct manifest of **100 validation samples**, stratified at 10 samples per class. The attacks perturb event timestamps in timestamp space; event coordinates and polarity are preserved.

### Canonical representation and audit

- Event/frame indexing is `[time, polarity, y, x]`.
- Temporal bins use polarity-major channels on the 34×34 sensor grid.
- Canonical reconstruction uses 10 temporal bins and 2 polarity channels.
- Timestamp projection enforces monotonicity, the clean time window, and the per-event epsilon bound.
- Each serialized record is checked for event-count, coordinate, polarity, timestamp, canonical-frame, prediction, objective, success, distortion, and query-accounting invariants.
- Atomic NPZ writing, reload validation, record hashes, and independent audit status are retained in the result artifacts.

### PGD

- White-box timestamp PGD with 20 sign steps.
- 21 candidate evaluations.
- Accounting: 41 attack forwards and 20 backward evaluations.
- True-label cross-entropy objective.

### TEMP-DRIFT-v2

- Derivative-free timestamp search.
- Zero gradients and zero backward evaluations.
- Budget-scaled population/refinement search under the frozen access and wall-clock definitions.

## 4. Audit status

```text
1600/1600 records complete
100/100 samples complete
FULLY AUDITED: YES
All records passed independent audit: YES
Serialization reconstruction verified: YES
```

The original canonical v3 artifact also remains complete and independently audited: 2,400/2,400 records passed with zero failures. The budget-matched artifact reuses the hash-verified frozen v3 source records where specified and records all newly generated conditions separately.

## 5. Budget-matched results

All comparisons below use paired outcomes on the same 100 clean-correct samples. ASR is the fraction of samples for which the attack changes the predicted class.

### Access/query matched

TEMP access was matched to PGD using either 21 candidate evaluations or 41 attack-internal forwards.

| Model | Epsilon | PGD ASR | TEMP-DRIFT-v2 ASR |
|---|---:|---:|---:|
| SNN | 5% | 0% | 0% |
| SNN | 10% | 0% | 0% |
| QSNN | 5% | 3% | 4% |
| QSNN | 10% | 3% | 3% |

### Wall-clock matched

Frozen calibration selected TEMP Q=1600 for SNN and Q=4000 for QSNN. The median TEMP/PGD runtime ratios were 1.083 and 0.978, respectively.

| Model | Epsilon | PGD ASR | TEMP-DRIFT-v2 ASR |
|---|---:|---:|---:|
| SNN | 5% | 0% | 0% |
| SNN | 10% | 0% | 1% |
| QSNN | 5% | 3% | 4% |
| QSNN | 10% | 3% | 5% |

## 6. Distortion comparison

QSNN, epsilon=10%, wall-clock matched:

| Attack | Normalized timestamp shift | Events with bin changes | Frame L2 |
|---|---:|---:|---:|
| PGD | 0.0667 | 0.6463 | 105.65 |
| TEMP-DRIFT-v2 | 0.0925 | 0.8907 | 137.85 |

## 7. Interpretation and limitations

**Observed ASR differences were small and not statistically significant under paired tests. TEMP-DRIFT occasionally achieved slightly higher ASR, accompanied by larger timestamp/frame distortion.**

The attack evidence is single-seed evidence based on 100 paired samples. It does not support a claim that TEMP-DRIFT is superior, that QSNN is more robust, or that either method produces a statistically significant improvement. No multi-seed robustness claim is made.

The paired budget-matched analysis reports PGD-only, TEMP-only, both-success, and neither-success outcomes, together with exact paired tests and class-stratified bootstrap intervals. These results are descriptive and evidence-bounded by the frozen seed-42 attack protocol.

## 8. Key artifacts

### Clean QSNN-v3 validation

- `results/nmnist_hybrid_qsnn_seed42/nmnist_qsnn_v3_multiseed/summary.json`
- `results/nmnist_hybrid_qsnn_seed42/nmnist_qsnn_v3_multiseed/report.md`

### Canonical audited attack protocol

- `results/nmnist_attack_protocol_v3_auditable_seed42/STATUS.json`
- `results/nmnist_attack_protocol_v3_auditable_seed42/audit.json`
- `results/nmnist_attack_protocol_v3_auditable_seed42/per_sample_results.csv`
- `results/nmnist_attack_protocol_v3_auditable_seed42/records_manifest.json`

### Completed budget-matched comparison

- `results/nmnist_budget_matched_comparison_v2_seed42/STATUS.json`
- `results/nmnist_budget_matched_comparison_v2_seed42/audit.json`
- `results/nmnist_budget_matched_comparison_v2_seed42/budget_definitions.json`
- `results/nmnist_budget_matched_comparison_v2_seed42/wallclock_calibration.json`
- `results/nmnist_budget_matched_comparison_v2_seed42/condition_summaries.csv`
- `results/nmnist_budget_matched_comparison_v2_seed42/paired_comparisons.json`
- `results/nmnist_budget_matched_comparison_v2_seed42/report.md`

### Runners and tests

- `scripts/run_nmnist_qsnn_v3_multiseed.py`
- `scripts/run_nmnist_attack_protocol_v3_auditable_seed42.py`
- `scripts/run_nmnist_budget_matched_comparison_v2_seed42.py`
- `scripts/audit_nmnist_attack_protocol_v3_auditable_seed42.py`
- `tests/test_nmnist_canonical_attack_preprocessing.py`
- `tests/test_nmnist_attack_auditor.py`
- `tests/test_nmnist_budget_matched_atomic_writer.py`

## Bottom line

The repository contains completed five-seed QSNN-v3 validation evidence, a completed five-seed SNN reference, an independently audited canonical seed-42 attack protocol, and a completed 1,600-record budget-matched PGD/TEMP-DRIFT-v2 comparison. The evidence shows small, non-significant ASR differences and higher TEMP timestamp/frame distortion in the reported QSNN wall-clock cell. It does not establish attack superiority, QSNN robustness superiority, or a multi-seed robustness claim.
