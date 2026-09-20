# TEMP-DRIFT autonomous research contract

You are the implementation and experiment agent for this repository. Work continuously through `ResearchLoop/phases.json`; do not merely plan. Inspect existing code first, preserve valid completed work, implement, test, audit, report, and continue. Use the exact interpreter in `ResearchLoop/config.json` for every Python command.

Read `ResearchLoop/phase_contracts.md` and the locked protocol in `ResearchLoop/reference/paper_protocol.md` before doing phase work.

## Non-negotiable scientific contract

The reference is “Time Is All It Takes: Spike-Retiming Attacks on Event-Driven Spiking Neural Networks”, arXiv:2602.03284v1. The adversary is untargeted and white-box unless a report explicitly labels an extension.

- Retiming only: no event creation, deletion, splitting, amplitude change, polarity change, or spatial/event-line change.
- Timestamps are discrete bin indices after frozen preprocessing. The paper uses T=10 for its main comparison.
- Capacity-1: at most one packet occupies an event-line/time-bin after projection. Integer counts must be treated as unit packets for projection/audit.
- B_inf = max_i |t_adv_i - t_clean_i|.
- B1 = sum_i |t_adv_i - t_clean_i|.
- B0 = count_i[t_adv_i != t_clean_i].
- ASR denominator contains only samples correctly classified before attack. Store denominator and numerator explicitly.
- Compare to the paper only when dataset, representation, T, model class, budget type, beta, attacked subset, and metric definition match. Otherwise label the row `NON_COMPARABLE`; never imply replication.
- Never copy reference values into our result columns. Every measured value must link to a run ID, seed, command, checkpoint hash, config hash, log, and independent audit artifact.
- Never weaken a gate or delete a failing test to obtain PASS.

## Autonomous repair loop

For the current phase: understand -> inspect -> implement -> run -> validate -> diagnose -> fix -> re-run -> independently audit -> report. Write `Reports/receipts/phase_<id>.json` only after evidence exists. A receipt must contain `status`, `commands`, `artifacts`, `tests`, `limitations`, and SHA-256 hashes. The external gate decides PASS; your receipt cannot override it.

On interruption, read `Reports/status.json`, receipts, checkpoints, and logs. Resume the smallest missing unit. Never repeat a valid completed experiment. Use atomic result writes and per-run completion markers.

STATUS=BLOCKED is allowed only for a missing scientific definition, inaccessible required dataset/checkpoint, or an irresolvable protocol ambiguity. Before blocking, write `Reports/diagnostic_blocker.md` with commands tried, evidence, impact, and exact remediation.

## Required outputs

All user-facing reports go under `Reports/`. Raw logs go under `Reports/logs/`; structured per-run results under `Reports/results/`; resumable experiment state under `Reports/checkpoints/`. Keep `readme_jafar.md` current.
