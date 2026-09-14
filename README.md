# QSNN TEMP-DRIFT Project

## Project Overview

This repository studies timing-domain attacks and robustness in quantum spiking neural networks (QSNNs). Inputs are converted to time-to-first-spike (TTFS) latencies, angle encoded, processed by a variational quantum circuit, and classified by a classical head. Iris is the frozen attack benchmark; MNIST work is currently clean-baseline development only.

Scientific status is determined by saved artifacts, not by whether code executes successfully. In particular, MNIST results below are validation-only and do not support attack, defense, or held-out generalization claims.

## Iris Clean Protocol

The authoritative frozen clean protocol is `results/final_clean_protocol.json`:

- Canonical Iris: 150 samples, 4 features, 3 classes
- Stratified train/validation/held-out split with split seed `42`
- TTFS/angle encoding over time window `T = 100`
- 4 qubits, 4 variational layers, 47 trainable parameters
- Adam, learning rate `0.01`, no scheduler
- Model seeds: `42, 123, 777, 2026, 6543`
- Maximum 380 epochs, independently trained from scratch
- Selection: highest validation accuracy, then lowest validation CE, then earliest epoch
- Frozen checkpoint identities recorded with SHA-256 hashes

| Seed | Best epoch | Validation accuracy | Macro-F1 | Class 0 | Class 1 | Class 2 |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 103 | 0.9667 | 0.9666 | 1.00 | 0.90 | 1.00 |
| 123 | 380 | 0.9333 | 0.9333 | 1.00 | 0.90 | 0.90 |
| 777 | 63 | 0.9667 | 0.9666 | 1.00 | 0.90 | 1.00 |
| 2026 | 71 | 0.9333 | 0.9333 | 1.00 | 0.90 | 0.90 |
| 6543 | 380 | 0.9333 | 0.9333 | 1.00 | 0.90 | 0.90 |

Mean validation accuracy was `0.9467 +/- 0.0183` (sample SD), minimum seed accuracy was `0.9333`, and mean class-1 accuracy was `0.9000`. Extending the validation-only training limit from 240 to 380 epochs improved seeds 123 and 6543 without reducing the selected accuracy of the other seeds.

`configs/iris.json` still contains `epochs: 80`. That file is a live/default configuration, not the final checkpoint manifest. Where they conflict, the explicitly `FROZEN` 380-epoch manifest and its hash-identified checkpoints define the final Iris campaign.

## Iris Attack Evaluation

The final held-out campaign compared Classical Timing PGD with derivative-free Adaptive TEMP-DRIFT on the five hash-verified frozen checkpoints. `held_out_evaluations: 1` in the artifact means one final campaign; it should not be interpreted as proof that the held-out partition was accessed only once throughout project history.

- PGD: 20 iterations, step size `epsilon/5`, no random start
- Adaptive TEMP-DRIFT: 1,600 candidates, `tau = 0.1`, no gradients
- Epsilon fractions: 2%, 5%, and 10% of `T`
- ASR: untargeted flips among clean-correct samples
- Exact feasibility: `100%` in every reported final run

| Epsilon | PGD ASR mean +/- SD | TEMP ASR mean +/- SD | PGD 1-F mean +/- SD | TEMP 1-F mean +/- SD |
|---:|---:|---:|---:|---:|
| 2% | 0.0864 +/- 0.0622 | 0.0864 +/- 0.0622 | 0.000987 +/- 0.000000 | 0.000980 +/- 0.000006 |
| 5% | 0.1918 +/- 0.0828 | 0.1918 +/- 0.0828 | 0.006109 +/- 0.000039 | 0.005766 +/- 0.000103 |
| 10% | 0.3285 +/- 0.0967 | 0.3354 +/- 0.1023 | 0.024069 +/- 0.000276 | 0.021953 +/- 0.000473 |

Paired outcomes used the 137 sample/checkpoint observations clean-correct for both attacks:

| Epsilon | PGD only | TEMP only | Both successful | Both robust |
|---:|---:|---:|---:|---:|
| 2% | 0 | 0 | 12 | 125 |
| 5% | 0 | 0 | 27 | 110 |
| 10% | 0 | 1 | 46 | 90 |

Adaptive TEMP-DRIFT was competitive in this campaign: it matched PGD at 2% and 5% and added one paired success at 10%. PGD produced greater mean quantum-state drift. These are descriptive five-seed results, not a significance or superiority claim.

