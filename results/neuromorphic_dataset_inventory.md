# Neuromorphic Dataset Inventory

Data preparation only. Native events/spikes were loaded without static conversion, preprocessing, or experimental train/validation split creation.

| Dataset | Status | Native partitions | Samples | Classes | Sensor/input | Fields |
|---|---|---|---:|---:|---|---|
| SHD | FAILED | -- | -- | -- | -- | -- |
| DVS Gesture | FAILED | -- | -- | -- | -- | -- |
| CIFAR10-DVS | FAILED | -- | -- | -- | -- | -- |

## Details

### SHD

- Status: `FAILED`
- Storage: `data\shd`
- Error: `ValueError: zero-size array to reduction operation minimum which has no identity`

### DVS Gesture

- Status: `FAILED`
- Storage: `data\dvs_gesture`
- Error: `RuntimeError: File not found or corrupted.`

### CIFAR10-DVS

- Status: `FAILED`
- Storage: `data\cifar10_dvs`
- Error: `RuntimeError: File not found or corrupted.`
