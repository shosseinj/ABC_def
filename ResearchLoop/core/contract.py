from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_write_json(path: str | Path, value: Any) -> str:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    return sha256_file(destination)


def deterministic_subset(sample_ids: Iterable[str | int], count: int, seed: int) -> list[str]:
    """Select IDs by a stable SHA-256 ordering, independent of input order."""
    unique = {str(item) for item in sample_ids}
    if count < 0 or count > len(unique):
        raise ValueError("count must be between zero and the number of unique sample IDs")
    return sorted(unique, key=lambda item: (hashlib.sha256(f"{seed}:{item}".encode()).digest(), item))[:count]


def clean_correct_asr(records: Sequence[Mapping[str, Any]]) -> dict[str, float | int]:
    eligible = [row for row in records if bool(row["clean_correct"])]
    successes = sum(bool(row["attack_success"]) for row in eligible)
    denominator = len(eligible)
    return {
        "clean_correct_count": denominator,
        "attack_success_count": successes,
        "asr": (successes / denominator * 100.0) if denominator else 0.0,
    }


def expand_integer_grid(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Expand [line][time] nonnegative counts into stable capacity-auditable packets.

    Multiple packets from one line/time bin are retained with unique IDs. Such an
    input will fail a capacity-1 audit until a valid retiming projection separates
    the packets; no count is silently converted to amplitude.
    """
    packets: list[dict[str, Any]] = []
    for line, times in enumerate(grid):
        for time, count in enumerate(times):
            if not isinstance(count, int) or count < 0:
                raise ValueError("integer grid counts must be nonnegative integers")
            for packet in range(count):
                packets.append({
                    "event_id": f"line{line}:time{time}:packet{packet}",
                    "t": time,
                    "line": str(line),
                    "value": 1,
                })
    return packets
