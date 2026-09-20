# Current Research Status — QSNN / TEMP-DRIFT

**Repository state audited:** 2026-09-20. This file is an evidence-bounded status record. A script or artifact is not treated as completed evidence unless its metadata, status, row counts, and audit fields support that conclusion.

## 1. Research goal

The current main question is whether timing-domain perturbations of event timestamps can change classification in spiking and quantum-spiking neural networks, and how TEMP-DRIFT compares with a white-box timing PGD baseline under a reproducible, paired, clean-correct evaluation. The current central dataset is N-MNIST. Iris is the completed proof-of-concept line; SHD is a completed SNN baseline line; MNIST, DVS Gesture, and CIFAR10-DVS are supporting development or preparation lines.

The repository does **not** currently support a general robustness or attack-superiority claim: the main N-MNIST attack evidence is single-seed, and the compute/query-budget-matched extension is incomplete.

## 2. Supervisor requirements represented by repository evidence

No separate supervisor instruction document was found in the repository. The following checklist is therefore limited to requirements encoded in the phase plans, protocol scripts, audit scripts, `AGENTS.md`, and saved reports.

| Requirement | Status | Evidence boundary |
|---|---|---|
| Establish clean SNN and QSNN baselines | **DONE for N-MNIST development scope** | SNN five-seed test artifact; QSNN-v3 five-seed validation artifact |
| Use canonical event preprocessing and frozen splits | **DONE for corrected N-MNIST protocol** | `nmnist_snn_multiseed_split.json`; v3 audit |
| Compare PGD and TEMP-DRIFT on common clean-correct samples | **DONE at the audited-record level; final matched comparison pending** | v3 manifest, per-sample CSV, and audit |
| Preserve event invariants and audit serialized records | **DONE for v3** | 2,400/2,400 records audited; zero failures |
| Match attack compute/query budgets | **IN PROGRESS / PARTIAL** | v2 calibration and budgets frozen; evaluation interrupted |
| Produce final paired statistics for the budget-matched study | **NOT STARTED** | No final audit, summaries, comparisons, or report in the v2 directory |
| Establish multi-seed N-MNIST attack evidence | **NOT STARTED** | v3 audit explicitly records `five_seed_campaign_started: false` |
| Evaluate official N-MNIST QSNN test performance | **NOT STARTED** | QSNN artifacts state official test was not accessed |
| Demonstrate a clean-preserving defense | **BLOCKED / NOT ESTABLISHED** | Existing defense experiments are historical validation studies, not a frozen reproducible robustness result |

## 3. Current model architecture

### N-MNIST SNN baseline — completed clean evaluation

The saved clean protocol uses native N-MNIST events converted to **10 ordered temporal bins × 2 polarity channels × 34 × 34**, with a convolutional LIF network. The fixed official-training split uses `split_seed=42`; five model seeds are 42, 123, 777, 2026, and 6543. Checkpoints are selected by validation accuracy, then validation loss. Parameter count is **25,482**.

Aggregate clean results from `results/nmnist_snn_multiseed_summary.json`:

| Metric | Mean ± sample SD | Evaluation |
|---|---:|---|
| Validation accuracy | 98.132% ± 0.241% | five seeds |
| Official test accuracy | 98.346% ± 0.184% | one evaluation per seed |
| Official test macro-F1 | 98.336% ± 0.186% | one evaluation per seed |

The SNN clean campaign is marked `COMPLETED`. It has not been independently re-evaluated in the same way as the SHD campaign.

### N-MNIST QSNN-v3 — frozen validation model

The current frozen QSNN configuration is `wide4 + project_measure2`:

- 10 event frames with polarity preserved;
- `wide4` Conv/LIF frontend: 16 then 32 channels, 4×4 spatial summary, 32-dimensional latent;
- learned `Linear(32, 8)` projection with no classical bypass;
- two quantum re-upload blocks, two-axis encoding, ring entanglement, learned measurement basis;
- AdamW, batch size 256, maximum 40 epochs, validation-accuracy-first checkpoint selection;
- five seeds: 42, 123, 777, 2026, 6543;
- parameter count: **40,762** for the promoted end-to-end model.

Aggregate validation results from `results/nmnist_hybrid_qsnn_seed42/nmnist_qsnn_v3_multiseed/summary.json`:

| Metric | Mean ± sample SD |
|---|---:|
| Validation accuracy | 97.272% ± 0.212% |
| Validation macro-F1 | 97.274% ± 0.212% |

