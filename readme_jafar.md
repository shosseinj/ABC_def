# Clean Performance Benchmark Comparison

## N-MNIST

| Source | Model | Model Type | Input / Setting | Clean Accuracy | Role |
|---|---|---|---|---:|---|
| Time Is All It Takes | VGGSNN | SNN | Integer event grid | 99.71% | Literature reference |
| Input-Specific and Universal Adversarial Attack... | Reported SNN | SNN | Full spiking input | 98.19% | Literature reference |
| Ours | Our SNN | SNN | Same internal split / preprocessing | TBD | Internal baseline |
| Ours | Our QSNN | QSNN | Quantum temporal encoding | TBD | Main model |

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
