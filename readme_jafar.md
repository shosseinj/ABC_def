# Clean Performance Benchmark Comparison

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
| Ours | Our SNN | SNN | Same internal split / preprocessing | TBD | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Main model |

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
