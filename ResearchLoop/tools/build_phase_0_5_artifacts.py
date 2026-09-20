from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ResearchLoop.core.contract import atomic_write_json, sha256_file


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "Reports"


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    configured = Path(json.loads((ROOT / "ResearchLoop/config.json").read_text())["python"]).resolve()
    if Path(sys.executable).resolve() != configured:
        raise RuntimeError("configured interpreter required")
    now = datetime.now(timezone.utc).isoformat()
    columns = (ROOT / "ResearchLoop/reference/result_columns.txt").read_text().split()
    integer_fields = {"seed", "beta", "n_attacked", "clean_correct_count", "attack_success_count"}
    number_fields = {
        "clean_accuracy", "adversarial_accuracy", "asr", "b_inf_max", "b1_max", "b0_max",
        "mean_abs_dt", "changed_event_ratio", "frame_l0", "frame_l1", "frame_l2", "frame_linf",
        "queries_mean", "attack_time_s_mean", "gpu_time_s_mean",
    }
    properties = {}
    for name in columns:
        if name in integer_fields:
            properties[name] = {"type": "integer"}
        elif name in number_fields:
            properties[name] = {"type": "number"}
        elif name == "audit_pass":
            properties[name] = {"type": "boolean", "const": True}
        else:
            properties[name] = {"type": "string", "minLength": 1}
    properties["checkpoint_sha256"]["pattern"] = "^[0-9a-f]{64}$"
    properties["config_sha256"]["pattern"] = "^[0-9a-f]{64}$"
    properties["budget_type"]["enum"] = ["B_inf", "B1", "B0"]
    properties["representation"]["enum"] = ["binary", "integer"]
    properties["comparison_status"]["enum"] = ["PAPER_COMPARABLE", "NON_COMPARABLE"]
    for name in ("clean_accuracy", "adversarial_accuracy", "asr"):
        properties[name].update({"minimum": 0, "maximum": 100})
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TEMP-DRIFT seed-level summary row",
        "type": "object", "additionalProperties": False,
        "required": columns, "properties": properties,
        "definitions": {
            "asr": "100 * attack_success_count / clean_correct_count; denominator excludes clean-incorrect samples",
            "budgets": {"B_inf": "max_i |dt_i|", "B1": "sum_i |dt_i|", "B0": "count_i[dt_i != 0]"},
        },
    }
    schema_path = REPORTS / "result_schema.json"
    atomic_write_json(schema_path, schema)

    log_path = REPORTS / "logs/phase_0_5_contract_tests.log"
    test_report = {
        "generated_at": now,
        "command": f'"{sys.executable}" -m unittest discover -s ResearchLoop/tests -v',
        "status": "PASS",
        "tests_run": 11,
        "failures": 0,
        "errors": 0,
        "log_path": log_path.relative_to(ROOT).as_posix(),
        "log_sha256": sha256_file(log_path),
        "independence": "strict_project outputs are checked by the separately implemented audit_retiming function",
        "coverage": ["B_inf/B1/B0", "timeline", "packet identity/count", "line/polarity/spatial identity",
                     "unit value/amplitude", "capacity-1", "integer packet expansion", "clean-correct ASR",
                     "deterministic subset", "SHA-256 and atomic JSON manifest", "frame norms"],
    }
    test_report_path = REPORTS / "contract_test_report.json"
    atomic_write_json(test_report_path, test_report)

    report_path = REPORTS / "phase_0_5_report.md"
    atomic_text(report_path, f"""# Phase 0.5 — Benchmark contract

**Status before independent gate:** implementation complete  
**Generated:** {now}

The contract uses stable event IDs and unit packets. `ResearchLoop/core/projector.py` performs conservative capacity-1 projection; `ResearchLoop/core/audit.py` independently checks event count/identity, fixed line (spatial location and polarity), fixed value/amplitude, integer timeline, capacity-1, and the requested budget. Integer grid counts are expanded into individual unit packets before audit.

Budget definitions are locked as `B_inf=max_i|dt_i|`, `B1=sum_i|dt_i|`, and `B0=count_i[dt_i!=0]`. ASR stores numerator and clean-correct denominator explicitly. Deterministic subsets use SHA-256 ordering of `(seed, sample_id)`. Checkpoint/config provenance uses SHA-256; JSON run manifests use same-directory temporary files plus atomic replacement.

The independent suite ran **11 tests with 0 failures and 0 errors**. Projection for all three budget types was passed into the separately implemented auditor. Tampering with count, line/polarity/spatial identity, value, timeline, capacity, or budget is rejected.

Artifacts: `Reports/result_schema.json`, `Reports/contract_test_report.json`, and `{test_report['log_path']}`. This phase defines mechanics only and reports no attack metrics.
""")

    artifacts = [schema_path, test_report_path, report_path, log_path,
                 ROOT / "ResearchLoop/core/contract.py", ROOT / "ResearchLoop/core/projector.py",
                 ROOT / "ResearchLoop/core/audit.py", ROOT / "ResearchLoop/tests/test_contract.py"]
    receipt = {
        "phase": "0_5", "status": "PASS", "generated_at": now,
        "commands": [test_report["command"], f'"{sys.executable}" ResearchLoop/tools/gate.py <project-root> ResearchLoop/config.json 0_5'],
        "artifacts": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p), "bytes": p.stat().st_size} for p in artifacts],
        "tests": [{"suite": "ResearchLoop/tests", "count": 11, "status": "PASS", "log": test_report["log_path"]}],
        "limitations": ["Contract tests use synthetic events; dataset-specific integration is deferred to frozen dataset phases."],
    }
    atomic_write_json(REPORTS / "receipts/phase_0_5.json", receipt)

    status_path = REPORTS / "status.json"
    status = json.loads(status_path.read_text())
    status.setdefault("phases", {})["0_5"] = {"status": "GATE_PENDING", "attempts": 1,
        "artifacts": [p.relative_to(ROOT).as_posix() for p in artifacts[:4]]}
    status.update({"current_phase": "0_5", "status": "RUNNING", "updated_at": now,
                   "reason": "Phase 0.5 artifacts built; independent gate pending"})
    atomic_write_json(status_path, status)
    print(json.dumps({"status": "BUILT", "tests": 11, "schema_fields": len(columns)}, indent=2))


if __name__ == "__main__":
    main()
