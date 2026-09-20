from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from math import sqrt
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class AuditResult:
    passed: bool
    b_inf: int
    b1: int
    b0: int
    mean_abs_dt: float
    changed_event_ratio: float
    count_preserved: bool
    line_preserved: bool
    value_preserved: bool
    timeline_valid: bool
    capacity1_valid: bool
    budget_valid: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["errors"] = list(self.errors)
        return data


def _index(events: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for event in events:
        event_id = str(event["event_id"])
        if event_id in indexed:
            raise ValueError(f"duplicate event_id: {event_id}")
        indexed[event_id] = event
    return indexed


def audit_retiming(
    clean_events: Iterable[Mapping[str, Any]],
    adv_events: Iterable[Mapping[str, Any]],
    *,
    time_bins: int,
    budget_type: str,
    beta: int,
) -> AuditResult:
    """Audit packet-aligned events independently of the attack implementation.

    Each event is {event_id, t, line, value}. Integer grids must be expanded
    into unit packets with stable event IDs before calling this function.
    """
    clean = _index(clean_events)
    adv = _index(adv_events)
    errors: list[str] = []
    count_preserved = set(clean) == set(adv)
    if not count_preserved:
        errors.append("event IDs differ: event creation/deletion/splitting detected")

    common = sorted(set(clean) & set(adv))
    line_preserved = all(clean[i]["line"] == adv[i]["line"] for i in common)
    value_preserved = all(clean[i]["value"] == adv[i]["value"] for i in common)
    if not line_preserved:
        errors.append("event line/polarity/spatial identity changed")
    if not value_preserved:
        errors.append("event amplitude/value changed")

    timeline_valid = all(
        isinstance(adv[i]["t"], int) and 0 <= adv[i]["t"] < time_bins for i in common
    )
    if not timeline_valid:
        errors.append("adversarial timestamp is non-integer or outside timeline")

    occupancy = Counter((adv[i]["line"], adv[i]["t"]) for i in common)
    capacity1_valid = all(v <= 1 for v in occupancy.values())
    if not capacity1_valid:
        errors.append("capacity-1 violation")

    delta = [abs(int(adv[i]["t"]) - int(clean[i]["t"])) for i in common]
    b_inf = max(delta, default=0)
    b1 = sum(delta)
    b0 = sum(d != 0 for d in delta)
    budget_type = budget_type.replace("∞", "inf").lower()
    observed = {"b_inf": b_inf, "binf": b_inf, "b1": b1, "b0": b0}.get(budget_type)
    if observed is None:
        raise ValueError(f"unknown budget type: {budget_type}")
    budget_valid = observed <= beta
    if not budget_valid:
        errors.append(f"budget exceeded: observed={observed}, beta={beta}")

    passed = all((count_preserved, line_preserved, value_preserved, timeline_valid,
                  capacity1_valid, budget_valid))
    return AuditResult(
        passed=passed,
        b_inf=b_inf,
        b1=b1,
        b0=b0,
        mean_abs_dt=(b1 / len(delta)) if delta else 0.0,
        changed_event_ratio=(b0 / len(delta)) if delta else 0.0,
        count_preserved=count_preserved,
        line_preserved=line_preserved,
        value_preserved=value_preserved,
        timeline_valid=timeline_valid,
        capacity1_valid=capacity1_valid,
        budget_valid=budget_valid,
        errors=tuple(errors),
    )


def frame_distortion(clean: list[float], adv: list[float]) -> dict[str, float]:
    if len(clean) != len(adv):
        raise ValueError("frame tensors must have equal flattened length")
    d = [abs(float(a) - float(b)) for a, b in zip(clean, adv)]
    return {
        "frame_l0": float(sum(x != 0 for x in d)),
        "frame_l1": sum(d),
        "frame_l2": sqrt(sum(x * x for x in d)),
        "frame_linf": max(d, default=0.0),
    }
