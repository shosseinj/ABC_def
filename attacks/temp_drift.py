import numpy as np
import torch
from encoding.quantum import angle_encode
from metrics.quantum_drift import trace_distance_from_bloch
from metrics.spike_statistics import classical_mismatch


def product_fidelity_torch(theta_a, theta_b):
    if theta_a.shape != theta_b.shape or theta_a.numel() == 0:
        raise ValueError("Angle tensors must have the same non-empty shape.")
    return torch.prod(torch.cos((theta_a - theta_b) / 2.0) ** 2)


def _stealth_surrogate(clean, adv, T):
    clean_isi = torch.diff(torch.sort(clean).values)
    adv_isi = torch.diff(torch.sort(adv).values)
    if clean_isi.numel() == 0:
        return torch.zeros((), dtype=adv.dtype)
    return torch.mean(torch.abs(adv_isi - clean_isi)) / T


def temp_drift_gradient(
    spike_times,
    epsilon,
    tau,
    T=100.0,
    iterations=40,
    step_size=None,
    restarts=3,
    stealth_weight=1.0,
    seed=42,
):
    """Maximize product-state 1-fidelity and retain only exact-feasible candidates."""
    clean = np.asarray(spike_times, dtype=np.float32)
    if clean.ndim != 1 or clean.size == 0:
        raise ValueError("spike_times must be a non-empty one-dimensional array.")
    if T <= 0 or epsilon < 0 or tau < 0 or iterations < 1 or restarts < 1:
        raise ValueError("Invalid gradient TEMP-DRIFT parameters.")
    if not np.isfinite(stealth_weight) or stealth_weight < 0:
        raise ValueError("stealth_weight must be finite and nonnegative.")
    if not np.all(np.isfinite(clean)) or np.any(clean < 0) or np.any(clean > T):
        raise ValueError("Spike times must be finite and lie in [0,T].")
    alpha = float(step_size if step_size is not None else epsilon / max(iterations // 4, 1))
    if not np.isfinite(alpha) or alpha <= 0:
        if epsilon == 0 and step_size is None:
            alpha = 1.0
        else:
            raise ValueError("step_size must be positive and finite.")

    clean_t = torch.tensor(clean, dtype=torch.float32)
    clean_theta = (torch.pi / 2.0) * clean_t / T
    best = clean.copy().astype(float)
    best_drift = 0.0
    best_classical = classical_mismatch(clean, clean, T=T)
    feasible_candidates = 1
    evaluated_candidates = 1
    generator = torch.Generator().manual_seed(int(seed))

    for _ in range(restarts):
        if epsilon > 0:
            delta = torch.empty_like(clean_t).uniform_(-epsilon, epsilon, generator=generator)
        else:
            delta = torch.zeros_like(clean_t)
        delta = torch.clamp(clean_t + delta, 0.0, T) - clean_t
        for _ in range(iterations):
            delta = delta.detach().requires_grad_(True)
            adv = torch.clamp(clean_t + delta, 0.0, T)
            adv_theta = (torch.pi / 2.0) * adv / T
            drift = 1.0 - product_fidelity_torch(clean_theta, adv_theta)
            surrogate = _stealth_surrogate(clean_t, adv, T)
            objective = drift - stealth_weight * torch.relu(surrogate - tau)
            gradient = torch.autograd.grad(objective, delta)[0]
            if not torch.isfinite(gradient).all():
                raise RuntimeError("Non-finite TEMP-DRIFT gradient encountered.")
            with torch.no_grad():
                delta = delta + alpha * gradient.sign()
                delta.clamp_(-epsilon, epsilon)
                delta.copy_(torch.clamp(clean_t + delta, 0.0, T) - clean_t)
                candidate = torch.clamp(clean_t + delta, 0.0, T).numpy().astype(float)
            evaluated_candidates += 1
            exact = classical_mismatch(clean, candidate, T=T)
            if exact["delta_cls"] <= tau + 1e-12:
                feasible_candidates += 1
                candidate_theta = angle_encode(candidate, T)
                candidate_drift = trace_distance_from_bloch(angle_encode(clean, T), candidate_theta)
                if candidate_drift > best_drift:
                    best = candidate.copy()
                    best_drift = candidate_drift
                    best_classical = exact

    fidelity = float(np.prod(np.cos((angle_encode(clean, T) - angle_encode(best, T)) / 2.0) ** 2))
    return best, {
        "objective": "product_state_one_minus_fidelity",
        "quantum_drift": best_drift,
        "fidelity": fidelity,
        "one_minus_fidelity": 1.0 - fidelity,
        **best_classical,
        "feasible": bool(best_classical["delta_cls"] <= tau + 1e-12),
        "attack_found": bool(best_drift > 0.0),
        "feasible_candidate_fraction": feasible_candidates / evaluated_candidates,
        "iterations": int(iterations),
        "step_size": alpha,
        "restarts": int(restarts),
        "stealth_surrogate": "mean_absolute_sorted_isi_displacement_over_T",
        "seed": int(seed),
    }

def temp_drift_reference(spike_times, epsilon, tau, T=100.0,
                         steps=200, candidates=64, seed=42):
    t = np.asarray(spike_times, dtype=float)
    if T <= 0 or epsilon < 0 or tau < 0 or steps < 1 or candidates < 1:
        raise ValueError("Invalid TEMP-DRIFT search parameters.")
    if not np.all(np.isfinite(t)) or np.any(t < 0) or np.any(t > T):
        raise ValueError("Spike times must be finite and lie in [0,T].")
    rng = np.random.default_rng(seed)
    clean_theta = angle_encode(t, T)
    best = t.copy()
    best_score = 0.0
    best_info = {"quantum_drift": 0.0, **classical_mismatch(t, t, T=T), "score": 0.0}
    for _ in range(steps):
        for _ in range(candidates):
            delta = rng.uniform(-epsilon, epsilon, size=t.shape)
            cand = np.clip(t + delta, 0.0, T)
            q = trace_distance_from_bloch(clean_theta, angle_encode(cand, T))
            c = classical_mismatch(t, cand, T=T)
            score = q
            if c["delta_cls"] <= tau and score > best_score:
                best_score = score
                best = cand
                best_info = {"quantum_drift": q, **c, "score": score}
    return best, best_info
