from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from sklearn.metrics import f1_score

from defenses.quantum_temp import true_class_margin
from experiments.iris.attack_evaluation import evaluate_attack_data
from experiments.iris.data import load_iris_train_validation
from experiments.iris.paired_analysis import paired_category, summarize_paired_outcomes
from experiments.iris.phase173 import RULES, pareto_epochs, per_class_accuracy, select_checkpoint
from experiments.iris.training import train_iris_model
from scripts.run_phase172_diagnosis import config_pair


RESULTS = ROOT / "results"
CHECKPOINTS = ROOT / "checkpoints"
SEEDS = (42, 777, 2026)
FRACTIONS = (0.01, 0.02, 0.05, 0.10)


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in rows)


def observer(states, clean_rows, sample119_index):
    def observe(model, epoch, val_loss, val_accuracy, angles, labels):
        model.eval()
        with torch.no_grad():
            features = model.quantum_features(angles)
            logits = model.head(features)
            predictions = logits.argmax(1)
            probabilities = torch.softmax(logits, dim=-1)
            margins = true_class_margin(logits, labels)
        class_acc = per_class_accuracy(labels.numpy(), predictions.numpy())
        class_margins = [float(margins[labels == class_id].mean()) for class_id in range(3)]
        states[epoch] = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
        clean_rows.append({
            "epoch": epoch, "val_loss": val_loss, "val_accuracy": val_accuracy,
            "macro_F1": float(f1_score(labels.numpy(), predictions.numpy(), average="macro")),
            "class0_acc": class_acc[0], "class1_acc": class_acc[1], "class2_acc": class_acc[2],
            "min_class_acc": min(class_acc), "mean_margin": float(margins.mean()),
            "min_class_mean_margin": min(class_margins),
            "low_margin_count": int((margins.abs() < 0.10).sum()),
            "negative_margin_count": int((margins < 0).sum()),
            "class1_mean_margin": class_margins[1], "class2_mean_margin": class_margins[2],
            "class12_low_margin_count": int((margins[(labels == 1) | (labels == 2)].abs() < 0.10).sum()),
            "class12_misclassified": int((predictions[(labels == 1) | (labels == 2)] != labels[(labels == 1) | (labels == 2)]).sum()),
            "sample119_pred": int(predictions[sample119_index]),
            "sample119_margin": float(margins[sample119_index]),
            "sample119_confidence": float(probabilities[sample119_index, labels[sample119_index]]),
        })
    return observe


def attack_grid(config, checkpoint, Xval, yval, val_ids):
    output = {}
    T = float(config["time_window"])
    for attack in ("random_jitter", "classical_timing"):
        for fraction in FRACTIONS:
            result = evaluate_attack_data(
                config, checkpoint, attack, fraction * T, Xval, yval,
                iterations=20, step_size=fraction * T / 5, split="validation",
                sample_ids=val_ids, return_samples=True,
            )
            output[(attack, fraction)] = result
    return output


def paired(current, alternative):
    left = {row["sample_id"]: row for row in current}
    right = {row["sample_id"]: row for row in alternative}
    rows = []
    for sample_id in sorted(left.keys() & right.keys()):
        if left[sample_id]["clean_correct"] and right[sample_id]["clean_correct"]:
            rows.append({"paired_category": paired_category(left[sample_id]["attack_success"], right[sample_id]["attack_success"])})
    return summarize_paired_outcomes(rows)


