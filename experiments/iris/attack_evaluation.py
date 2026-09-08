import time

import numpy as np
import torch

from attacks.classical_timing import classical_timing_attack
from attacks.random_jitter import random_timing_jitter
from attacks.temp_drift import temp_drift_gradient, temp_drift_reference
from encoding.quantum import angle_encode
from encoding.ttfs import ttfs_encode
from experiments.iris.data import load_iris_splits
from experiments.iris.training import to_theta
from metrics.quantum_drift import fidelity_from_angles, trace_distance_from_bloch
from metrics.spike_statistics import classical_mismatch
from models.qsnn import IrisQSNN
from defenses.quantum_temp import true_class_margin


def load_frozen_model(config, checkpoint_path):
    model = IrisQSNN(
        int(config["n_qubits"]), int(config["n_layers"]), int(config["n_classes"])
    )
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=True))
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


def evaluate_attack_data(
    config,
    checkpoint_path,
    attack,
    epsilon,
    normalized_features,
    labels,
    tau=0.1,
    iterations=20,
    step_size=None,
    restarts=3,
    split="validation",
    sample_ids=None,
    return_samples=False,
):
    seed = int(config["seed"])
    T = float(config["time_window"])
    features = np.asarray(normalized_features, dtype=float)
    labels = np.asarray(labels, dtype=int)
    if features.ndim != 2 or labels.shape != (len(features),):
        raise ValueError("Features and labels have incompatible shapes.")
    if sample_ids is None:
        sample_ids = np.arange(len(features))
    sample_ids = np.asarray(sample_ids)
    if sample_ids.shape != labels.shape:
        raise ValueError("sample_ids must match labels.")
    clean_times = ttfs_encode(features, T)
    model = load_frozen_model(config, checkpoint_path)
    with torch.no_grad():
        clean_angles_tensor = to_theta(features, T)
        clean_quantum_features = model.quantum_features(clean_angles_tensor)
        clean_logits = model.head(clean_quantum_features)
        clean_predictions = clean_logits.argmax(1).numpy()

    attacked_times = []
    drift = []
    classical = []
    attack_info = []
    started = time.perf_counter()
    for index, times in enumerate(clean_times):
        if attack == "random_jitter":
            adv, _ = random_timing_jitter(times, epsilon, T=T, seed=seed + index)
            info = {"feasible": True, "feasible_candidate_fraction": 1.0}
        elif attack == "classical_timing":
            adv, info = classical_timing_attack(
                model, times, int(labels[index]), epsilon, T=T,
                iterations=iterations, step_size=step_size, seed=seed + index,
            )
        elif attack == "temp_drift_reference":
            adv, info = temp_drift_reference(
                times, epsilon, tau, T=T, steps=50, candidates=32, seed=seed + index
            )
            info["feasible"] = info["delta_cls"] <= tau + 1e-12
            info["feasible_candidate_fraction"] = float(info["feasible"])
        elif attack == "temp_drift_gradient":
            adv, info = temp_drift_gradient(
                times, epsilon, tau, T=T, iterations=iterations,
                step_size=step_size, restarts=restarts, seed=seed + index,
            )
        else:
            raise ValueError(f"Unknown attack: {attack}")
        attacked_times.append(adv)
        attack_info.append(info)
        clean_angles = angle_encode(times, T)
        attacked_angles = angle_encode(adv, T)
        fidelity = fidelity_from_angles(clean_angles, attacked_angles)
        drift.append((trace_distance_from_bloch(clean_angles, attacked_angles), fidelity))
        classical.append(classical_mismatch(times, adv, T=T))

    runtime = time.perf_counter() - started

    attacked_features = 1.0 - np.asarray(attacked_times) / T
    with torch.no_grad():
        attacked_angles_tensor = to_theta(attacked_features, T)
        attacked_quantum_features = model.quantum_features(attacked_angles_tensor)
        attacked_logits = model.head(attacked_quantum_features)
        attacked_predictions = attacked_logits.argmax(1).numpy()
        clean_prob = torch.softmax(clean_logits, dim=-1)
        attacked_prob = torch.softmax(attacked_logits, dim=-1)
        midpoint = 0.5 * (clean_prob + attacked_prob)
        js = 0.5 * (
            torch.sum(clean_prob * (torch.log(clean_prob) - torch.log(midpoint)), dim=-1)
            + torch.sum(attacked_prob * (torch.log(attacked_prob) - torch.log(midpoint)), dim=-1)
        )
        measured_feature_drifts = torch.linalg.vector_norm(
            clean_quantum_features - attacked_quantum_features, dim=-1
        )
        logit_drifts = torch.linalg.vector_norm(clean_logits - attacked_logits, dim=-1)
        label_tensor = torch.tensor(labels, dtype=torch.long)
        clean_margins = true_class_margin(clean_logits, label_tensor)
        attacked_margins = true_class_margin(attacked_logits, label_tensor)
    clean_correct = clean_predictions == labels
    successful = clean_correct & (attacked_predictions != labels)
    denominator = int(clean_correct.sum())
    drift = np.asarray(drift)
    actual_step_size = (
        float(step_size) if step_size is not None
        else float(epsilon / max(iterations // 2, 1)) if attack == "classical_timing"
        else float(epsilon / max(iterations // 4, 1)) if attack == "temp_drift_gradient"
        else 0.0
    )
    perturbations = np.abs(np.asarray(attacked_times) - clean_times)
    summary = {
        "dataset": "iris",
        "split": split,
        "encoding": "angle_ttfs",
        "model_depth": int(config["n_layers"]),
        "seed": seed,
        "attack": attack,
        "epsilon": float(epsilon),
        "epsilon_fraction": float(epsilon / T),
        "tau": float(tau),
        "clean_accuracy": float(clean_correct.mean()),
        "attacked_accuracy": float((attacked_predictions == labels).mean()),
        "asr": float(successful.sum() / denominator) if denominator else 0.0,
        "asr_numerator": int(successful.sum()),
        "asr_denominator": denominator,
        "successful_attacks": int(successful.sum()),
        "clean_correct_count": denominator,
        "trace_distance": float(drift[:, 0].mean()),
        "fidelity": float(drift[:, 1].mean()),
        "one_minus_fidelity": float((1.0 - drift[:, 1]).mean()),
        "delta_cls": float(np.mean([item["delta_cls"] for item in classical])),
        "spike_count_diff": float(np.mean([item["spike_count_diff"] for item in classical])),
        "rate_diff": float(np.mean([item["rate_diff"] for item in classical])),
        "isi_tv": float(np.mean([item["isi_tv"] for item in classical])),
        "linf_timing": float(np.max(perturbations)),
        "iterations": int(iterations) if attack in ("classical_timing", "temp_drift_gradient") else 0,
        "step_size": actual_step_size,
        "restarts": int(restarts) if attack == "temp_drift_gradient" else 0,
        "feasible_attack_fraction": float(np.mean([item.get("feasible", True) for item in attack_info])),
        "feasible_candidate_fraction": float(np.mean([item.get("feasible_candidate_fraction", 1.0) for item in attack_info])),
        "runtime_seconds": float(runtime),
        "n_qubits": int(config["n_qubits"]),
        "checkpoint": str(checkpoint_path),
        "mean_trace_distance": float(drift[:, 0].mean()),
        "mean_one_minus_fidelity": float((1.0 - drift[:, 1]).mean()),
        "mean_delta_cls": float(np.mean([item["delta_cls"] for item in classical])),
        "mean_isi_tv": float(np.mean([item["isi_tv"] for item in classical])),
        "mean_measured_feature_drift": float(measured_feature_drifts.mean()),
        "mean_logit_drift": float(logit_drifts.mean()),
        "mean_prediction_js": float(js.mean()),
        "mean_clean_true_margin": float(clean_margins.mean()),
        "mean_attacked_true_margin": float(attacked_margins.mean()),
        "mean_margin_drop": float((clean_margins - attacked_margins).mean()),
        "clean_correct_attacked_positive_margin_fraction": float(
            (attacked_margins[torch.tensor(clean_correct)] > 0).float().mean()
        ) if denominator else 0.0,
    }
    if not return_samples:
        return summary
    samples = []
    for index, sample_id in enumerate(sample_ids):
        samples.append({
            "sample_id": int(sample_id),
            "true_label": int(labels[index]),
            "clean_prediction": int(clean_predictions[index]),
            "attacked_prediction": int(attacked_predictions[index]),
            "clean_correct": bool(clean_correct[index]),
            "attack_success": bool(successful[index]),
            "input_trace_distance": float(drift[index, 0]),
            "input_one_minus_fidelity": float(1.0 - drift[index, 1]),
            "delta_cls": float(classical[index]["delta_cls"]),
            "measured_feature_drift": float(measured_feature_drifts[index]),
            "logit_drift": float(logit_drifts[index]),
            "prediction_js": float(js[index]),
            "clean_true_margin": float(clean_margins[index]),
            "attacked_true_margin": float(attacked_margins[index]),
            "attacked_times": np.asarray(attacked_times[index]).tolist(),
        })
    return {"summary": summary, "samples": samples}


def evaluate_attack(
    config,
    checkpoint_path,
    attack,
    epsilon,
    tau=0.1,
    iterations=20,
    step_size=None,
    restarts=3,
):
    _, _, Xtest, _, _, ytest, _ = load_iris_splits(
        seed=int(config.get("split_seed", config["seed"])),
        test_size=float(config["test_size"]),
        val_size=float(config["val_size"]),
    )
    return evaluate_attack_data(
        config, checkpoint_path, attack, epsilon, Xtest, ytest, tau,
        iterations, step_size, restarts, split="test"
    )
