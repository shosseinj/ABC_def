# QSNN TEMP-DRIFT Project

## Project Overview

This repository studies timing-domain attacks and robustness in quantum spiking neural networks (QSNNs). Inputs are converted to time-to-first-spike (TTFS) latencies, angle encoded, processed by a variational quantum circuit, and classified by a classical head. Iris is the frozen attack benchmark; MNIST work is currently clean-baseline development only.

Scientific status is determined by saved artifacts, not by whether code executes successfully. In particular, MNIST results below are validation-only and do not support attack, defense, or held-out generalization claims.

- **Classical Timing PGD** is the frozen white-box classifier-loss baseline.
- **Adaptive TEMP-DRIFT** is the main derivative-free attack and jointly searches for decision changes and quantum-state drift.
- **Gradient Adaptive TEMP-DRIFT** is a validation-only gradient-guided ablation; its saved verdict is `NOT BENEFICIAL`.
- **Quantum-drift metrics** are product-state `1 - Fidelity` and Trace Distance, always reported alongside ASR and exact timing feasibility.
- **Dataset status:** Iris clean training and the final Iris attack comparison are completed; MNIST clean-baseline/capacity/resolution development is completed through the gated 12x12 arm. MNIST attacks, defenses, held-out evaluation, and the conditional 14x14 resolution arm were not run.

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

### Epoch-budget ablation

| Maximum epochs | Mean validation accuracy | Sample SD | Minimum seed accuracy | Mean class-1 accuracy | Artifact verdict |
|---:|---:|---:|---:|---:|---|
| 80 | 0.9000 | 0.0850 | 0.7667 | 0.7800 | Baseline |
| 160 | 0.9133 | 0.0606 | 0.8333 | 0.8200 | `BENEFICIAL` |
| 240 | 0.9267 | 0.0435 | 0.8667 | 0.8400 | `BENEFICIAL` |
| 380 | 0.9467 | 0.0183 | 0.9333 | 0.9000 | `BENEFICIAL`; selected and frozen |
| 600 | 0.9467 | 0.0183 | 0.9333 | 0.9000 | `NOT BENEFICIAL` |

The 600-epoch run reduced validation CE for some slow seeds but did not improve validation accuracy, macro-F1, class-wise accuracy, or the aggregate statistics used to choose the budget. The checkpoint policy therefore preserves the explicitly frozen 380-epoch checkpoints rather than replacing them with the newer 600-epoch files.

`configs/iris.json` still contains `epochs: 80`. That file is a live/default configuration, not the final checkpoint manifest. Where they conflict, the explicitly `FROZEN` 380-epoch manifest and its hash-identified checkpoints define the final Iris campaign.

## Iris Attack Evaluation

The final held-out campaign compared Classical Timing PGD with derivative-free Adaptive TEMP-DRIFT on the five hash-verified frozen checkpoints. `held_out_evaluations: 1` in the artifact means one final campaign; it should not be interpreted as proof that the held-out partition was accessed only once throughout project history.

- PGD: 20 iterations, step size `epsilon/5`, no random start
- Adaptive TEMP-DRIFT: 1,600 candidates, `tau = 0.1`, no gradients
- Epsilon fractions: 2%, 5%, and 10% of `T`
- ASR: untargeted flips among clean-correct samples
- Exact feasibility: `100%` in every reported final run

| Epsilon | PGD ASR mean +/- SD | TEMP ASR mean +/- SD | PGD 1-F mean +/- SD | TEMP 1-F mean +/- SD | PGD Trace mean +/- SD | TEMP Trace mean +/- SD |
|---:|---:|---:|---:|---:|---:|---:|
| 2% | 0.0864 +/- 0.0622 | 0.0864 +/- 0.0622 | 0.000987 +/- 0.000000 | 0.000980 +/- 0.000006 | 0.031409 +/- 0.000000 | 0.031309 +/- 0.000094 |
| 5% | 0.1918 +/- 0.0828 | 0.1918 +/- 0.0828 | 0.006109 +/- 0.000039 | 0.005766 +/- 0.000103 | 0.078146 +/- 0.000259 | 0.075813 +/- 0.000727 |
| 10% | 0.3285 +/- 0.0967 | 0.3354 +/- 0.1023 | 0.024069 +/- 0.000276 | 0.021953 +/- 0.000473 | 0.155087 +/- 0.000937 | 0.147765 +/- 0.001687 |

