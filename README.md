# QSNN TEMP-DRIFT Project

## Project Overview

This project studies timing-domain adversarial vulnerability in a Quantum Spiking Neural Network (QSNN) using time-to-first-spike (TTFS) encoding on the Iris dataset.

## Clean QSNN Model

- Dataset: canonical Iris
- Samples: 150
- Input features: 4
- Classes: 3
- Split: stratified train/validation/held-out protocol
- Encoding: TTFS
- Model: 4-qubit QSNN with 4 variational layers
- Trainable parameters: 47
- Optimizer: Adam
- Learning rate: `0.01`
- Scheduler: none
- Checkpoint selection: validation only

## Final Clean Training Protocol

`max_epochs = 380`

Model seeds: `42, 123, 777, 2026, 6543`

Every model is trained independently from scratch:

- No previous weights are loaded.
- No checkpoint is resumed.
- A fresh QSNN is initialized for each seed.
- A fresh Adam optimizer is initialized for each seed.

Checkpoint selection uses:

1. Highest validation accuracy
2. Lowest validation cross-entropy (CE)
3. Earliest epoch

## Final Frozen Validation Results

| Seed | Best Epoch | Val Accuracy | Macro-F1 | Class 0 | Class 1 | Class 2 |
| ---: | ---------: | -----------: | -------: | ------: | ------: | ------: |
|   42 |        103 |       0.9667 |   0.9666 |    1.00 |    0.90 |    1.00 |
|  123 |        380 |       0.9333 |   0.9333 |    1.00 |    0.90 |    0.90 |
|  777 |         63 |       0.9667 |   0.9666 |    1.00 |    0.90 |    1.00 |
| 2026 |         71 |       0.9333 |   0.9333 |    1.00 |    0.90 |    0.90 |
| 6543 |        380 |       0.9333 |   0.9333 |    1.00 |    0.90 |    0.90 |

- Mean validation accuracy: `0.9467 ± 0.0183`
- Minimum seed accuracy: `0.9333`
- Mean Class-1 accuracy: `0.9000`
- No strong seed degraded.
- Seed variability was substantially reduced compared with shorter training limits.

## Why 380 Epochs Was Selected

Training limits of 80, 160, and 240 epochs were insufficient for the slower seeds. Extending training to 380 epochs improved seeds 123 and 6543 without degrading the strong seeds. A final 600-epoch test reduced validation CE further but did not improve validation accuracy, macro-F1, or class-wise accuracy.

The 380-epoch setting was therefore selected as the final efficient clean-training protocol.

`FINAL CLEAN PROTOCOL: FROZEN`

## Frozen Protocol Artifact

The frozen protocol and selected checkpoint hashes are recorded in:

- `results/final_clean_protocol.json`

Supporting validation artifacts:

- `results/clean_qsnn_380_epoch_test.json`
- `results/clean_qsnn_380_epoch_test.csv`
- `results/clean_qsnn_380_epoch_history.csv`

# TEMP-DRIFT Attack Framework

## TEMP-DRIFT Introduction

TEMP-DRIFT is the proposed derivative-free timing-domain attack for the QSNN. It perturbs TTFS spike times under the same epsilon timing budget, valid spike-time bounds `[0,T]`, and exact feasibility constraints used in evaluation. Its search jointly considers attack success or proximity to the decision boundary and quantum-state drift measured by `1 - Fidelity`.

The final Adaptive TEMP-DRIFT uses:

- Coordinate-2 sensitivity guidance
- Exploration of all timing coordinates
- Iterative elite refinement
- Rank-balanced fidelity/margin scoring
- Boundary-crossing priority
- Differential mutation
- Exact feasibility checking

Coordinate 2 was identified by the earlier seed-sensitivity analysis and guides the search, but Adaptive TEMP-DRIFT continues to explore every timing coordinate.

## Classical Timing PGD Baseline

Classical Timing PGD is the main baseline. It is a white-box, gradient-based attack that directly maximizes classification loss in spike-time space under the same epsilon constraints while keeping the victim QSNN frozen. It provides a strong classifier-oriented baseline against which TEMP-DRIFT is compared.

## Gradient Adaptive TEMP-DRIFT

