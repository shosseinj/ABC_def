# Clean Performance Benchmark Comparison

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

Parameter count: **25,482**.

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
| Ours | Our SNN | SNN | Native temporal SHD recurrent LIF SNN; 5 deterministic seeds | 46.72% +/- 4.28% | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Main model |

### Our SHD SNN Multi-Seed Baseline

The fixed clean protocol used all 700 cochlear input channels, 100 ordered binary spike-occupancy bins over a 1.4-second window, and no normalization. A compact recurrent LIF network (`Linear(700,128)-recurrent-LIF(128)-Linear(128,20)`) was trained with one stratified validation split (`split_seed = 42`) and five deterministic model seeds. Checkpoints were selected by validation accuracy, then validation loss, then earliest epoch before one final official-test evaluation per seed.

| Seed | Best Validation Accuracy | Final Test Accuracy | Macro-F1 | Best Epoch | Training Runtime |
|---:|---:|---:|---:|---:|---:|
| 42 | 47.30% | 51.77% | 48.24% | 38 | 254.08 s |
| 123 | 45.89% | 46.69% | 43.64% | 39 | 246.67 s |
| 777 | 34.38% | 39.93% | 35.75% | 14 | 132.50 s |
| 2026 | 46.32% | 47.66% | 44.20% | 40 | 241.35 s |
| 6543 | 43.50% | 47.57% | 42.63% | 19 | 158.68 s |

| Aggregate Metric | Mean +/- Sample SD |
|---|---:|
| Validation accuracy | 43.48% +/- 5.28% |
| Test accuracy | 46.72% +/- 4.28% |
| Macro-F1 | 42.89% +/- 4.53% |

Parameter count: **108,692**. Mean training runtime: **206.66 s**. This weak clean baseline is retained without post-test tuning.

## CIFAR10-DVS

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Time Is All It Takes | SpikingResformer | SNN | Integer event grid | 82.90% | Literature reference |
| Ours | Our SNN | SNN | Same internal split / preprocessing | TBD | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Optional extension |

## Iris

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Ours | Our QSNN | QSNN | TTFS | 94.67% | Proof-of-concept |