The official N-MNIST test partition was not accessed. Seed 42 training stopped at the command limit during epoch 38; its saved best epoch-37 checkpoint was separately re-evaluated and matched its stored validation metrics. This is valid validation evidence, not a completed official-test result.

## 4. Clean model results and partitions

| Dataset/model | Current evidence | Status |
|---|---|---|
| N-MNIST SNN | Five-seed validation and official-test artifacts; 98.346% ± 0.184% test accuracy | **VALID; not independently re-audited** |
| N-MNIST QSNN-v3 | Five-seed validation only; 97.272% ± 0.212% | **VALID validation evidence; official test not started** |
| SHD SNN | Five-seed official-test campaign, then independent exact re-audit | **VALID / AUDITED** |
| Iris QSNN | Earlier proof-of-concept and attack/defense phases | **Historical completed line; scope-specific** |
| MNIST clean development | 4×4, 8×8/PCA and resolution/capacity studies | **Development evidence only** |
| DVS Gesture | Dataset availability only; no saved internal model result | **NOT STARTED** |
| CIFAR10-DVS | Seed-42 64×64 vs 128×128 validation resolution check | **VALID validation check; no held-out test** |

## 5. Current N-MNIST attack protocol

The current valid attack artifact is `results/nmnist_attack_protocol_v3_auditable_seed42/`. It supersedes the v2 canonical artifact for audited record storage while retaining the corrected preprocessing and attack definitions.

- **Evaluation set:** 100 validation samples, 10 per class, selected from the frozen common-clean-correct manifest; official test was not instantiated.
- **Epsilons:** 0, 0.01%, 0.25%, 1%, 5%, and 10% of each sample's inclusive clean duration `t_last - t_first + 1`.
- **Projection:** timestamp perturbations remain within the clean time window, satisfy the per-event epsilon bound, and are projected to nondecreasing timestamps.
- **Canonical representation:** event order `[time, polarity, y, x]`, 10 temporal bins, 2 polarity channels, 34×34 sensor grid.
- **PGD:** 20 steps, step size `epsilon/5`, no random start, true-label cross-entropy objective; surrogate triangular soft bins with straight-through hard forward/soft gradient.
- **TEMP-DRIFT-v2:** derivative-free timestamp search with 1,600 candidates per sample, initialization 600, four refinement generations of 250, elite preservation, differential mutation, boundary priority, fidelity weight 0.35, margin weight 0.65.
- **ASR:** untargeted prediction flips among the 100 clean-correct samples.
- **Accounting:** candidate evaluations and batched classifier/state calls are stored separately; record-level event, timestamp, frame, prediction, objective, and query invariants are checked.

## 6. Corrected and independently audited attack results

The v3 artifact contains **2,400/2,400 hash-verified, invariant-passing records**, with `failed_records=0`, `fully_audited=true`, and independent audit version `independent-posthoc-v1`.

### QSNN-v3, seed 42, 100 validation samples

| Epsilon | PGD ASR | TEMP-DRIFT-v2 ASR |
|---:|---:|---:|
| 5% | 3% (3/100) | 4% (4/100) |
| 10% | 3% (3/100) | 5% (5/100) |

At 0%, 0.01%, 0.25%, and 1%, both attacks have 0/100 successes for QSNN. All v3 cells have 100% feasibility. These are single-seed validation results and are not a superiority or robustness claim.

### SNN, seed 42, 100 validation samples

| Epsilon | PGD ASR | TEMP-DRIFT-v2 ASR |
|---:|---:|---:|
| 5% | 0% (0/100) | 0% (0/100) |
| 10% | 0% (0/100) | 1% (1/100) |

The v3 audit confirms the stored ASR values, zero-epsilon identity controls, feasibility, hashes, canonical frames, timestamp bounds, and query accounting. It does not provide multi-seed attack replication.

## 7. Statistical analysis

Completed analyses include:

- paired success/failure accounting is available from the v3 per-sample records, but no final significance report has been generated;
- per-class and sample-level records in the audited v3 artifact;
- Iris paired attack/defense and multi-seed validation analyses;
- Phase 18–22 descriptive representation, sensitivity, and seed analyses;
- SHD independent exact test re-audit.

The N-MNIST v3 audit is a validity audit, not a significance test. The repository contains no completed significance analysis for the interrupted budget-matched v2 campaign. No claim of statistical significance is made here. Single-seed N-MNIST attack cells and incomplete budget matching limit inference.

## 8. Compute/query budget matching — PARTIAL / NOT FINAL