## Gradient Adaptive TEMP-DRIFT Ablation

The validation-only gradient ablation retained the frozen victim models and the same epsilon and feasibility constraints. It used 600 initial candidates, 1,000 gradient updates, and 12 retained elites. Its predeclared acceptance rule required no pooled or checkpoint-level ASR loss, nondecreasing `1-F` and trace distance at every epsilon, at least one strict joint drift gain, and exact feasibility of 1.0.

| Epsilon | PGD ASR | Adaptive TEMP ASR | Gradient TEMP ASR | PGD 1-F | Adaptive TEMP 1-F | Gradient TEMP 1-F |
|---:|---:|---:|---:|---:|---:|---:|
| 2% | 0.0563 | 0.0563 | 0.0563 | 0.000987 | 0.000970 | 0.000976 |
| 5% | 0.1338 | 0.1268 | 0.1268 | 0.006120 | 0.005630 | 0.005603 |
| 10% | 0.2394 | 0.2535 | 0.2465 | 0.024143 | 0.021200 | 0.020973 |

Gradient TEMP had zero unique successes at every epsilon and failed the acceptance rule. The artifact conclusion is `NOT BENEFICIAL`; Adaptive TEMP-DRIFT remains the main proposed attack.

## Gradient TEMP Runtime Optimization

The gradient implementation batches active elites into one model/QNode call per update rather than evaluating each elite separately. It similarly batches initial and proposed candidates. The 1,600-candidate validation configuration records 5,102 QNode evaluations per seed/epsilon run, approximately `66.2-68.8 s` per 30-observation run, and 76,530 QNode evaluations across the 15 gradient runs. Summed gradient-run time is approximately `1,018.3 s`, or `2.263 s` per evaluated validation observation (450 observations, distinct from the 426 clean-correct ASR denominator).

These values describe the current implementation. No artifact contains a controlled pre-optimization versus post-optimization benchmark on identical hardware and workload, so no speedup factor is claimed. Runtime values from the older `iris_attack_comparison_gradient.json` are not directly comparable because that artifact used a different attack grid and checkpoint.

## MNIST Clean-Baseline Development

The first MNIST baseline used balanced subsets of 1,000 training and 200 validation examples per class, 4x4 average-pooled images, 16 TTFS inputs, 4 qubits, 4 re-upload blocks, and five model seeds. Checkpoints were selected by lowest validation CE, then earliest epoch. No held-out data, attacks, or defenses were used.

| Metric | Five-seed result |
|---|---:|
| Validation accuracy | 0.6513 +/- 0.0153 |
| Validation macro-F1 | 0.6486 +/- 0.0155 |
| Validation CE | 1.1167 +/- 0.0454 |
| Minimum seed accuracy | 0.6315 |

The artifact classifies this baseline as `NEEDS_IMPROVEMENT`. Subsequent development increased spatial resolution to 8x8, fitted PCA-16 on training data only, used training-range scaling, expanded to 8 qubits, and tested 2, 3, and 4 re-upload blocks. At seed 42, validation accuracy rose from `0.8305` (2 blocks, epoch 400) to `0.8465` (3 blocks, epoch 250) and `0.8615` (4 blocks, epoch 250). The 3-block runtime is unavailable because the parent diagnostic timed out after that arm completed.

## MNIST Resolution Ablation

The resolution ablation held PCA dimensionality, 8 qubits, 4 blocks, optimizer settings, split, and seed fixed. PCA was fitted on training data only.

| Resolution | Raw features | PCA features | Explained variance | Best epoch | Validation accuracy | Macro-F1 | Validation CE |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8x8 | 64 | 16 | not recorded here | 400 | 0.8680 | 0.8675 | 0.4432 |
| 12x12 | 144 | 16 | 78.60% | 335 | 0.8530 | 0.8523 | 0.4753 |

The 12x12 run stopped at epoch 355 by early stopping and did not exceed the 8x8 reference. The predeclared gate required at least `+0.010` validation accuracy before progressing, so 14x14 was intentionally not run. This is a negative resolution result and is retained as such.

## Current Best MNIST Configuration

The current validation-selected configuration is:

