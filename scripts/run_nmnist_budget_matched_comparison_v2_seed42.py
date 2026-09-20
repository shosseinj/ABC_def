"""Corrected, auditable Seed-42 N-MNIST budget-matched comparison.

Run only with the project interpreter documented in REQUIRED_PYTHON.  The
audited v3 artifact supplies the original condition and frozen PGD results;
new work is limited to scaled TEMP conditions and a separately calibrated
wall-clock condition.  Calibration never uses the evaluation manifest.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.nmnist.snn_baseline import events_to_frames
import scripts.run_nmnist_common_attack_protocol_seed42 as legacy
import scripts.run_nmnist_temp_drift_v2_seed42 as frozen_temp
from scripts.run_nmnist_attack_protocol_v2_canonical_seed42 import canonical_frames_torch

SEED = 42
VERSION = "nmnist-budget-matched-v2-seed42"
METHOD = "TEMP-DRIFT-v2-budget-scaled"
REQUIRED_PYTHON = Path(r"C:\Users\jafari.h\Desktop\ai_project\.venv\Scripts\python.exe")
SOURCE = ROOT / "results/nmnist_attack_protocol_v3_auditable_seed42"
DEST = ROOT / "results/nmnist_budget_matched_comparison_v2_seed42"
RECORDS = DEST / "records"
SPLIT = ROOT / "results/nmnist_snn_multiseed_split.json"
EPSILONS = (0.05, 0.10)
BOOTSTRAPS = 20_000
CALIBRATION_REPEATS = 2
CALIBRATION_EPSILON = 0.10
WALLCLOCK_Q_GRID = (800, 1200, 1600, 2000, 2400, 3200, 4000, 4800, 5600, 6400)
CONDITIONS = {
    "access_candidates_21": {"q": 21, "initial": 13, "generations": 4, "per_generation": 2,
                             "match": "PGD candidate evaluations"},
    "access_forwards_41": {"q": 41, "initial": 13, "generations": 4, "per_generation": 7,
                           "match": "PGD attack-internal forwards"},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty CSV: {path}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(rows[0]) + sorted(set().union(*(row.keys() for row in rows)) - set(rows[0]))
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def synchronize() -> None:
    torch.cuda.synchronize()


def timed(callable_):
    synchronize()
    start = time.perf_counter()
    result = callable_()
    synchronize()
    return result, time.perf_counter() - start


def scaled_budget(requested_q: int) -> dict:
    """Apply the frozen 37.5%/four-generation rule and state adjustment."""
    initial = max(12, round(0.375 * requested_q))
    per_generation = max(0, round((requested_q - initial) / 4))
    actual_q = initial + 4 * per_generation
    return {"requested_q": requested_q, "q": actual_q, "initial": initial,
            "generations": 4, "per_generation": per_generation,
            "adjustment": actual_q - requested_q}


def source_records() -> tuple[list[dict], list[dict], dict]:
    status = json.loads((SOURCE / "STATUS.json").read_text(encoding="utf-8"))
    if status.get("fully_audited") is not True or status.get("failed_records") != 0:
        raise RuntimeError("Frozen v3 source is not fully audited")
    manifest_doc = json.loads((SOURCE / "records_manifest.json").read_text(encoding="utf-8"))
    failures = []
    for item in manifest_doc["records"]:
        path = SOURCE / item["record_path"]
        actual = sha256(path) if path.is_file() else None
        if actual != item["sha256"]:
            failures.append({"record_path": item["record_path"], "expected": item["sha256"], "actual": actual})
    if failures:
        raise RuntimeError(f"Frozen v3 record hash failures: {len(failures)}")
    with (SOURCE / "per_sample_results.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != manifest_doc["record_count"] or len(rows) != 2400:
        raise RuntimeError("Frozen v3 row count mismatch")
    return rows, manifest_doc["records"], {
        "status_sha256": sha256(SOURCE / "STATUS.json"),
        "audit_sha256": sha256(SOURCE / "audit.json"),
        "rows_sha256": sha256(SOURCE / "per_sample_results.csv"),
        "records_manifest_sha256": sha256(SOURCE / "records_manifest.json"),
        "verified_record_count": len(manifest_doc["records"]),
    }


def temp_attack(model, events, label: int, epsilon: float, rng, budget: dict):
    clean = np.asarray(events["t"], dtype=np.float64)
    n = len(clean)
    initial, generations, per_gen = budget["initial"], budget["generations"], budget["per_generation"]
    if initial < 12 or generations != 4 or per_gen < 1:
        raise ValueError("TEMP budget cannot preserve elite=12 and exactly four generations")
    pool = np.asarray([legacy.project(clean + rng.uniform(-epsilon, epsilon, n), clean, epsilon)
                       for _ in range(initial)])
    values, predictions, invocations = evaluate(model, events, pool, label)
    for scale in (0.50, 0.30, 0.18, 0.10):
        elite_idx = np.argsort(values, kind="stable")[:12]
        elite = pool[elite_idx]
        children = []
        for i in range(per_gen):
            parent = elite[i % len(elite)]
            proposal = parent + 0.5 * (elite[rng.integers(12)] - elite[rng.integers(12)])
            proposal += rng.normal(0, epsilon * scale, n)
            children.append(legacy.project(proposal, clean, epsilon))
        children = np.asarray(children)
        child_values, child_predictions, calls = evaluate(model, events, children, label)
        invocations += calls
        pool = np.vstack((elite, children))
        values = np.concatenate((values[elite_idx], child_values))
        predictions = np.concatenate((predictions[elite_idx], child_predictions))
    best = int(np.argmin(values))
    return pool[best], float(values[best]), int(predictions[best]), invocations


@torch.no_grad()
def evaluate(model, events, candidates, label: int, chunk: int = 64):
    values, predictions, calls = [], [], 0
    for start in range(0, len(candidates), chunk):
        timestamps = torch.as_tensor(candidates[start:start + chunk], device="cuda", dtype=torch.float32)
        logits = model(canonical_frames_torch(events, timestamps))
        values.extend(frozen_temp.objective_values(logits, label).cpu().tolist())
        predictions.extend(logits.argmax(1).cpu().tolist())
        calls += 1
    return np.asarray(values), np.asarray(predictions), calls


def select_calibration(dataset, models, manifest_ids: set[int]) -> list[dict]:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    candidates = defaultdict(list)
    # A deterministic bounded scan gives a broad event-count pool without attack outcomes.
    for sid in split["train_indices"]:
        sid = int(sid)
        if sid in manifest_ids:
            continue
        events, label = dataset[sid]
        label = int(label)
        if len(candidates[label]) >= 50:
            if all(len(candidates[c]) >= 50 for c in range(10)):
                break
            continue
        frame = torch.from_numpy(events_to_frames(events, 10)).float()[None].cuda()
        with torch.no_grad():
            predictions = [int(model(frame).argmax(1).item()) for model in models.values()]
        if all(p == label for p in predictions):
            candidates[label].append({"sample_id": sid, "label": label, "event_count": len(events)})
    selected = []
    for label in range(10):
        pool = candidates[label]
        if not pool:
            raise RuntimeError(f"No common-clean-correct calibration samples for class {label}")
        median = float(np.median([x["event_count"] for x in pool]))
        chosen = sorted(pool, key=lambda x: (abs(x["event_count"] - median), x["sample_id"]))[:1]
        selected.extend({**x, "class_candidate_count": len(pool), "class_event_count_median": median} for x in chosen)
    if len(selected) != 10 or manifest_ids.intersection(x["sample_id"] for x in selected):
        raise RuntimeError("Calibration selection invariant failed")
    return selected


def warmup(model, events, label: int) -> None:
    clean = np.asarray(events["t"], dtype=np.float64)
    epsilon = CALIBRATION_EPSILON * (clean[-1] - clean[0] + 1)
    legacy.pgd(model, events, label, epsilon)
    temp_attack(model, events, label, epsilon, np.random.default_rng(7), scaled_budget(400))
    synchronize()


def calibrate(dataset, models, samples: list[dict]) -> dict:
    result = {}
    for model_name, model in models.items():
        first_events, _ = dataset[samples[0]["sample_id"]]
        warmup(model, first_events, samples[0]["label"])
        pgd_times = []
        for position, item in enumerate(samples):
            events, _ = dataset[item["sample_id"]]
            clean = np.asarray(events["t"], dtype=np.float64)
            epsilon = CALIBRATION_EPSILON * (clean[-1] - clean[0] + 1)
            for repeat in range(CALIBRATION_REPEATS):
                _, elapsed = timed(lambda: legacy.pgd(model, events, item["label"], epsilon))
                pgd_times.append(elapsed)
        timings = {q: [] for q in WALLCLOCK_Q_GRID}
        for q in WALLCLOCK_Q_GRID:
            budget = scaled_budget(q)
            for position, item in enumerate(samples):
                events, _ = dataset[item["sample_id"]]
                clean = np.asarray(events["t"], dtype=np.float64)
                epsilon = CALIBRATION_EPSILON * (clean[-1] - clean[0] + 1)
                for repeat in range(CALIBRATION_REPEATS):
                    seed = 900_000_000 + q * 1009 + position * 31 + repeat
                    _, elapsed = timed(lambda: temp_attack(model, events, item["label"], epsilon,
                                                           np.random.default_rng(seed), budget))
                    timings[q].append(elapsed)
        grid = []
        for q in WALLCLOCK_Q_GRID:
            pgd_median = float(np.median(pgd_times))
            temp_median = float(np.median(timings[q]))
            grid.append({**scaled_budget(q), "pgd_median_seconds": pgd_median,
                         "temp_median_seconds": temp_median, "median_runtime_ratio": temp_median / pgd_median,
                          "pgd_times_seconds": pgd_times, "temp_times_seconds": timings[q]})
        selected = min(grid, key=lambda x: (abs(x["median_runtime_ratio"] - 1), x["q"]))
        matched = 0.9 <= selected["median_runtime_ratio"] <= 1.1
        result[model_name] = {"grid": grid, "selected": selected, "matched": matched,
                              "status": "matched" if matched else "unmatched_no_budget_within_10_percent"}
    return result


def metrics(events, clean_t, adversarial_t, clean_frame, adversarial_frame) -> dict:
    duration = float(clean_t[-1] - clean_t[0] + 1)
    delta = np.abs(adversarial_t - clean_t)
    clean_bins = frozen_temp.bins(events, clean_t)
    adversarial_bins = frozen_temp.bins(events, adversarial_t)
    frame_delta = (adversarial_frame - clean_frame).float().flatten()
    return {"mean_normalized_abs_dt": float(np.mean(delta / duration)),
            "median_normalized_abs_dt": float(np.median(delta / duration)),
            "max_normalized_abs_dt": float(np.max(delta / duration)),
            "fraction_events_bin_changed": float(np.mean(clean_bins != adversarial_bins)),
            "events_bin_changed": int(np.count_nonzero(clean_bins != adversarial_bins)),
            "frame_l0": int(torch.count_nonzero(frame_delta).item()),
            "frame_l1": float(frame_delta.abs().sum().item()),
            "frame_l2": float(torch.linalg.vector_norm(frame_delta).item()),
            "frame_linf": float(frame_delta.abs().max().item()),
            "clean_bins": clean_bins, "adversarial_bins": adversarial_bins}


def reused_metrics(path: Path) -> dict:
    """Recompute metrics from complete, hash-verified v3 event arrays."""
    with np.load(path, allow_pickle=False) as z:
        clean_t = z["clean_t"]
        adversarial_t = z["adversarial_t"]
        duration = float(z["duration"])
        delta = np.abs(adversarial_t - clean_t)
        return {"mean_normalized_abs_dt": float(np.mean(delta / duration)),
                "median_normalized_abs_dt": float(np.median(delta / duration)),
                "fraction_events_bin_changed": float(np.mean(z["clean_bins"] != z["adversarial_bins"])),
                **{name: float(z[name]) for name in ("frame_l0", "frame_l1", "frame_l2", "frame_linf")},
                **{name: int(z[name]) for name in ("model_forward_evaluations", "backward_evaluations",
                                                   "candidate_evaluations")},
                "batched_model_invocations": (int(z["model_forward_evaluations"])
                                                if str(z["attack"]) == "PGD"
                                                else math.ceil(int(z["candidate_evaluations"]) / 64)),
                "verification_forwards_excluded": 1}


def run_new_record(model, model_name, events, label, sample_id, position, epsilon_fraction,
                   condition, budget, attack: str):
    clean_t = np.asarray(events["t"], dtype=np.float64)
    duration = float(clean_t[-1] - clean_t[0] + 1)
    epsilon = epsilon_fraction * duration
    rng_seed = SEED + position * 1009 + int(epsilon_fraction * 1_000_000)
    if attack == "PGD":
        (adversarial_t, elapsed) = timed(lambda: legacy.pgd(model, events, label, epsilon))
        forwards, backwards, candidates, invocations = 41, 20, 21, 41
        returned_objective, returned_prediction = math.nan, -1
        objective_name = "cross_entropy_true_label"
    else:
        ((adversarial_t, returned_objective, returned_prediction, invocations), elapsed) = timed(
            lambda: temp_attack(model, events, label, epsilon, np.random.default_rng(rng_seed), budget))
        forwards = candidates = budget["q"]
        backwards = 0
        objective_name = "true_class_margin"
    adversarial_t = legacy.project(adversarial_t, clean_t, epsilon)
    clean_frame = canonical_frames_torch(events, torch.as_tensor(clean_t, device="cuda", dtype=torch.float32))
    adversarial_frame = canonical_frames_torch(events, torch.as_tensor(adversarial_t, device="cuda", dtype=torch.float32))
    with torch.no_grad():
        clean_logits, adversarial_logits = model(clean_frame), model(adversarial_frame)
    clean_prediction = int(clean_logits.argmax(1).item())
    adversarial_prediction = int(adversarial_logits.argmax(1).item())
    clean_margin = float(frozen_temp.objective_values(clean_logits, label).item())
    adversarial_margin = float(frozen_temp.objective_values(adversarial_logits, label).item())
    clean_objective = (float(F.cross_entropy(clean_logits, torch.tensor([label], device="cuda")).item())
                       if attack == "PGD" else clean_margin)
    adversarial_objective = (float(F.cross_entropy(adversarial_logits, torch.tensor([label], device="cuda")).item())
                             if attack == "PGD" else adversarial_margin)
    m = metrics(events, clean_t, adversarial_t, clean_frame, adversarial_frame)
    x, y, p = (np.asarray(events[k]) for k in ("x", "y", "p"))
    reference_adversarial_frame_np = np.zeros((10, 2, 34, 34), dtype=np.float32)
    np.add.at(reference_adversarial_frame_np, (frozen_temp.bins(events, adversarial_t), p, y, x), 1)
    reference_adversarial_frame = torch.from_numpy(np.clip(reference_adversarial_frame_np, 0, 255))[None].cuda()
    checks = {
        "label_clean_correct": clean_prediction == label,
        "coordinates_valid": bool(np.array_equal(x, np.asarray(events["x"])) and np.all((0 <= x) & (x < 34))
                                  and np.array_equal(y, np.asarray(events["y"])) and np.all((0 <= y) & (y < 34))),
        "polarity_valid": bool(np.array_equal(p, np.asarray(events["p"])) and np.all(np.isin(p, (0, 1)))),
        "event_count_preserved": len(adversarial_t) == len(clean_t) == len(x) == len(y) == len(p),
        "timestamps_monotonic": bool(np.all(np.diff(adversarial_t) >= 0)),
        "timestamp_domain": bool(np.all(adversarial_t >= clean_t[0]) and np.all(adversarial_t <= clean_t[-1])),
        "epsilon_bound": bool(np.all(np.abs(adversarial_t - clean_t) <= epsilon + 1e-9)),
        "canonical_clean_frame": bool(torch.equal(clean_frame, torch.from_numpy(events_to_frames(events, 10)).float()[None].cuda())),
        "canonical_adversarial_frame": bool(torch.equal(adversarial_frame, reference_adversarial_frame)),
        "prediction_consistent": attack != METHOD or returned_prediction == adversarial_prediction,
        "objective_consistent": bool(np.isfinite(adversarial_objective) and np.isfinite(adversarial_margin)),
        "success_consistent": (adversarial_prediction != label) == bool(adversarial_prediction != clean_prediction),
    }
    passed = all(checks.values())
    slug = attack.lower().replace("-", "_")
    path = RECORDS / condition / model_name / slug / f"sample_{sample_id:06d}__eps_{int(epsilon_fraction*1e6):06d}.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"protocol_version": np.asarray(VERSION), "condition": np.asarray(condition),
               "sample_id": sample_id, "label": label, "model": np.asarray(model_name), "attack": np.asarray(attack),
               "epsilon_fraction": epsilon_fraction, "epsilon_absolute": epsilon, "rng_seed": rng_seed,
               "clean_x": x.astype(np.int16), "clean_y": y.astype(np.int16), "clean_p": p.astype(np.int8),
               "adversarial_x": x.astype(np.int16), "adversarial_y": y.astype(np.int16), "adversarial_p": p.astype(np.int8),
               "clean_t": clean_t, "adversarial_t": adversarial_t, "clean_bins": m.pop("clean_bins"),
               "adversarial_bins": m.pop("adversarial_bins"), "clean_prediction": clean_prediction,
               "adversarial_prediction": adversarial_prediction, "attack_success": adversarial_prediction != label,
               "clean_objective": clean_objective, "adversarial_objective": adversarial_objective,
               "clean_margin": clean_margin, "adversarial_margin": adversarial_margin,
               "attack_returned_objective": returned_objective, "attack_returned_prediction": returned_prediction,
               "objective_name": np.asarray(objective_name), "runtime_seconds": elapsed,
               "model_forward_evaluations": forwards, "backward_evaluations": backwards,
               "candidate_evaluations": candidates, "batched_model_invocations": invocations,
               "verification_forwards_excluded": 2, "audit_passed": passed, **m}
    np.savez_compressed(path, **payload)
    row = {k: (v.item() if isinstance(v, np.ndarray) and v.ndim == 0 else v) for k, v in payload.items()
           if not isinstance(v, np.ndarray) or v.ndim == 0}
    row.update({"record_path": path.relative_to(DEST).as_posix(), "record_sha256": sha256(path),
                "audit_passed": passed, "audit_failures": ";".join(k for k, v in checks.items() if not v)})
    return row


def paired(rows: list[dict], condition: str, model: str, epsilon: float, labels: dict[int, int]) -> dict:
    cell = [r for r in rows if r["condition"] == condition and r["model"] == model
            and float(r["epsilon_fraction"]) == epsilon]
    temp_label = "TEMP-DRIFT-v2" if condition == "original_v3_fixed_budget" else METHOD
    by_attack = {a: {int(r["sample_id"]): bool(r["attack_success"]) for r in cell if r["attack"] == a}
                 for a in ("PGD", temp_label)}
    ids = sorted(set(by_attack["PGD"]) & set(by_attack[temp_label]))
    if len(ids) != 100:
        raise RuntimeError(f"Incomplete paired cell {condition}/{model}/{epsilon}: {len(ids)}")
    pgd_only = sum(by_attack["PGD"][i] and not by_attack[temp_label][i] for i in ids)
    temp_only = sum(by_attack[temp_label][i] and not by_attack["PGD"][i] for i in ids)
    both = sum(by_attack["PGD"][i] and by_attack[temp_label][i] for i in ids)
    neither = len(ids) - pgd_only - temp_only - both
    discordant = pgd_only + temp_only
    p = stats.binomtest(temp_only, discordant, 0.5).pvalue if discordant else 1.0
    rng = np.random.default_rng(42_424_242)
    strata = {c: np.asarray([i for i in ids if labels[i] == c]) for c in range(10)}
    differences = np.empty(BOOTSTRAPS)
    for b in range(BOOTSTRAPS):
        sampled = np.concatenate([rng.choice(strata[c], len(strata[c]), replace=True) for c in range(10)])
        differences[b] = np.mean([int(by_attack[temp_label][int(i)]) - int(by_attack["PGD"][int(i)]) for i in sampled])
    return {"condition": condition, "model": model, "epsilon_fraction": epsilon, "n": len(ids),
            "pgd_asr": float(np.mean([by_attack["PGD"][i] for i in ids])),
            "temp_asr": float(np.mean([by_attack[temp_label][i] for i in ids])),
            "temp_minus_pgd_asr": (temp_only - pgd_only) / len(ids), "pgd_only": pgd_only,
             "temp_only": temp_only, "both_succeed": both, "neither_succeeds": neither,
            "mcnemar_exact_two_sided_p": float(p), "bootstrap_replicates": BOOTSTRAPS,
            "class_stratified_bootstrap_seed": 42_424_242,
            "bootstrap_95_ci_low": float(np.quantile(differences, 0.025)),
            "bootstrap_95_ci_high": float(np.quantile(differences, 0.975)),
            "pgd_successful_ids": [i for i in ids if by_attack["PGD"][i]],
            "temp_successful_ids": [i for i in ids if by_attack[temp_label][i]]}


def summary_rows(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["condition"], row["model"], row["attack"], float(row["epsilon_fraction"]))].append(row)
    output = []
    metric_names = ("mean_normalized_abs_dt", "median_normalized_abs_dt", "fraction_events_bin_changed",
                    "frame_l0", "frame_l1", "frame_l2", "frame_linf")
    for (condition, model, attack, epsilon), cell in sorted(grouped.items()):
        out = {"condition": condition, "model": model, "attack": attack, "epsilon_fraction": epsilon,
               "n": len(cell), "successes": sum(bool(x["attack_success"]) for x in cell),
               "asr": float(np.mean([bool(x["attack_success"]) for x in cell])),
               "mean_runtime_seconds": float(np.mean([float(x["runtime_seconds"]) for x in cell])),
               "median_runtime_seconds": float(np.median([float(x["runtime_seconds"]) for x in cell])),
               "mean_model_forward_evaluations": float(np.mean([int(x["model_forward_evaluations"]) for x in cell])),
               "mean_backward_evaluations": float(np.mean([int(x["backward_evaluations"]) for x in cell])),
               "mean_candidate_evaluations": float(np.mean([int(x["candidate_evaluations"]) for x in cell])),
               "mean_batched_model_invocations": float(np.mean([int(x["batched_model_invocations"]) for x in cell])),
               "successful_ids": json.dumps(sorted(int(x["sample_id"]) for x in cell if bool(x["attack_success"]))) }
        for metric in metric_names:
            out[f"mean_{metric}"] = float(np.mean([float(x[metric]) for x in cell]))
        output.append(out)
    return output


def report(summaries, comparisons, calibration, status) -> str:
    lines = ["# Corrected N-MNIST Budget-Matched Comparison v2 (Seed 42)", "",
             f"Status: **{status}**. Seed-42 evidence only; this is not a multi-seed robustness claim.", "",
             "## Design", "",
             "- Original fixed-budget rows and full event arrays are reused from the hash-verified, fully audited v3 artifact.",
             "- Access 21: TEMP 13 + 4x2 candidates; matched to PGD's 21 candidate evaluations.",
             "- Access 41: TEMP 13 + 4x7 candidates; matched to PGD's 41 attack-internal forwards.",
             "- PGD has 41 attack forwards, 20 backward evaluations, and 21 candidates. TEMP has Q forwards/candidates and zero backwards.",
             "- No backward-pass conversion factor or backward equivalence is asserted.",
             "- Verification uses two additional forwards per new record and is excluded from attack timing/accounting.", "",
             "## Wall-Clock Calibration", ""]
    for model, value in calibration.items():
        selected = value["selected"]
        lines.append(f"- {model}: {value['status']}; Q={selected['q']}, median TEMP/PGD ratio={selected['median_runtime_ratio']:.3f}.")
    lines += ["", "## Paired Outcomes", "",
               "| Condition | Model | epsilon | PGD ASR | TEMP ASR | Delta | PGD only | TEMP only | Both succeed | Neither succeeds | Exact p | Bootstrap 95% CI |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in comparisons:
        lines.append(f"| {x['condition']} | {x['model']} | {x['epsilon_fraction']:.2f} | {x['pgd_asr']:.3f} | {x['temp_asr']:.3f} | {x['temp_minus_pgd_asr']:+.3f} | {x['pgd_only']} | {x['temp_only']} | {x['both_succeed']} | {x['neither_succeeds']} | {x['mcnemar_exact_two_sided_p']:.6g} | [{x['bootstrap_95_ci_low']:+.3f}, {x['bootstrap_95_ci_high']:+.3f}] |")
    lines += ["", "Complete sample IDs, runtime means/medians, distortions, and audit fields are in the CSV/JSON outputs.",
              "The original, access-21, access-41, and model-specific wall-clock conditions are reported separately.", ""]
    return "\n".join(lines)


def main() -> None:
    if Path(sys.executable).resolve() != REQUIRED_PYTHON.resolve():
        raise RuntimeError(f"Required interpreter: {REQUIRED_PYTHON}; current: {sys.executable}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    if (DEST / "records").exists() or (DEST / "per_sample_results.csv").exists():
        raise RuntimeError(f"Refusing to overwrite experiment records in {DEST}")
    DEST.mkdir(parents=True, exist_ok=True)
    write_json(DEST / "STATUS.json", {"status": "running", "fully_audited": False,
                                      "started_at_utc": datetime.now(timezone.utc).isoformat()})
    audit = {"status": "running", "record_failures": [], "source": {}}
    try:
        original_rows, original_manifest, source_hashes = source_records()
        audit["source"] = source_hashes
        manifest = json.loads((SOURCE / "common_clean_correct_manifest.json").read_text(encoding="utf-8"))
        labels = {int(x["sample_id"]): int(x["label"]) for x in manifest["samples"]}
        from tonic.datasets import NMNIST
        dataset = NMNIST(save_to=str(ROOT / "data/nmnist"), train=True)
        legacy.frames_torch = canonical_frames_torch
        frozen_temp.frames_torch = canonical_frames_torch
        models = legacy.load_models()
        calibration_samples = select_calibration(dataset, models, set(labels))
        write_json(DEST / "calibration_samples.json", {"frozen_before_evaluation": True,
                                                        "selection_uses_attack_success": False,
                                                        "samples": calibration_samples})
        calibration = calibrate(dataset, models, calibration_samples)
        write_json(DEST / "wallclock_calibration.json", calibration)
        budgets = {**CONDITIONS, **{f"wallclock_{m.lower()}": v["selected"] for m, v in calibration.items()}}
        write_json(DEST / "budget_definitions.json", {"frozen_before_evaluation": True,
                                                       "method": METHOD, "conditions": budgets,
                                                       "pgd": {"attack_forwards": 41, "backwards": 20, "candidates": 21},
                                                       "temp_scaling_rule": "initial=max(12,round(.375Q)); exactly four equal generations; actual total explicitly recorded"})
        rows = []
        # Reuse only audited v3 rows/arrays for original and all PGD access comparators.
        source_index = {(int(x["sample_id"]), x["model"], x["attack"], float(x["epsilon_fraction"])): x
                        for x in original_manifest}
        original_csv = {(int(x["sample_id"]), x["model"], x["attack"], float(x["epsilon_fraction"])): x
                        for x in original_rows}
        for key, src in source_index.items():
            sid, model, attack, epsilon = key
            if epsilon not in EPSILONS:
                continue
            source_row = original_csv[key]
            rows.append({"condition": "original_v3_fixed_budget", "sample_id": sid, "label": labels[sid],
                         "model": model, "attack": attack, "epsilon_fraction": epsilon,
                         "attack_success": source_row["stored_attack_success"].lower() == "true",
                         "runtime_seconds": float(source_row["runtime_seconds"]),
                         "record_path": str((SOURCE / src["record_path"]).relative_to(ROOT)),
                          "record_sha256": src["sha256"], "audit_passed": True, "audit_failures": "",
                          **reused_metrics(SOURCE / src["record_path"])})
        evaluation_conditions = ["access_candidates_21", "access_forwards_41"]
        evaluation_conditions += [f"wallclock_{m.lower()}" for m in models if calibration[m]["matched"]]
        for position, item in enumerate(manifest["samples"]):
            sid, label = int(item["sample_id"]), int(item["label"])
            events, actual_label = dataset[sid]
            if int(actual_label) != label:
                raise RuntimeError(f"Manifest label mismatch: {sid}")
            for model_name, model in models.items():
                for epsilon in EPSILONS:
                    for condition in evaluation_conditions:
                        if condition.startswith("wallclock_") and condition != f"wallclock_{model_name.lower()}":
                            continue
                        budget = budgets[condition]
                        # Access PGD is immutable v3 PGD. Wall-clock reruns PGD and alternates attack order.
                        if condition.startswith("access_"):
                            src = source_index[(sid, model_name, "PGD", epsilon)]
                            source_row = original_csv[(sid, model_name, "PGD", epsilon)]
                            row = {"condition": condition, "sample_id": sid, "label": label, "model": model_name,
                                   "attack": "PGD", "epsilon_fraction": epsilon,
                                   "attack_success": source_row["stored_attack_success"].lower() == "true",
                                   "runtime_seconds": float(source_row["runtime_seconds"]),
                                   "record_path": str((SOURCE / src["record_path"]).relative_to(ROOT)),
                                   "record_sha256": src["sha256"], "audit_passed": True, "audit_failures": "",
                                   **reused_metrics(SOURCE / src["record_path"])}
                            rows.append(row)
                            rows.append(run_new_record(model, model_name, events, label, sid, position, epsilon,
                                                       condition, budget, METHOD))
                        else:
                            order = ("PGD", METHOD) if position % 2 == 0 else (METHOD, "PGD")
                            for attack in order:
                                rows.append(run_new_record(model, model_name, events, label, sid, position, epsilon,
                                                           condition, budget, attack))
        failures = [r for r in rows if not r["audit_passed"]]
        audit.update({"status": "passed" if not failures else "failed", "records_checked": len(rows),
                      "record_failures": failures, "all_records_passed": not failures,
                      "source_records_hash_verified": source_hashes["verified_record_count"],
                      "new_record_count": sum(str(x["record_path"]).startswith("records/") for x in rows)})
        write_json(DEST / "audit.json", audit)
        if failures:
            raise RuntimeError(f"Fail-closed audit: {len(failures)} records failed")
        write_csv(DEST / "per_sample_results.csv", rows)
        summaries = summary_rows(rows)
        write_csv(DEST / "condition_summaries.csv", summaries)
        write_json(DEST / "condition_summaries.json", summaries)
        comparison_conditions = ["original_v3_fixed_budget"] + evaluation_conditions
        comparisons = [paired(rows, condition, model, epsilon, labels)
                       for condition in comparison_conditions for model in models for epsilon in EPSILONS
                       if not condition.startswith("wallclock_") or condition == f"wallclock_{model.lower()}"]
        write_csv(DEST / "paired_comparisons.csv", comparisons)
        write_json(DEST / "paired_comparisons.json", comparisons)
        status = "complete" if all(x["matched"] for x in calibration.values()) else "complete_wallclock_unmatched_for_one_or_more_models"
        (DEST / "report.md").write_text(report(summaries, comparisons, calibration, status), encoding="utf-8")
        write_json(DEST / "STATUS.json", {"status": status, "fully_audited": True, "failed_records": 0,
                                          "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                                          "python_executable": sys.executable, "python_version": platform.python_version(),
                                          "cuda": torch.version.cuda})
    except Exception as exc:
        audit["status"] = "failed"
        audit["error"] = repr(exc)
        write_json(DEST / "audit.json", audit)
        write_json(DEST / "STATUS.json", {"status": "failed", "fully_audited": False,
                                          "error": repr(exc), "finished_at_utc": datetime.now(timezone.utc).isoformat()})
        raise


if __name__ == "__main__":
    main()