Gradient Adaptive TEMP-DRIFT is an experimental gradient-guided extension that preserves the adaptive TEMP-DRIFT structure, computes gradients directly with respect to timing perturbations, and uses a joint decision-boundary/quantum-drift objective. It does not update model parameters and retains all epsilon and exact feasibility constraints. The variant was evaluated experimentally but was not selected as the final main method.

## Final Validation Comparison of Gradient Variant

The comparison used the frozen clean QSNN checkpoints and paired common clean-correct development/validation samples.

| ε   | PGD ASR | Adaptive TEMP ASR | Gradient TEMP ASR |  PGD 1-F | Adaptive TEMP 1-F | Gradient TEMP 1-F |
| --- | ------: | ----------------: | ----------------: | -------: | ----------------: | ----------------: |
| 2%  |  0.0563 |            0.0563 |            0.0563 | 0.000987 |          0.000970 |          0.000976 |
| 5%  |  0.1338 |            0.1268 |            0.1268 | 0.006120 |          0.005630 |          0.005603 |
| 10% |  0.2394 |            0.2535 |            0.2465 | 0.024143 |          0.021200 |          0.020973 |

- Gradient TEMP unique successes: `0` at every epsilon
- Exact feasibility: `100%`
- Gradient TEMP average runtime: `2.263 s/sample`
- Gradient TEMP QNode evaluations: `76,530`
- Gradient TEMP runtime: approximately `1018.3 s`

`GRADIENT ADAPTIVE TEMP-DRIFT: NOT BENEFICIAL`

The gradient variant provided no ASR improvement over Adaptive TEMP-DRIFT, no consistent quantum-drift improvement, and no unique successful attacks, while requiring substantially more computation.

`Adaptive TEMP-DRIFT remains the main proposed attack.`

## Final Held-Out Attack Comparison

The final frozen-model held-out comparison evaluated Classical Timing PGD and Adaptive TEMP-DRIFT.

| ε   | PGD ASR mean ± SD | TEMP-DRIFT ASR mean ± SD |   PGD 1-F mean ± SD |  TEMP 1-F mean ± SD | PGD Trace mean ± SD | TEMP Trace mean ± SD |
| --- | ----------------: | -----------------------: | ------------------: | ------------------: | ------------------: | -------------------: |
| 2%  |   0.0864 ± 0.0622 |          0.0864 ± 0.0622 | 0.000987 ± 0.000000 | 0.000980 ± 0.000006 | 0.031409 ± 0.000000 |  0.031309 ± 0.000094 |
| 5%  |   0.1918 ± 0.0828 |          0.1918 ± 0.0828 | 0.006109 ± 0.000039 | 0.005766 ± 0.000103 | 0.078146 ± 0.000259 |  0.075813 ± 0.000727 |
| 10% |   0.3285 ± 0.0967 |          0.3354 ± 0.1023 | 0.024069 ± 0.000276 | 0.021953 ± 0.000473 | 0.155087 ± 0.000937 |  0.147765 ± 0.001687 |

Paired results on `137` common clean-correct samples:

- At 2%: PGD-only `0`, TEMP-only `0`
- At 5%: PGD-only `0`, TEMP-only `0`
- At 10%: PGD-only `0`, TEMP-only `1`
- TEMP-DRIFT matched every PGD success and added one unique success at 10%

TEMP-DRIFT was competitive with PGD in ASR: the methods tied at 2% and 5%, while TEMP-DRIFT was slightly higher at 10%. PGD retained higher quantum drift in both `1 - Fidelity` and Trace Distance. Exact feasibility was `100%`.

`TEMP-DRIFT: COMPETITIVE WITH CLASSICAL PGD`

## Current Method Selection

- Clean QSNN protocol: FROZEN
- Main baseline: Classical Timing PGD
- Main proposed method: Adaptive TEMP-DRIFT
- Gradient Adaptive TEMP-DRIFT: rejected as non-beneficial
- Quantum-refined TEMP-DRIFT: rejected as non-beneficial
- Defense: still provisional

## Result Artifacts

- `results/final_attack_comparison.json`
- `results/final_attack_comparison.csv`
- `results/final_attack_samples.csv`
- `results/final_attack_report.md`
- `results/gradient_adaptive_temp_drift_validation.json`
- `results/quantum_refined_temp_drift_validation.json`
