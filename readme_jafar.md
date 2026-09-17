# Clean Performance Benchmark Comparison

## Summary

| Dataset | Model | Clean Accuracy | Re-audited | Status |
|---|---|---:|---|---|
| N-MNIST | SNN | 98.35% +/- 0.18% | No | Baseline complete |
| SHD | SNN | 65.99% +/- 2.33% | **Yes - VERIFIED** | Baseline complete |
| DVS Gesture | SNN | TBD | No | Pending |
| CIFAR10-DVS | SNN | TBD | No | 64x64 resolution check complete; held-out test pending |

## Dataset Availability

| Dataset | Status | Native partitions | Storage |
|---|---|---|---|
| N-MNIST | Existing | Train/test dataset already present | `data/nmnist/` |
| SHD | READY | Train: 8,156; test: 2,264 | `data/shd/` |
| DVS Gesture | READY | Train: 1,077; test: 264 | `data/dvs_gesture/` |
| CIFAR10-DVS | READY | 10,000 samples; no official train/test partition | `data/cifar10_dvs/` |

Availability reflects native event/spike loading only. No experimental train/validation splits, static-frame conversion, preprocessing, or training was performed in this preparation phase. Full verification metadata is in `results/neuromorphic_dataset_inventory.md`.

## N-MNIST

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Time Is All It Takes | VGGSNN | SNN | Integer event grid | 99.71% | Literature reference |
| Input-Specific and Universal Adversarial Attack... | Reported SNN | SNN | Full spiking input | 98.19% | Literature reference |
| Ours | Our SNN | SNN | Native-event convolutional LIF SNN; 5 deterministic seeds | 98.35% +/- 0.18% | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Main model |

### Our N-MNIST SNN Multi-Seed Baseline

The fixed clean protocol used 10 ordered, polarity-separated 34x34 event-count frames, a convolutional LIF SNN, the same deterministic train/validation split (`split_seed = 42`), and five model seeds. Checkpoints were selected by validation accuracy and then validation loss before one final evaluation per seed on the official test set.

| Seed | Best Validation Accuracy | Final Test Accuracy | Macro-F1 | Best Epoch | Training Runtime |
|---:|---:|---:|---:|---:|---:|
| 42 | 98.24% | 98.49% | 98.48% | 11 | 615.05 s |
| 123 | 97.96% | 98.14% | 98.13% | 8 | 508.07 s |
| 777 | 98.36% | 98.53% | 98.52% | 13 | 662.11 s |
| 2026 | 97.80% | 98.16% | 98.15% | 6 | 471.25 s |
| 6543 | 98.30% | 98.41% | 98.40% | 11 | 931.77 s |

| Aggregate Metric | Mean +/- Sample SD |
|---|---:|
| Validation accuracy | 98.13% +/- 0.24% |
| Test accuracy | 98.35% +/- 0.18% |
| Macro-F1 | 98.34% +/- 0.19% |

Parameter count: **25,482**. Re-audit: not yet independently re-evaluated.

**Re-audit status**: Pending. Test results were evaluated once per seed after training. Independent re-evaluation script not yet implemented for N-MNIST.

### N-MNIST QSNN Seed-42 Development Ablation

This validation-only study reused the frozen SNN/QSNN official-training split (`split_seed = 42`, SHA-256 `a12176ce117ab9a85dd29d277901f8617ad2b5427dd3f976dbba436942f70198`). Native `x,y,t,p` events were reduced to ordered, polarity-preserving temporal and spatial channels; no static MNIST images were created. All runs used seed 42, angle encoding with data re-uploading, trainable RY/RZ gates, ring entanglement, Pauli-Z measurements, Adam (`learning_rate = 0.003`), batch size 256, and 15 epochs.

| Configuration | Temporal Bins | Spatial-Polarity Channels | Qubits | Blocks | Input Features | Parameters | Best Validation Accuracy | Best Validation Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T4-S8-Q8-B4 baseline | 4 | 8 | 8 | 4 | 32 | 154 | 69.56% | 1.018668 |
| T8-S8-Q8-B4 | 8 | 8 | 8 | 4 | 64 | 154 | 48.32% | 1.587339 |
| T10-S8-Q8-B4 | 10 | 8 | 8 | 4 | 80 | 154 | 36.84% | 1.806725 |
| T4-S16-Q8-B4 | 4 | 16 | 8 | 4 | 64 | 154 | 36.76% | 1.820386 |
| T4-S8-Q8-B6 | 4 | 8 | 8 | 6 | 32 | 186 | 75.88% | 0.850372 |
| T4-S8-Q12-B6 | 4 | 8 | 12 | 6 | 32 | 274 | **76.72%** | **0.833559** |

