from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "Reports"
CONFIGURED_PYTHON = Path(json.loads((ROOT / "ResearchLoop/config.json").read_text(encoding="utf-8"))["python"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def atomic_json(path: Path, value: object) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def files_under(relative: str, suffix: str | None = None) -> list[Path]:
    base = ROOT / relative
    if not base.exists():
        return []
    files = [p for p in base.rglob("*") if p.is_file()]
    return sorted(p for p in files if suffix is None or p.suffix == suffix)


def tree_summary(relative: str) -> dict[str, object]:
    files = files_under(relative)
    return {
        "exists": (ROOT / relative).exists(),
        "file_count": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "top_level": sorted(p.name for p in (ROOT / relative).iterdir()) if (ROOT / relative).is_dir() else [],
    }


def main() -> None:
    if Path(sys.executable).resolve() != CONFIGURED_PYTHON.resolve():
        raise RuntimeError(f"wrong interpreter: {sys.executable}; expected {CONFIGURED_PYTHON}")
    now = datetime.now(timezone.utc).isoformat()
    package_names = ["torch", "torchvision", "tonic", "numpy", "scipy", "pandas", "scikit-learn", "pennylane", "pytest"]
    packages = {name: importlib.metadata.version(name) for name in package_names}
    import torch

    checkpoint_files = files_under("checkpoints")
    checkpoint_inventory = [
        {"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in checkpoint_files
    ]
    config_files = files_under("configs", ".json")
    dataset_paths = {
        "N-MNIST": "data/mnist/NMNIST",
        "DVS-Gesture": "data/dvs_gesture/DVSGesture",
        "CIFAR10-DVS": "data/cifar10_dvs/CIFAR10DVS",
        "SHD (prior work; outside benchmark)": "data/shd/SHD",
        "MNIST (prior work; outside benchmark)": "data/MNIST",
    }
    inventory = {
        "generated_at": now,
        "scope": "Phase 0 repository inspection; no benchmark metrics generated",
        "git_head": "7c30433 (observed before artifact generation)",
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "packages": packages,
            "torch": {
                "version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_version": torch.version.cuda,
                "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
            },
            "disk_free_bytes": shutil.disk_usage(ROOT).free,
        },
        "source": {
            "models": [p.relative_to(ROOT).as_posix() for p in files_under("models", ".py")],
            "attacks": [p.relative_to(ROOT).as_posix() for p in files_under("attacks", ".py")],
            "defenses": [p.relative_to(ROOT).as_posix() for p in files_under("defenses", ".py")],
            "metrics": [p.relative_to(ROOT).as_posix() for p in files_under("metrics", ".py")],
            "experiment_modules": [p.relative_to(ROOT).as_posix() for p in files_under("experiments", ".py")],
            "script_count": len(files_under("scripts", ".py")),
            "test_count": len(files_under("tests", ".py")) + len(files_under("ResearchLoop/tests", ".py")),
            "benchmark_core": ["ResearchLoop/core/projector.py", "ResearchLoop/core/audit.py"],
        },
        "checkpoints": checkpoint_inventory,
        "configs": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256(p)} for p in config_files
        ],
        "datasets": {name: {"path": path, **tree_summary(path)} for name, path in dataset_paths.items()},
        "stored_outputs": {"results": tree_summary("results"), "reports": tree_summary("Reports")},
        "preprocessing_and_loaders": {
            "N-MNIST": ["experiments/nmnist/snn_baseline.py", "experiments/nmnist/hybrid_data.py"],
            "CIFAR10-DVS": ["scripts/train_cifar10_dvs_snn_seed42.py", "scripts/compare_cifar10_dvs_resolution_seed42.py"],
            "dataset_preparation": "scripts/prepare_neuromorphic_datasets.py",
            "canonical_event_layout": "[time, polarity, y, x] in prior N-MNIST work",
        },
        "experiment_entry_points": [
            "scripts/train_nmnist_snn_seed42.py",
            "scripts/run_nmnist_snn_multiseed.py",
            "scripts/evaluate_nmnist_snn_test_once.py",
            "scripts/train_cifar10_dvs_snn_seed42.py",
            "scripts/prepare_neuromorphic_datasets.py",
            "scripts/run_nmnist_attack_protocol_v3_auditable_seed42.py",
        ],
        "gaps": [
            "No TEMP-DRIFT benchmark run under the locked paper protocol is complete.",
            "DVS-Gesture has no repository benchmark model/checkpoint or dataset-specific attack runner.",
            "CIFAR10-DVS has only seed-42 baseline checkpoints, not five frozen seeds.",
            "N-MNIST prior attack outputs use a different epsilon/query protocol and cannot be relabeled as paper-comparable.",
            "Raw-event preprocessing must be reconciled with the locked T=10 capacity-1 packet representation before specification freeze.",
            "requirements.txt pins torch 2.9.1/torchvision 0.24.1, while the configured environment has torch 2.5.1+cu124/torchvision 0.20.1+cu124.",
        ],
    }
    inventory_path = REPORTS / "repository_inventory.json"
    atomic_json(inventory_path, inventory)

    dataset_rows = []
    for name, value in inventory["datasets"].items():
        dataset_rows.append(f"| {name} | `{value['path']}` | {value['file_count']} | {value['bytes']} |")
    report = f"""# Phase 0 — Repository inspection

**Inspection time:** {now}  
**Outcome:** Repository inventory completed; no benchmark experiment was run.

## Environment

- Configured interpreter: `{sys.executable}` (Python {platform.python_version()})
- PyTorch: {torch.__version__}; CUDA available: {torch.cuda.is_available()}; CUDA runtime: {torch.version.cuda}
- GPU(s): {', '.join(inventory['environment']['torch']['devices']) or 'none'}
- Free disk: {inventory['environment']['disk_free_bytes'] / 1e9:.1f} GB
- Dependency versions are recorded in `Reports/repository_inventory.json` and `Reports/logs/phase_0_environment.log`.

## Repository inventory

- Models: {len(inventory['source']['models'])} Python modules, including classical SNN and PennyLane QSNN paths.
- Checkpoints: {len(checkpoint_inventory)} files; every path, size, and SHA-256 is recorded in the machine-readable inventory.
- Configurations: {len(config_files)} JSON files, each hashed.
- Entry points: {inventory['source']['script_count']} Python scripts; {inventory['source']['test_count']} Python test files.
- Attack code includes legacy TEMP-DRIFT variants plus the new independent `ResearchLoop/core/projector.py` and `audit.py` contract utilities.
- Defenses currently consist primarily of `defenses/quantum_temp.py`; locked-protocol defense evaluation has not run.

## Dataset storage

| Dataset | Path | Files | Bytes |
|---|---|---:|---:|
{chr(10).join(dataset_rows)}

Presence does not imply completeness. N-MNIST, DVS-Gesture, and CIFAR10-DVS directories contain archives/extracted material, but only N-MNIST has five repository SNN checkpoints. DVS-Gesture has no benchmark checkpoint; CIFAR10-DVS has seed-42 checkpoints only.

## Representation and provenance findings

Prior N-MNIST code uses Tonic event data and `[time, polarity, y, x]` framed representations, commonly with 10 temporal bins. Existing attack results use earlier epsilon/query-matched protocols and are **NON_COMPARABLE** to the locked paper benchmark unless every matching field is independently established. The new benchmark contract requires unit-packet identity, fixed event lines, discrete bins `[0,10)`, capacity-1, and clean-correct ASR.

## Gaps that affect later phases

{chr(10).join('- ' + gap for gap in inventory['gaps'])}

Phase 0 is an inspection gate only. These gaps do not invalidate this inventory, but they must be resolved by the benchmark-contract and specification-freeze phases before dataset experiments.
"""
    report_path = REPORTS / "phase_0_report.md"
    atomic_text(report_path, report)

    readme_path = ROOT / "readme_jafar.md"
    readme = readme_path.read_text(encoding="utf-8")
    marker = "> **Active autonomous workflow status:**"
    active = f"> **Active autonomous workflow status:** Phase 0 inventory regenerated at {now}; independent gate pending. No locked-protocol benchmark experiment has run.\n"
    lines = readme.splitlines()
    if any(line.startswith(marker) for line in lines):
        lines = [active.rstrip() if line.startswith(marker) else line for line in lines]
    else:
        lines.insert(2, active.rstrip())
    atomic_text(readme_path, "\n".join(lines) + "\n")

    artifacts = [inventory_path, report_path, readme_path, REPORTS / "logs/phase_0_environment.log"]
    receipt = {
        "phase": "0",
        "status": "PASS",
        "generated_at": now,
        "commands": [
            f'"{sys.executable}" ResearchLoop/tools/build_phase0_inventory.py',
            f'"{sys.executable}" ResearchLoop/tools/gate.py <project-root> ResearchLoop/config.json 0',
        ],
        "artifacts": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256(p), "bytes": p.stat().st_size}
            for p in artifacts
        ],
        "tests": ["Independent phase gate and ResearchLoop unittest discovery (pending execution after receipt creation)"],
        "limitations": inventory["gaps"],
    }
    atomic_json(REPORTS / "receipts/phase_0.json", receipt)

    status_path = REPORTS / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {"phases": {}}
    status.update({"current_phase": "0", "status": "RUNNING", "updated_at": now, "reason": "Phase 0 artifacts built; independent gate pending"})
    status.setdefault("phases", {})["0"] = {
        "status": "GATE_PENDING", "attempts": int(status.get("phases", {}).get("0", {}).get("attempts", 0)),
        "artifacts": [p.relative_to(ROOT).as_posix() for p in artifacts],
    }
    atomic_json(status_path, status)
    print(json.dumps({"status": "BUILT", "checkpoints": len(checkpoint_inventory), "configs": len(config_files), "datasets": inventory["datasets"]}, indent=2))


if __name__ == "__main__":
    main()