Paired outcomes used the 137 sample/checkpoint observations clean-correct for both attacks:

| Epsilon | PGD only | TEMP only | Both successful | Both robust |
|---:|---:|---:|---:|---:|
| 2% | 0 | 0 | 12 | 125 |
| 5% | 0 | 0 | 27 | 110 |
| 10% | 0 | 1 | 46 | 90 |

Adaptive TEMP-DRIFT was competitive in this campaign: it matched PGD at 2% and 5% and added one paired success at 10%. PGD produced greater mean quantum-state drift. These are descriptive five-seed results, not a significance or superiority claim.

## Gradient Adaptive TEMP-DRIFT Ablation

The validation-only gradient ablation retained the frozen victim models and the same epsilon and feasibility constraints. It used 600 initial candidates, 1,000 gradient updates, and 12 retained elites. Its predeclared acceptance rule required no pooled or checkpoint-level ASR loss, nondecreasing `1-F` and trace distance at every epsilon, at least one strict joint drift gain, and exact feasibility of 1.0.

| Epsilon | PGD ASR | Adaptive TEMP ASR | Gradient TEMP ASR | Gradient unique successes | Adaptive TEMP 1-F | Gradient TEMP 1-F | Adaptive TEMP Trace | Gradient TEMP Trace |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2% | 0.0563 | 0.0563 | 0.0563 | 0 | 0.000970 | 0.000976 | 0.031135 | 0.031237 |
| 5% | 0.1338 | 0.1268 | 0.1268 | 0 | 0.005630 | 0.005603 | 0.074816 | 0.074464 |
| 10% | 0.2394 | 0.2535 | 0.2465 | 0 | 0.021200 | 0.020973 | 0.144647 | 0.142993 |

Gradient TEMP had zero unique successes at every epsilon and failed the acceptance rule. The artifact conclusion is `NOT BENEFICIAL`; Adaptive TEMP-DRIFT remains the main proposed attack.

## Gradient TEMP Runtime Optimization

The gradient implementation batches active elites into one model/QNode call per update rather than evaluating each elite separately. It similarly batches initial and proposed candidates. The 1,600-candidate validation configuration records 5,102 QNode evaluations per seed/epsilon run, approximately `66.2-68.8 s` per 30-observation run, and 76,530 QNode evaluations across the 15 gradient runs. Summed gradient-run time is approximately `1,018.3 s`, or `2.263 s` per evaluated validation observation (450 observations, distinct from the 426 clean-correct ASR denominator).

| Runtime comparison field | Before optimization | Current batched implementation |
|---|---:|---:|
| QNode evaluations | Not available | 76,530 across 15 runs |
| Summed runtime | Not available | approximately 1,018.3 s |
| Runtime per evaluated observation | Not available | 2.263 s |
| Controlled numerical equivalence verification | Not available | Not established by a saved before/after artifact |

These values describe the current implementation. No artifact contains a controlled pre-optimization versus post-optimization benchmark on identical hardware and workload, so no speedup factor is claimed. Runtime values from the older `iris_attack_comparison_gradient.json` are not directly comparable because that artifact used a different attack grid and checkpoint.

## MNIST Clean-Baseline Development

The first MNIST baseline used balanced subsets of 1,000 training and 200 validation examples per class, 4x4 average-pooled images, 16 TTFS inputs, 4 qubits, 4 re-upload blocks, 122 trainable parameters, and five model seeds. The frozen result artifact selected checkpoints by highest validation accuracy, then lowest validation CE, then earliest epoch. No held-out data, attacks, or defenses were used.

| Seed | Best epoch | Validation accuracy | Macro-F1 | Validation CE | Runtime (s) |
|---:|---:|---:|---:|---:|---:|
| 42 | 35 | 0.6510 | 0.6472 | 1.1604 | 170.6 |
| 123 | 39 | 0.6415 | 0.6407 | 1.1383 | 172.7 |
| 777 | 40 | 0.6665 | 0.6640 | 1.0910 | 171.1 |
| 2026 | 40 | 0.6315 | 0.6276 | 1.1438 | 170.9 |
| 6543 | 39 | 0.6660 | 0.6635 | 1.0499 | 171.0 |
| **Mean +/- sample SD** | -- | **0.6513 +/- 0.0153** | **0.6486 +/- 0.0155** | **1.1167 +/- 0.0454** | **171.3 mean** |