The selected development candidate is **T4-S8-Q12-B6**, improving seed-42 validation accuracy by **7.16 percentage points** over the original sanity baseline. Its advantage over T4-S8-Q8-B6 is only 0.84 percentage points and requires multi-seed confirmation. The official N-MNIST test partition was not accessed, so the main `Our QSNN` clean-accuracy entry remains **TBD** until the architecture is frozen, multi-seed training is complete, and one final official-test evaluation is performed. Full development artifacts are documented in `results/nmnist_qsnn_ablation_report.md`.

### N-MNIST QSNN Seed-42 Timing-Attack Comparison

The selected T4-S8-Q12-B6 checkpoint was evaluated on the same 100 clean-correct validation samples, with 10 samples per class. The official N-MNIST test partition was not instantiated. Both attacks preserved coordinates, polarity, labels, event counts, timestamp ordering, and the original clean time window; the perturbation bound was 2%, 5%, or 10% of each sample's inclusive clean duration. PGD used 20 surrogate-gradient steps, while derivative-free TEMP-DRIFT evaluated 1,600 candidates per sample, so their search budgets are not directly comparable.

| Epsilon | Attack | Attack Success Rate | Attacked Accuracy | Mean 1-Fidelity | Mean Trace Distance | Feasibility |
|---|---|---:|---:|---:|---:|---:|
| 2% | PGD | 8% | 92% | 0.042797 | 0.177274 | 100% |
| 2% | TEMP-DRIFT | **22%** | **78%** | 0.073987 | 0.263669 | 100% |
| 5% | PGD | 32% | 68% | 0.274971 | 0.479222 | 100% |
| 5% | TEMP-DRIFT | **76%** | **24%** | 0.422699 | 0.641635 | 100% |
| 10% | PGD | 63% | 37% | 0.663569 | 0.792713 | 100% |
| 10% | TEMP-DRIFT | **99%** | **1%** | 0.890414 | 0.942616 | 100% |

| Epsilon | PGD Only Successful | TEMP-DRIFT Only Successful | Both Successful | Both Robust |
|---|---:|---:|---:|---:|
| 2% | 0 | 14 | 8 | 78 |
| 5% | 0 | 44 | 32 | 24 |
| 10% | 0 | 36 | 63 | 1 |

Under this frozen exploratory protocol, TEMP-DRIFT had higher ASR than PGD at every tested epsilon, by 14, 44, and 36 percentage points respectively. This is single-seed validation evidence with unequal attack-search budgets; it does not establish a general robustness or attack-superiority claim. Full aggregate and per-sample artifacts are in `results/nmnist_attack_comparison_seed42_report.md`, `results/nmnist_attack_comparison_seed42.json`, `results/nmnist_attack_comparison_seed42.csv`, and `results/nmnist_attack_samples_seed42.csv`.

## DVS Gesture

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Time Is All It Takes | VGGSNN | SNN | Integer event grid | 94.79% | Literature reference |
| Input-Specific and Universal Adversarial Attack... | Reported SNN | SNN | Full spiking input | 86.36% | Literature reference |
| Ours | Our SNN | SNN | Same internal split / preprocessing | TBD | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Main model |

## SHD

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Input-Specific and Universal Adversarial Attack... | Reported SNN | SNN | Neuromorphic audio spikes | 76.59% | Literature reference |
| Ours | Our SNN | SNN | Native temporal SHD recurrent LIF SNN; 5 deterministic seeds | 65.99% +/- 2.33% | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Main model |

### Our SHD SNN Multi-Seed Baseline

