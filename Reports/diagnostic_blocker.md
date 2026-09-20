# TEMP-DRIFT workflow blocker — Phase 0.75

**Phase:** 0.75, specification freeze  
**Classification:** true scientific blocker under `AGENTS.md`  
**Date:** 2026-09-20

## Blocker

The benchmark specification cannot truthfully freeze all required model/checkpoint and attack fields:

1. **DVS-Gesture:** the dataset is present, but the repository contains no DVS-Gesture model implementation, training definition, split manifest, or checkpoint for any required seed. Selecting an architecture/training protocol would be a new scientific definition, not repository recovery.
2. **CIFAR10-DVS:** only the seed-42 checkpoint exists. Checkpoints for seeds 123, 777, 2026, and 6543 are absent.
3. **N-MNIST:** five SNN checkpoints exist, but the Tonic `data/mnist/NMNIST` event dataset is absent, so the official test subset and its deterministic clean-correct hash cannot be computed or verified.
4. **Attack:** no implementation of the locked white-box PIL-PGD soft-retiming attack (including its forward/backward behavior and penalties) was found. The conservative strict projector is a contract utility, not a substitute attack implementation.

These missing items prevent the required resolved model/checkpoint fields, exact test subset hashes, preprocessing validation, and attack-query definition. Writing `Reports/benchmark_specification.json` now would either leave unresolved fields or invent scientific choices, both prohibited.

## Commands tried and evidence

- Repository inventory builder using the configured interpreter: `python -m ResearchLoop.tools.build_phase0_inventory`; output in `Reports/logs/phase_0_inventory_build.log` and `Reports/repository_inventory.json`.
- Contract suite: configured Python `-m unittest discover -s ResearchLoop/tests -v`; 11/11 passed in `Reports/logs/phase_0_5_contract_tests.log`.
- Phase 0.75 model/data/attack preflight using the configured interpreter; full output in `Reports/logs/phase_0_75_preflight.log`.

Observed preflight facts:

- `nmnist_data: false`
- `dvs_data: true`, `dvs_models: []`, `dvs_checkpoints: []`
- `cifar_data: true`; seed 42 checkpoint present, four required seed checkpoints absent
- `pil_pgd_sources: []`

## Impact

Phase 0.75 cannot pass its independent gate. Phases 1–9 must not start because they depend on a complete frozen specification. No locked-protocol attack experiment was launched and no metric was fabricated or copied.

## Exact remediation required

An authorized scientific owner must provide or approve all of the following:

1. A DVS-Gesture SNN architecture and complete training/preprocessing/split protocol, followed by hash-verified checkpoints for seeds 42, 123, 777, 2026, and 6543.
2. CIFAR10-DVS checkpoints for seeds 123, 777, 2026, and 6543 produced under the same frozen seed-42 architecture/protocol, or an explicit approved replacement protocol for all five seeds.
3. Restore/download and integrity-check the official N-MNIST train/test event data under `data/mnist`, then compute the deterministic clean-correct attacked-subset IDs/hash for every frozen seed/model as specified.
4. Provide or approve an implementation-level definition of PIL-PGD matching arXiv:2602.03284v1: strict projected forward pass, soft retiming surrogate backward pass, capacity and budget penalties, iterations, query accounting, and packet collision handling. It must be independently tested against `ResearchLoop/core/audit.py`.
5. After these are available, resolve every model/checkpoint/split/preprocessing field in `Reports/benchmark_specification.json`, hash all inputs, run the Phase 0.75 gate, and only then continue to Phase 1.
