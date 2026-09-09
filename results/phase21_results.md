# Phase 21 — Representation Diagnosis

## 1. Agents and Skills Used

Q1: Used scientific-critical-thinking, experimental-design, statistical-analysis, and PennyLane guidance. Implementation success and scientific success are reported separately.

## 2. Interpreter

Q2: Python interpreter provenance is recorded by the generator report; reconciliation used the repository interpreter.

## 3. Files Added

Added the exact Stage-A diagnosis, robust-versus-failed, centroid-crossing, local-purity, StageA-gate, report, and exhaustive manifest contract files.

## 4. Files Modified

Q3: Updated the Phase-21 contract exporter/tests only. TTFS, circuit, deployment head family, training rule, and attacks were not altered.

## 5. Regression Status

Focused Phase-21 tests pass. This verifies implementation/schema behavior, not defense efficacy.

## 6. Phase 21 Protocol

Q4: The immutable repository-local protocol was persisted before Phase-21 outputs. Its provenance is not independent registration and cannot exclude deleted, external, or unrecorded work.

## 7. Development Splits

Seeds 271, 811, 1618, 2718, and 4242 were absent from recorded split-seed context before output inspection. Each exact manifest contains 90 train, 30 validation, and 30 hidden IDs/labels with disjoint membership.

## 8. Model Seeds

Q5: Model seeds 42, 777, and 2026 are nested matched repetitions within each split. The scientific replication unit is split, n=5.

## 9. Stage A Representation Metrics

Q6: `iris_phase21_repr_diagnosis.csv/json` contains exactly 3600 rows: 15 cells x 2 attacks x 4 epsilons x 30 validation samples, with raw, normalized, TTFS, measured quantum, logit, margin, prediction, geometry, and canonical-ID fields.

## 10. Robust vs Failed Samples

Q7: Successful means clean-correct then attacked-incorrect; robust means clean-correct then attacked-correct. Clean-incorrect rows are explicitly excluded rather than moved into either denominator. Group counts and means are in `iris_phase21_robust_vs_fail.csv`.

## 11. Class-Wise Representation Shift

Class labels are retained per row for descriptive stratification only. No class-specific result, including sample 119, entered the gate or selected a defense.

## 12. Centroid Crossing

Q8: `iris_phase21_centroid_crossing.csv` contains all 3,600 clean/attacked nearest-centroid states and crossing indicators using training-only centroids.

## 13. Local Purity Stability

Q9: `iris_phase21_local_purity.csv` contains all 3,600 clean/attacked k=3 training-neighbor purities, deltas, IDs, and label-sequence change indicators.

## 14. Multi-Split Reproducibility

Split quantum successful-minus-robust contrasts were {271: -0.001428294105033416, 811: 0.01947382729195153, 1618: -0.004941311877125086, 2718: 0.014381663227837998, 4242: -0.002979012901771419}. Their equal-split mean was 0.004901374, descriptive t4 95% CI [-0.008996324, 0.018799073]. Only 2/5 directions were positive.

## 15. Stage A Gate

Q10: Stage A failed with criteria {'criterion1_aggregate_quantum_positive': True, 'criterion2_quantum_positive_splits': False, 'criterion3_margin_and_spearman': False, 'criterion4_top_contributor_exclusion': True}; all four were required without post-result modification. The split quantum contrast was positive in only 2/5 splits and its descriptive t4 CI crossed zero. Q11: Stage B's prespecified CE-plus-cosine objective, fixed lambda ablation, loss/gradient monitoring, and clean gate were not run. Q12: Anti-collapse geometry, the train-only linear diagnostic, and at-most-one selection were not run. Q13: Candidate random-jitter/Phase14-PGD attacks, common-clean-correct rescued/broken/both-fail/both-robust outcomes, small-epsilon and robustness gates, and TEMP transfer are not estimable; no Stage-B artifacts exist and non-execution is not robustness. Split is n=5; nested model seeds and pooled Spearman rho=0.633002 are descriptive only; undefined denominators were not set to zero. Sample 119 was ordinary data and never a criterion. No held-out feature rows were accessed; full loaders were fail-closed. Root classification: negative Stage-A scientific mechanism gate, not implementation failure and not proof all defenses fail. Q14: See protected `iris_phase21_scientific_audit.md` and `iris_phase21_beginner_summary.md`; the exhaustive manifest hashes generator outputs. Phase 22 decision: do not advance a defense; first independently replicate the frozen Stage-A protocol on new development splits.