Target: `results/nmnist_budget_matched_comparison_v2_seed42/`, runner `scripts/run_nmnist_budget_matched_comparison_v2_seed42.py`.

Calibration and budget artifacts were written before interruption:

- calibration sample selection completed: 10 samples, one per class, selected without attack outcomes;
- wall-clock calibration completed for QSNN and SNN;
- both models were marked matched within the protocol's 10% median-runtime criterion;
- frozen access conditions: TEMP budgets matching 21 PGD candidates and 41 PGD attack-internal forwards;
- selected wall-clock budgets: QSNN `Q=4000`, SNN `Q=1600`.

The actual evaluation matrix is:

```text
100 samples × 2 models × 2 epsilons × (2 access conditions + 2 wall-clock attack records)
= 1,600 new records
```

Observed state at audit:

- 1,054 readable NPZ files exist;
- 523 have `audit_passed=True`;
- 531 have `audit_passed=False`;
- no NPZ file failed the read/truncation check;
- 546 matrix positions have no NPZ file;
- no final `audit.json`, per-sample CSV, condition summaries, paired comparisons, or report exists;
- `STATUS.json` remains `running` with `fully_audited=false`;
- the runner has no safe resume/skip implementation and currently refuses an existing records directory.

This experiment is **PARTIAL / NOT FINAL**. Its partial records must not be interpreted scientifically or combined into completed comparisons. The required next implementation step is a separately reviewed safe-resume change that validates existing files, accepts only complete audit-passing records, skips those keys, writes new files atomically, and emits live progress. No such change has been made by this audit.

## 9. Important bugs and corrections

### N-MNIST representation mismatch — INVALID / SUPERSEDED

Earlier N-MNIST attack outputs used a representation that did not match the native event-to-frame contract. The canonical v2 script explicitly records the previous results as invalid/debug-only due to representation mismatch. The correction centralized `canonical_frames_torch`, preserved polarity and event metadata, and added zero-control and canonical-frame checks. The v3 artifact supersedes the old debug campaign and is the audited source for current N-MNIST attack numbers.

### Attack objective and accounting ambiguity — corrected in v3

The corrected v3 records distinguish PGD true-label cross-entropy from TEMP-DRIFT true-class-margin optimization and separately store candidate evaluations, classifier calls, state calls, and verification forwards. Earlier results that do not identify these definitions are not current evidence for matched-compute claims.

### Unequal attack budgets — limitation of the exploratory comparison

The earlier 1,600-candidate TEMP-DRIFT versus PGD comparison is valid as an audited exploratory result, but it is not compute/query matched. The v2 budget-matched campaign was created to address this limitation and was interrupted before final completion.

### Interrupted QSNN seed-42 training — bounded use

The QSNN seed-42 command stopped at its time limit during epoch 38. The saved best checkpoint and independent validation re-evaluation support validation reporting, but not a completed official-test result.

### Historical defense/robustness results — not current success evidence

The Iris and phase defense studies include negative or mixed validation results, seed sensitivity, and clean-performance tradeoffs. They do not establish a clean-preserving reproducible defense. They remain useful diagnostics but must not be presented as a successful defense.

## 10. Audit and reproducibility status

**Strongest current audit:** `results/nmnist_attack_protocol_v3_auditable_seed42/`.

It includes a 2,400-record manifest with SHA-256 hashes, per-sample CSV data, audit JSON, canonical preprocessing provenance, invariant checks, zero-epsilon controls, frozen split/checkpoint hashes, seed 42, and explicit test-access flags. The v2 interrupted directory has calibration and budget metadata but no completed final audit.

The SHD test campaign has an independent exact re-audit in `results/shd_snn_test_reaudit.json` and `results/shd_snn_test_reaudit_report.md`. N-MNIST SNN clean test artifacts contain checkpoint hashes and one test evaluation per seed, but no equivalent independent re-audit artifact was found.

## 11. Current project status

