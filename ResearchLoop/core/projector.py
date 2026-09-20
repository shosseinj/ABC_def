from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class Candidate:
    event_id: str
    source_t: int
    target_t: int
    line: str
    probability: float


def strict_project(
    events: Iterable[Mapping[str, Any]],
    candidates: Iterable[Mapping[str, Any]],
    *,
    time_bins: int,
    budget_type: str,
    beta: int,
) -> list[dict[str, Any]]:
    """Conservative greedy P* projector following Appendix D's invariants.

    Candidates are sorted by probability and then shorter distance. Original
    occupied positions remain reserved until their packet is moved, preventing
    overwrites and symmetric swaps. This utility is suitable as an independent
    baseline and contract test; the differentiable PIL path remains repository code.
    """
    source: dict[str, dict[str, Any]] = {}
    for event in events:
        event_id = str(event["event_id"])
        if event_id in source:
            raise ValueError(f"duplicate event ID: {event_id}")
        source[event_id] = dict(event)
    reserved = {(str(e["line"]), int(e["t"])) for e in source.values()}
    occupied: set[tuple[str, int]] = set()
    moved: set[str] = set()
    spent_b1 = 0
    spent_b0 = 0
    out = {event_id: dict(e) for event_id, e in source.items()}
    btype = budget_type.replace("∞", "inf").lower()

    parsed: list[Candidate] = []
    for c in candidates:
        event_id = str(c["event_id"])
        if event_id not in source:
            continue
        s = int(source[event_id]["t"])
        t = int(c["target_t"])
        parsed.append(Candidate(event_id, s, t, str(source[event_id]["line"]), float(c["probability"])))
    parsed.sort(key=lambda c: (-c.probability, abs(c.target_t - c.source_t), c.event_id, c.target_t))

    for c in parsed:
        if c.event_id in moved or c.target_t == c.source_t or not 0 <= c.target_t < time_bins:
            continue
        distance = abs(c.target_t - c.source_t)
        target = (c.line, c.target_t)
        if target in occupied or target in reserved:
            continue
        if btype in ("b_inf", "binf") and distance > beta:
            continue
        if btype == "b1" and spent_b1 + distance > beta:
            continue
        if btype == "b0" and spent_b0 + 1 > beta:
            continue
        out[c.event_id]["t"] = c.target_t
        moved.add(c.event_id)
        reserved.discard((c.line, c.source_t))
        occupied.add(target)
        spent_b1 += distance
        spent_b0 += 1
    return [out[k] for k in sorted(out)]