The current clean protocol uses all 700 cochlear input channels, 100 ordered binary spike-occupancy bins over a 1.4-second window, and no normalization. A compact recurrent LIF network (`Linear(700,128)-recurrent-LIF(128)-Linear(128,20)`) uses one stratified validation split (`split_seed = 42`) and five deterministic model seeds. Training used a total budget of 350 epochs with `ReduceLROnPlateau(mode="max", factor=0.5, patience=10, min_lr=1e-5)` and early-stopping patience 40.

| Seed | Best Validation | Final Test | Macro-F1 | Best Epoch | Stopping Epoch | LR Reductions | Final LR | Extension Runtime |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 78.86% | 65.77% | 64.68% | 271 | 311 | 7 | 0.000010 | 878.26 s |
| 123 | 81.68% | 69.79% | 69.11% | 217 | 257 | 5 | 0.00003125 | 567.76 s |
| 777 | 77.39% | 66.21% | 65.63% | 232 | 272 | 7 | 0.000010 | 651.97 s |
| 2026 | 76.90% | 64.00% | 63.20% | 233 | 273 | 6 | 0.000015625 | 655.77 s |
| 6543 | 82.05% | 64.18% | 63.90% | 190 | 230 | 5 | 0.00003125 | 432.93 s |

| Aggregate Metric | Mean +/- Sample SD |
|---|---:|
| Validation accuracy | 79.38% +/- 2.39% |
| Test accuracy | 65.99% +/- 2.33% |
| Macro-F1 | 65.30% +/- 2.31% |

Parameter count: **108,692**. Each validation-selected checkpoint was evaluated once on the official SHD test partition after training and model selection were complete.

**Re-audit status**: All 5 checkpoints independently re-evaluated on the official SHD test partition. Every seed produced an exact match (zero difference in accuracy, macro-F1, loss, and confusion matrices). Verdict: **VERIFIED**. Evidence: `results/shd_snn_test_reaudit.json`, `results/shd_snn_test_reaudit_report.md`.

## CIFAR10-DVS

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Time Is All It Takes | SpikingResformer | SNN | Integer event grid | 82.90% | Literature reference |
| Ours | Our SNN | SNN | 10-bin polarity-separated 64x64 event frames; validation-only | TBD | Internal baseline; resolution check ACCEPT |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Optional extension |

### CIFAR10-DVS 64x64 Resolution Check

The comparison reused the frozen stratified split (`split_seed = 42`, SHA-256 `629571c70b6202629206d7a449a41e02f124efba2cf469f966c19ea4cdf288b8`) with 8,000 training and 1,000 validation samples; the 1,000-sample held-out partition was not accessed. Both runs used seed 42, 10 temporal bins, separate polarity channels, additive event counts, per-sample max normalization, the same convolutional LIF pattern and LIF settings, AdamW, `ReduceLROnPlateau` stepped on validation accuracy, and the same checkpoint-selection rule. The 64x64 representation mapped native coordinates with deterministic floor division before accumulation.

The earlier 128x128 run was interrupted and its saved checkpoint metadata did not match the observed run log, so both resolutions were rerun under the same cached-frame protocol. For reporting, "substantially faster" was operationalized as at least 1.25x mean epoch speedup.

| Resolution | Best Validation Accuracy | Best Validation Loss | Best Epoch | Mean Epoch Runtime | Peak GPU Allocated | Parameters | Throughput |
|---|---:|---:|---:|---:|---:|---:|---:|
| 128x128 | 50.40% | 1.9122 | 6 | 18.5 s | 0.820 GB | 187,402 | 433.6 samples/s |
| 64x64 | **54.80%** | **1.8448** | 21 | **14.2 s** | **0.253 GB** | 64,522 | **564.4 samples/s** |

The 64x64 run was 1.31x faster, used less peak allocated GPU memory, and improved validation accuracy by 4.40 percentage points. `scheduler.step(validation_accuracy)` was called 36 times. Selection verdict: **CIFAR10-DVS 64x64: ACCEPT**. No held-out test evaluation or 350-epoch training was performed in this comparison.

Evidence and artifacts: `results/cifar10_dvs_resolution_comparison_seed42.json`, `results/cifar10_dvs_resolution_128x128_seed42_history.csv`, `results/cifar10_dvs_resolution_64x64_seed42_history.csv`, and the corresponding LR-history and checkpoint files.

## Iris

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Ours | Our QSNN | QSNN | TTFS | 94.67% | Proof-of-concept |
