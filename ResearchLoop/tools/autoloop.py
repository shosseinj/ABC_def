from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gate import run_gate


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def preflight(repo: Path, config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not repo.is_dir():
        errors.append(f"project root does not exist: {repo}")
    python = Path(config["python"])
    if not python.is_file():
        errors.append(f"configured Python does not exist: {python}")
    if repo.is_dir() and not (repo / "ResearchLoop").is_dir():
        errors.append("ResearchLoop directory is not under project root; extract the ZIP into the project root")
    if not shutil.which("opencode"):
        errors.append("OpenCode was not found on PATH; install it and reopen PowerShell")
    if python.is_file():
        test = subprocess.run([str(python), "-c", "import sys; print(sys.executable)"], text=True, capture_output=True)
        if test.returncode:
            errors.append("configured Python cannot start: " + test.stderr[-1000:])
    return errors


def backend(config: dict[str, Any]) -> str | None:
    if config.get("backend") != "opencode":
        return None
    return "opencode" if shutil.which("opencode") else None


def make_prompt(repo: Path, phase: dict[str, Any], attempt: int, gate_errors: list[str]) -> str:
    contract = (repo / "AGENTS.md").read_text(encoding="utf-8", errors="replace")
    config = (repo / "ResearchLoop" / "config.json").read_text(encoding="utf-8")
    phase_text = json.dumps(phase, indent=2)
    gate = json.dumps(gate_errors, indent=2)
    return f"""You are resuming an autonomous research engineering run.

CURRENT PHASE:\n{phase_text}
ATTEMPT: {attempt}
LAST INDEPENDENT GATE ERRORS:\n{gate}

Read the repository and current Reports/status.json before acting. Complete this phase, execute real tests/experiments with the configured interpreter, independently audit outputs, update the required report, and write the phase receipt. Do not proceed to another phase; the external loop owns progression. Do not fabricate metrics or mark unavailable work PASS. Repair ordinary failures autonomously. If truly blocked under the contract, write Reports/diagnostic_blocker.md and a receipt with status BLOCKED.

CONFIG:\n{config}

REPOSITORY CONTRACT:\n{contract}
"""


def invoke_agent(name: str, repo: Path, config: dict[str, Any], prompt: str, log: Path) -> int:
    timeout = int(config.get("agent_timeout_minutes", 360)) * 60
    if name != "opencode":
        raise ValueError("This package is OpenCode-only")
    args = [a.replace("{repo}", str(repo)).replace("{prompt}", prompt) for a in config["opencode_args"]]
    cmd = [shutil.which("opencode") or "opencode", *args]
    input_text = None
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as handle:
        handle.write(f"START {now()}\nBACKEND {name}\nCOMMAND {cmd[:5]}\n\n")
        handle.flush()
        try:
            proc = subprocess.run(cmd, cwd=repo, input=input_text, text=True, stdout=handle,
                                  stderr=subprocess.STDOUT, timeout=timeout)
            handle.write(f"\nEND {now()} EXIT {proc.returncode}\n")
            return proc.returncode
        except subprocess.TimeoutExpired:
            handle.write(f"\nTIMEOUT {now()} after {timeout}s\n")
            return 124


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    errors = preflight(repo, config)
    if errors:
        print(json.dumps({"status": "BLOCKED", "errors": errors}, indent=2))
        return 2
    if args.preflight_only:
        print(json.dumps({"status": "PASS", "repo": str(repo), "python": config["python"]}, indent=2))
        return 0

    reports = repo / "Reports"
    reports.mkdir(exist_ok=True)
    stop = reports / "STOP_REQUESTED"
    lock = reports / "autoloop.lock"
    if lock.exists():
        print(f"Loop lock exists: {lock}. Remove it only if no loop process is active.")
        return 3
    lock.write_text(f"pid={os.getpid()} started={now()}\n", encoding="utf-8")
    status_path = reports / "status.json"
    phases = load_json(repo / "ResearchLoop" / "phases.json")
    state = load_json(status_path) if status_path.exists() else {
        "project": "SNN + TEMP-DRIFT spike-retiming attack benchmark",
        "created_at": now(), "current_phase": phases[0]["id"], "phases": {}
    }
    try:
        agent = backend(config)
        if not agent:
            state.update({"status": "BLOCKED", "updated_at": now(),
                          "reason": "OpenCode CLI is not available on PATH"})
            atomic_json(status_path, state)
            (reports / "diagnostic_blocker.md").write_text(
                "# Automation blocker\n\n`opencode` was not found on PATH. Install/authenticate OpenCode, then rerun `ResearchLoop\\RUN_LOOP.ps1`. No experiment was marked complete.\n",
                encoding="utf-8")
            return 2

        for phase in phases:
            pid = phase["id"]
            passed, gate_errors = run_gate(repo, config, phase)
            if passed:
                state["phases"][pid] = {"status": "PASS", "validated_at": now()}
                atomic_json(status_path, state)
                continue
            max_attempts = int(config.get("max_repair_attempts_per_phase", 8))
            prior_attempts = int(state["phases"].get(pid, {}).get("attempts", 0))
            for attempt in range(prior_attempts + 1, max_attempts + 1):
                if stop.exists():
                    state.update({"status": "PAUSED", "current_phase": pid, "updated_at": now()})
                    atomic_json(status_path, state)
                    stop.unlink(missing_ok=True)
                    return 0
                state.update({"status": "RUNNING", "current_phase": pid, "updated_at": now()})
                state["phases"][pid] = {"status": "RUNNING", "attempts": attempt, "last_gate_errors": gate_errors}
                atomic_json(status_path, state)
                prompt = make_prompt(repo, phase, attempt, gate_errors)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log = reports / "logs" / f"phase_{pid}_attempt_{attempt}_{stamp}.log"
                exit_code = invoke_agent(agent, repo, config, prompt, log)
                passed, gate_errors = run_gate(repo, config, phase)
                state["phases"][pid].update({"agent_exit_code": exit_code, "log": str(log.relative_to(repo)),
                                             "last_gate_errors": gate_errors, "updated_at": now()})
                atomic_json(status_path, state)
                if passed:
                    state["phases"][pid].update({"status": "PASS", "validated_at": now()})
                    atomic_json(status_path, state)
                    break
                receipt = reports / "receipts" / f"phase_{pid}.json"
                if receipt.exists():
                    try:
                        if load_json(receipt).get("status") == "BLOCKED":
                            state.update({"status": "BLOCKED", "current_phase": pid, "updated_at": now()})
                            atomic_json(status_path, state)
                            return 2
                    except Exception:
                        pass
            if not passed:
                state.update({"status": "NEEDS_INTERVENTION", "current_phase": pid, "updated_at": now(),
                              "reason": f"independent gate failed after {max_attempts} repair attempts"})
                atomic_json(status_path, state)
                (reports / "diagnostic_blocker.md").write_text(
                    "# Repair-loop exhaustion\n\n" + "\n".join(f"- {e}" for e in gate_errors) +
                    "\n\nNo failed result was promoted to PASS. See the latest phase log.\n", encoding="utf-8")
                return 4
        state.update({"status": "PASS", "current_phase": "complete", "completed_at": now(), "updated_at": now()})
        atomic_json(status_path, state)
        return 0
    except KeyboardInterrupt:
        state.update({"status": "PAUSED", "updated_at": now(), "reason": "keyboard interrupt"})
        atomic_json(status_path, state)
        return 130
    except Exception:
        state.update({"status": "CRASHED", "updated_at": now(), "traceback": traceback.format_exc()})
        atomic_json(status_path, state)
        return 1
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