The artifact classifies this baseline as `NEEDS_IMPROVEMENT`. Subsequent development increased spatial resolution to 8x8, fitted PCA-16 on the 10,000-example training partition only, used training-range scaling, expanded to 8 qubits, and tested 2, 3, and 4 re-upload blocks. The saved 8x8 reducer retains `0.876441` of explained variance.

| MNIST development stage | Resolution | PCA features | Qubits | Blocks | Parameters | Best / stop epoch | Validation accuracy | Macro-F1 | Validation CE | Runtime (s) | Convergence evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Initial five-seed baseline | 4x4 | Not used | 4 | 4 | 122 | 35-40 / 40 | 0.6513 +/- 0.0153 | 0.6486 +/- 0.0155 | 1.1167 +/- 0.0454 | 171.3 mean | Gate failed: `NEEDS_IMPROVEMENT` |
| Initial PCA sanity, seed 42 | 8x8 | 16 | 8 | 2 | 202 | 40 / 40 | 0.7195 | 0.7171 | 0.9165 | 264.2 | Max epoch |
| PCA continuation, seed 42 | 8x8 | 16 | 8 | 2 | 202 | 250 / 250 | 0.8185 | 0.8180 | 0.6074 | 1,431.2 | Loss still improving |
| PCA continuation, seed 42 | 8x8 | 16 | 8 | 2 | 202 | 400 / 400 | 0.8305 | 0.8301 | 0.5826 | 1,019.5 | Convergence not established |
| Capacity arm, seed 42 | 8x8 | 16 | 8 | 3 | 218 | 250 / 250 | 0.8465 | 0.8461 | 0.5082 | Not available | Parent diagnostic timed out after arm completion |
| Capacity arm, seed 42 | 8x8 | 16 | 8 | 4 | 234 | 250 / 250 | 0.8615 | 0.8606 | 0.4644 | 4,463.2 | Max epoch |
| Capacity continuation, seed 42 | 8x8 | 16 | 8 | 4 | 234 | 400 / 400 | **0.8680** | **0.8675** | **0.4432** | 2,763.0 | Convergence not established |
| Resolution arm, seed 42 | 12x12 | 16 | 8 | 4 | 234 | 335 / 355 | 0.8530 | 0.8523 | 0.4753 | 6,493.2 | Early stop |

## MNIST Resolution Ablation

The resolution ablation held PCA dimensionality, 8 qubits, 4 blocks, optimizer settings, split, and seed fixed. PCA was fitted on training data only.

| Resolution | Raw features | PCA features | Explained variance | Best epoch | Validation accuracy | Macro-F1 | Validation CE |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8x8 | 64 | 16 | 87.64% | 400 | 0.8680 | 0.8675 | 0.4432 |
| 12x12 | 144 | 16 | 78.60% | 335 | 0.8530 | 0.8523 | 0.4753 |
| 14x14 | 196 | 16 | Not available | Not run | Not run | Not run | Not run |

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

**Evidence:** 12x12 performed worse than 8x8 under fixed PCA-16 and model capacity, while increasing re-upload depth from two to four blocks improved the seed-42 validation result. The four-block 8x8 run still had not established convergence at epoch 400.

**Interpretation:** raw image resolution alone is not supported as the current bottleneck. A fixed 16-dimensional representation and/or model-capacity/optimization bottleneck remains plausible, but no causal mechanism has been demonstrated.

**Next planned controlled experiment:** the only saved conditional next resolution arm was 14x14, and it was correctly **not run** because 12x12 failed the predeclared `+0.010` validation-accuracy gate. No artifact explicitly freezes a replacement next experiment after that failure; multi-seed confirmation or a new controlled representation/capacity ablation is therefore a recommendation, not a completed or frozen plan.

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
| MNIST next experiment | Not started / not frozen | Conditional 14x14 was blocked; no replacement protocol is frozen |
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