def main():
    base = json.loads((ROOT / "configs" / "iris.json").read_text())
    _, Xval, _, yval, _, _, val_ids = load_iris_train_validation(42, base["test_size"], base["val_size"])
    sample119_index = int(np.where(val_ids == 119)[0][0])
    epoch_rows, all_states, configs = [], {}, {}
    for seed in SEEDS:
        _, config = config_pair(base, seed)
        configs[seed] = config
        states, clean_rows = {}, []
        train_iris_model(config, evaluate_test=False, epoch_observer=observer(states, clean_rows, sample119_index))
        diagnostic_checkpoint = CHECKPOINTS / f"iris_phase173_diagnostic_{seed}.pt"
        for row in clean_rows:
            torch.save(states[row["epoch"]], diagnostic_checkpoint)
            pgd = evaluate_attack_data(
                config, diagnostic_checkpoint, "classical_timing", 0.02 * config["time_window"],
                Xval, yval, iterations=20, step_size=0.004 * config["time_window"],
                split="validation",
            )
            row.update({"seed": seed, "PGD2_ASR": pgd["asr"]})
            epoch_rows.append(row)
        all_states[seed] = states
        diagnostic_checkpoint.unlink(missing_ok=True)
        print(f"seed={seed} epoch diagnostics complete")

    selections, selection_rows = {}, []
    for seed in SEEDS:
        rows = [row for row in epoch_rows if row["seed"] == seed]
        for rule in RULES:
            selected = select_checkpoint(rows, rule)
            selections[(rule, seed)] = selected
            selection_rows.append({
                "rule": rule, "seed": seed, "selected_epoch": selected["epoch"],
                "clean_accuracy": selected["val_accuracy"], "macro_F1": selected["macro_F1"],
                "min_class_acc": selected["min_class_acc"], "class1_acc": selected["class1_acc"],
                "class2_acc": selected["class2_acc"], "mean_margin": selected["mean_margin"],
                "PGD2_ASR": selected["PGD2_ASR"], "sample119_pred": selected["sample119_pred"],
                "sample119_margin": selected["sample119_margin"], "sample119_confidence": selected["sample119_confidence"],
                "class1_mean_margin": selected["class1_mean_margin"], "class2_mean_margin": selected["class2_mean_margin"],
                "class12_low_margin_count": selected["class12_low_margin_count"],
                "class12_misclassified": selected["class12_misclassified"],
            })

    grids = {}
    for rule in RULES:
        for seed in SEEDS:
            checkpoint = CHECKPOINTS / f"iris_phase173_{rule}_{seed}.pt"
            torch.save(all_states[seed][selections[(rule, seed)]["epoch"]], checkpoint)
            grids[(rule, seed)] = attack_grid(configs[seed], checkpoint, Xval, yval, val_ids)

    attack_rows = []
    for rule in RULES:
        for seed in SEEDS:
            for attack in ("random_jitter", "classical_timing"):
                for fraction in FRACTIONS:
                    result = grids[(rule, seed)][(attack, fraction)]
                    current = grids[("RULE_A_CURRENT", seed)][(attack, fraction)]
                    comparison = paired(current["samples"], result["samples"])
                    classwise = {}
                    for class_id in range(3):
                        members = [row for row in result["samples"] if row["true_label"] == class_id]
                        classwise[str(class_id)] = sum(row["attacked_prediction"] == class_id for row in members) / len(members)
                    attack_rows.append({
                        "rule": rule, "seed": seed, "attack": attack, "epsilon": fraction,
                        "N_common": comparison["N_common"], "failures": comparison["defense_failures"],
                        "ASR": result["summary"]["asr"], "rescued_vs_current": comparison["rescued"],
                        "broken_vs_current": comparison["broken"], "net_gain_vs_current": comparison["net_gain"],
                        "mean_attacked_margin": result["summary"]["mean_attacked_true_margin"],
                        "classwise_attacked_accuracy": classwise,
                    })

    summary_rows = []
    for rule in RULES:
        selected = [row for row in selection_rows if row["rule"] == rule]
        pgd = [row for row in attack_rows if row["rule"] == rule and row["attack"] == "classical_timing"]
        directions = []
        for seed in SEEDS:
            net = sum(row["net_gain_vs_current"] for row in pgd if row["seed"] == seed)
            directions.append(np.sign(net))
        summary_rows.append({
            "rule": rule, "mean_accuracy": float(np.mean([row["clean_accuracy"] for row in selected])),
            "mean_macro_F1": float(np.mean([row["macro_F1"] for row in selected])),
            "mean_min_class_acc": float(np.mean([row["min_class_acc"] for row in selected])),
            **{f"mean_PGD{int(fraction * 100)}_ASR": float(np.mean([row["ASR"] for row in pgd if row["epsilon"] == fraction])) for fraction in FRACTIONS},
            "improved_seeds": int(sum(value > 0 for value in directions)),
            "unchanged_seeds": int(sum(value == 0 for value in directions)),
            "worsened_seeds": int(sum(value < 0 for value in directions)),
        })

    pareto_rows = []
    for seed in SEEDS:
        for row in pareto_epochs([item for item in epoch_rows if item["seed"] == seed]):
            pareto_rows.append({"seed": seed, "epoch": row["epoch"], "val_accuracy": row["val_accuracy"], "min_class_acc": row["min_class_acc"], "PGD2_ASR": row["PGD2_ASR"], "mean_margin": row["mean_margin"]})

    rule_checks = {}
    for rule in RULES[1:]:
        checks = []
        for seed in SEEDS:
            current_selection = selections[("RULE_A_CURRENT", seed)]
            selection = selections[(rule, seed)]
            rows = [row for row in attack_rows if row["rule"] == rule and row["seed"] == seed and row["attack"] == "classical_timing"]
            checks.append({
                "seed": seed,
                "clean_preserved": selection["val_accuracy"] >= current_selection["val_accuracy"] - 1e-12,
                "min_class_preserved": selection["min_class_acc"] >= current_selection["min_class_acc"] - 1e-12,
                "small_epsilon_not_worse": all(row["net_gain_vs_current"] >= 0 for row in rows if row["epsilon"] in (0.01, 0.02)),
                "meaningful_improvement": any(row["net_gain_vs_current"] > 0 for row in rows if row["epsilon"] in (0.05, 0.10)),
            })
        rule_checks[rule] = checks
    passing = [rule for rule, checks in rule_checks.items() if all(row["clean_preserved"] and row["min_class_preserved"] and row["small_epsilon_not_worse"] for row in checks) and sum(row["meaningful_improvement"] for row in checks) >= 2]
    frozen_rule = passing[0] if passing else None

    write_csv(RESULTS / "iris_phase173_epoch_metrics.csv", epoch_rows, ["seed", "epoch", "val_accuracy", "macro_F1", "class0_acc", "class1_acc", "class2_acc", "min_class_acc", "mean_margin", "min_class_mean_margin", "low_margin_count", "negative_margin_count", "PGD2_ASR"])
    (RESULTS / "iris_phase173_epoch_metrics.json").write_text(json.dumps({"rows": epoch_rows}, indent=2), encoding="utf-8")
    write_csv(RESULTS / "iris_phase173_rule_selection.csv", selection_rows)
    (RESULTS / "iris_phase173_rule_selection.json").write_text(json.dumps({"rows": selection_rows}, indent=2), encoding="utf-8")
    write_csv(RESULTS / "iris_phase173_attack_comparison.csv", attack_rows)
    (RESULTS / "iris_phase173_attack_comparison.json").write_text(json.dumps({"rows": attack_rows}, indent=2), encoding="utf-8")
    write_csv(RESULTS / "iris_phase173_multiseed_summary.csv", summary_rows)
    (RESULTS / "iris_phase173_multiseed_summary.json").write_text(json.dumps({"rows": summary_rows}, indent=2), encoding="utf-8")
    write_csv(RESULTS / "iris_phase173_pareto_epochs.csv", pareto_rows)
    config_payload = {"selection_data": "validation_only", "rules": list(RULES), "frozen_rule": frozen_rule, "same_rule_across_seeds": True, "frozen_training": configs, "test_set_accessed": False}
    (ROOT / "configs" / "iris_phase173_checkpoint_rule.json").write_text(json.dumps(config_payload, indent=2), encoding="utf-8")
    gate = {"status": "checkpoint_rule_passed" if frozen_rule else "negative_checkpoint_gate_failed", "passing_rules": passing, "frozen_rule": frozen_rule, "rule_checks": rule_checks, "test_set_accessed": False, "test_loader_invoked": False, "final_test_runs": []}
    (RESULTS / "iris_phase173_gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    selected_epochs = {rule: [selections[(rule, seed)]["epoch"] for seed in SEEDS] for rule in RULES}
    print(f"selections={selected_epochs} passing={passing}")


if __name__ == "__main__":
    main()
