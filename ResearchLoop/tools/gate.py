from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


PLACEHOLDERS = ("todo", "tbd", "placeholder", "invented", "dummy", "resolve_from_repository")
DATASET_SLUG = {"N-MNIST": "nmnist", "DVS-Gesture": "dvs_gesture", "CIFAR10-DVS": "cifar10_dvs"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def nonempty(path: Path, errors: list[str]) -> None:
    if not path.is_file() or path.stat().st_size < 40:
        errors.append(f"missing or empty artifact: {path}")


def check_report(path: Path, errors: list[str]) -> None:
    nonempty(path, errors)
    if path.is_file():
        lowered = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(token in lowered for token in PLACEHOLDERS):
            errors.append(f"report contains unresolved placeholder marker: {path}")


def check_receipt(repo: Path, phase_id: str, errors: list[str]) -> None:
    receipt = repo / "Reports" / "receipts" / f"phase_{phase_id}.json"
    nonempty(receipt, errors)
    if not receipt.is_file():
        return
    try:
        data = load_json(receipt)
    except Exception as exc:
        errors.append(f"invalid receipt JSON: {exc}")
        return
    if data.get("status") != "PASS":
        errors.append("receipt status is not PASS")
    for key in ("commands", "artifacts", "tests"):
        if not data.get(key):
            errors.append(f"receipt lacks evidence field: {key}")


def self_tests(repo: Path, python: str, errors: list[str]) -> None:
    cmd = [python, "-m", "unittest", "discover", "-s", "ResearchLoop/tests", "-v"]
    result = subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
    if result.returncode:
        errors.append("independent contract tests failed:\n" + (result.stdout + result.stderr)[-4000:])


def finite_number(row: dict[str, str], key: str, errors: list[str], rownum: int) -> float | None:
    try:
        value = float(row[key])
        if not math.isfinite(value):
            raise ValueError
        return value
    except Exception:
        errors.append(f"row {rownum}: {key} must be finite")
        return None


def check_dataset_results(repo: Path, dataset: str, errors: list[str]) -> None:
    spec_path = repo / "Reports" / "benchmark_specification.json"
    if not spec_path.is_file():
        errors.append("benchmark specification JSON is missing")
        return
    spec = load_json(spec_path)
    ds = spec.get("datasets", {}).get(dataset)
    if not ds:
        errors.append(f"dataset absent from frozen specification: {dataset}")
        return
    if "resolve_" in str(ds.get("our_model", "")).lower():
        errors.append(f"our_model was not resolved for {dataset}")
    result_path = repo / "Reports" / "results" / DATASET_SLUG[dataset] / "summary.csv"
    nonempty(result_path, errors)
    if not result_path.is_file():
        return
    with result_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = (repo / "ResearchLoop" / "reference" / "result_columns.txt").read_text(encoding="utf-8").split()
    if not rows:
        errors.append(f"no result rows: {result_path}")
        return
    missing_columns = sorted(set(required) - set(rows[0]))
    if missing_columns:
        errors.append("missing result columns: " + ", ".join(missing_columns))
        return

    observed: set[tuple[str, int, str, str]] = set()
    for i, row in enumerate(rows, 2):
        if row["dataset"] != dataset:
            errors.append(f"row {i}: wrong dataset")
        try:
            seed = int(row["seed"])
            beta = int(float(row["beta"]))
        except ValueError:
            errors.append(f"row {i}: invalid seed/beta")
            continue
        observed.add((row["budget_type"], beta, row["representation"], str(seed)))
        for key in ("n_attacked", "clean_correct_count", "attack_success_count", "clean_accuracy",
                    "adversarial_accuracy", "asr", "b_inf_max", "b1_max", "b0_max",
                    "mean_abs_dt", "changed_event_ratio", "frame_l0", "frame_l1", "frame_l2",
                    "frame_linf", "queries_mean", "attack_time_s_mean", "gpu_time_s_mean"):
            finite_number(row, key, errors, i)
        if row["audit_pass"].strip().lower() not in ("true", "1", "pass"):
            errors.append(f"row {i}: independent audit did not pass")
        for key in ("checkpoint_sha256", "config_sha256"):
            if len(row[key].strip()) != 64:
                errors.append(f"row {i}: invalid {key}")
        for key in ("clean_accuracy", "adversarial_accuracy", "asr"):
            value = finite_number(row, key, errors, i)
            if value is not None and not 0 <= value <= 100:
                errors.append(f"row {i}: {key} outside [0,100]")

    expected: set[tuple[str, int, str, str]] = set()
    for representation in ds["representations"]:
        for btype, betas in ds["budgets"][representation].items():
            for beta in betas:
                for seed in spec["seeds"]:
                    expected.add((btype, int(beta), representation, str(seed)))
    missing = expected - observed
    if missing:
        preview = sorted(missing)[:20]
        errors.append(f"missing {len(missing)} required seed/budget/representation rows; first: {preview}")


def run_gate(repo: Path, config: dict[str, Any], phase: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    phase_id = phase["id"]
    check_report(repo / phase["report"], errors)
    check_receipt(repo, phase_id, errors)
    for item in phase.get("requirements", []):
        nonempty(repo / item, errors)
    self_tests(repo, config["python"], errors)

    if phase_id == "0_75":
        spec_path = repo / "Reports" / "benchmark_specification.json"
        if spec_path.is_file():
            try:
                spec = load_json(spec_path)
                if spec.get("frozen") is not True:
                    errors.append("benchmark specification is not frozen")
                if spec.get("seeds") != config["seeds"]:
                    errors.append("seed policy differs from config")
                if spec.get("time_bins") != 10:
                    errors.append("paper-comparable time_bins must be 10")
            except Exception as exc:
                errors.append(f"invalid benchmark specification: {exc}")
    if phase.get("dataset"):
        check_dataset_results(repo, phase["dataset"], errors)
    return not errors, errors


if __name__ == "__main__":
    repo = Path(sys.argv[1]).resolve()
    config = load_json(Path(sys.argv[2]))
    phases = load_json(repo / "ResearchLoop" / "phases.json")
    phase = next(p for p in phases if p["id"] == sys.argv[3])
    passed, errors = run_gate(repo, config, phase)
    print(json.dumps({"status": "PASS" if passed else "FAIL", "errors": errors}, indent=2))
    raise SystemExit(0 if passed else 1)