| Work item | Status | Evidence / artifact |
|---|---|---|
| N-MNIST SNN clean baseline | **VALID** | `results/nmnist_snn_multiseed_summary.json` and per-seed test JSON |
| N-MNIST QSNN-v3 clean validation | **VALID, validation-only** | `results/nmnist_hybrid_qsnn_seed42/nmnist_qsnn_v3_multiseed/` |
| Canonical N-MNIST attack protocol | **VALID / AUDITED** | v3 `STATUS.json`, `audit.json`, `records_manifest.json` |
| Seed-42 PGD/TEMP attack cells | **VALID / AUDITED; not a final matched comparison** | v3 audit and per-sample CSV |
| Budget-matched PGD/TEMP comparison | **PARTIAL / NOT FINAL** | v2 calibration, budgets, 1,054 readable NPZ files |
| N-MNIST attack multi-seed replication | **NOT STARTED** | v3 audit says campaign not started |
| QSNN official N-MNIST test | **NOT STARTED** | frozen config says test not accessed |
| SHD SNN clean test | **VALID / AUDITED** | independent re-audit artifacts |
| CIFAR10-DVS resolution check | **VALID validation-only** | resolution comparison JSON/history files |
| DVS Gesture internal model | **NOT STARTED** | dataset inventory only |
| Clean-preserving defense claim | **NOT ESTABLISHED** | negative/mixed defense artifacts |

## 12. Remaining work

### Immediate next step

Implement and independently review safe resume for the interrupted v2 runner. The change must validate existing NPZ metadata and invariants, accept only complete `audit_passed=True` records, preserve all valid files, avoid treating audit-failed/partial files as complete, write atomically, and produce live progress. Do not resume until this code is reviewed.

### Required before a supervisor report or paper

1. Complete the budget-matched v2 matrix under the frozen protocol.
2. Run the final record audit and generate condition summaries and paired comparisons.
3. Reconcile any audit-failed records rather than silently counting them.
4. Report paired outcomes with explicit denominators, including both-success, both-robust, and one-attack-only outcomes.
5. Decide whether multi-seed N-MNIST attack replication is required for the intended claim; the current repository has not started it.
6. If QSNN clean official-test performance is required, freeze the test protocol before accessing the partition.

### Later robustness work

Multi-seed attacks, additional model/checkpoint seeds, and any defense evaluation should follow only after the corrected single-seed budget-matched evidence is complete. No robustness claim should be generalized from the current partial or single-seed attack artifacts.

## 13. Recommended execution order

1. Review and test the safe-resume implementation without launching attacks.
2. Validate the existing v2 records and classify audit-passing, audit-failing, missing, and corrupt keys.
3. Resume only missing/invalid matrix keys under the frozen calibration and budget artifacts.
4. Run the final v2 audit and generate statistical summaries.
5. Independently review the completed comparison and its paired denominators.
6. Only then plan multi-seed attack replication or official-test evaluation.

## 14. Key files

### Current N-MNIST evidence

- `scripts/run_nmnist_snn_multiseed.py`
- `scripts/run_nmnist_qsnn_v3_multiseed.py`
- `scripts/run_nmnist_attack_protocol_v3_auditable_seed42.py`
- `scripts/run_nmnist_attack_protocol_v2_canonical_seed42.py`
- `scripts/run_nmnist_common_attack_protocol_seed42.py`
- `scripts/run_nmnist_budget_matched_comparison_v2_seed42.py`
- `scripts/audit_nmnist_attack_protocol_v3_auditable_seed42.py`
- `scripts/audit_nmnist_attack_pipeline_seed42.py`
- `results/nmnist_snn_multiseed_summary.json`
- `results/nmnist_hybrid_qsnn_seed42/nmnist_qsnn_v3_multiseed/`
- `results/nmnist_attack_protocol_v3_auditable_seed42/`
- `results/nmnist_budget_matched_comparison_v2_seed42/`

### Splits, checkpoints, and tests

- `results/nmnist_snn_multiseed_split.json`
- `results/nmnist_clean_seed42_preprocessing.json`
- `results/nmnist_attack_protocol_v3_auditable_seed42/common_clean_correct_manifest.json`
- `checkpoints/nmnist_snn_multiseed/`
- `checkpoints/nmnist_hybrid_qsnn_seed42/nmnist_qsnn_v3_multiseed/`
- `tests/test_nmnist_clean.py`
- `tests/test_nmnist_attack_auditor.py`
- `tests/test_nmnist_canonical_attack_preprocessing.py`
- `tests/test_nmnist_temp_drift_v2.py`

### Broader completed evidence

- `results/shd_snn_test_reaudit.json`
- `results/shd_snn_test_reaudit_report.md`
- `results/phase18_results.md` through `results/phase22_results.md`
- `results/phase22_results.md`
- `results/cifar10_dvs_resolution_comparison_seed42.json`

## Bottom line

The repository currently contains a completed and independently audited **single-seed canonical N-MNIST attack protocol**, completed clean SNN evidence, and validation-only QSNN-v3 evidence. The scientifically important compute/query-budget-matched comparison is **interrupted and not final**. No final matched-comparison statistics or multi-seed N-MNIST attack evidence currently exists.