- 8x8 images reduced from 64 values to 16 by train-only PCA and training-range scaling
- TTFS latency followed by angle encoding, `T = 100`
- 8 qubits, 4 cyclic re-upload blocks, 16 quantum features
- Circuit depth 44 and 234 trainable parameters
- Adam, learning rate `0.003`, batch size 64, gradient clipping at 1.0
- Seed and split seed `42`; 10,000 training and 2,000 validation examples
- Resumed from epoch 250 with optimizer state restored; selected at epoch 400

At the selected checkpoint, training accuracy was `0.8714`; validation accuracy was `0.8680`, macro-F1 was `0.8675`, and CE was `0.4432`. The continuation runtime was `2,763.0 s`. Epoch 349 reached raw validation accuracy `0.8710`, but epoch 400 was selected because validation CE, not accuracy, was the primary criterion. Convergence was not established, and this is a single-seed validation result.

## Current MNIST Bottleneck Hypothesis

The evidence does not support image resolution as the current bottleneck: 12x12 retained more spatial information but performed worse than 8x8 under fixed PCA-16 and model capacity. Increasing re-upload depth from two to four blocks improved the seed-42 validation result, while the four-block run still had not established convergence at epoch 400. The working hypothesis is therefore a fixed 16-dimensional representation/model-optimization or capacity bottleneck rather than raw image resolution alone. This is a hypothesis, not a demonstrated mechanism; it requires multi-seed validation and controlled ablations.

## Current Project Status

| Component | Status | Evidence boundary |
|---|---|---|
| Iris clean protocol | Frozen | Five seeds; validation-selected; hash manifest |
| Iris final attack campaign | Complete | One recorded held-out campaign; five frozen checkpoints |
| Adaptive TEMP-DRIFT | Main proposed attack | Competitive descriptively; no superiority claim |
| Gradient Adaptive TEMP-DRIFT | Rejected | Validation ablation, `NOT BENEFICIAL` |
| Quantum-refined TEMP-DRIFT | Rejected | Validation artifact reports non-beneficial result |
| Iris defense | Provisional/unsuccessful | No clean-preserving, reproducible paired robustness success frozen |
| MNIST 4x4 baseline | Complete, needs improvement | Five validation seeds |
| MNIST 8x8 PCA-16 development | Current best | Single validation seed; convergence not established |
| MNIST resolution ablation | Stopped at gate | 12x12 negative; 14x14 not run |
| MNIST attacks and defenses | Not run | No robustness evidence |
| MNIST held-out evaluation | Not accessed in cited artifacts | Generalization remains unknown |

## Scientific Protocol and Invariants

- Fit normalization, PCA, scaling, and every learned preprocessing transform on training data only.
- Select hyperparameters and checkpoints on validation data only; never tune on held-out/test outcomes.
- Treat the five hash-identified 380-epoch Iris checkpoints as frozen for the final campaign.
- Do not silently change the frozen Phase 14 attack definitions, epsilon budgets, or feasibility rules.
- Define ASR on clean-correct samples and report its numerator and denominator.
- When clean-correct sets differ, compare attacks or defenses on common-clean-correct sample IDs and report rescued, broken, both-fail, and both-robust outcomes.
- Keep implementation success separate from scientific success; passing tests does not establish robustness.
- Require reproducible, multi-seed, clean-preserving, paired evidence before making a robustness claim.
- Retain negative and gate-failed results rather than replacing them with post-hoc alternatives.
- Trace QSNN failures through raw features, training-fitted normalization, TTFS, quantum/measured representation, logits, and prediction.
- Treat isolated failures as sample-specific unless replicated evidence supports a broader class or representation effect.

## Primary Artifacts

- `results/final_clean_protocol.json`
- `results/clean_qsnn_380_epoch_test.json`
- `results/final_attack_comparison.json`
- `results/final_attack_samples.csv`
- `results/final_attack_report.md`
- `results/gradient_adaptive_temp_drift_validation.json`
- `results/quantum_refined_temp_drift_validation.json`
- `results/mnist_4x4_clean_validation.json`
- `results/mnist_8x8_pca16_capacity_seed42.json`
- `results/mnist_8x8_pca16_blocks4_seed42_epoch400.json`
- `results/mnist_8x8_pca16_blocks4_seed42_epoch400_history.csv`
- `results/mnist_12x12_pca16_seed42.json`
