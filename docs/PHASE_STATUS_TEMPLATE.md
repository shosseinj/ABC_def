# Phase status log

Interpreter for every Python command:
`C:\Users\jafari.h\Desktop\ai_project\.venv\Scripts\python.exe`

| Phase | Status | Command / evidence | Output artifact | Notes |
|---:|---|---|---|---|
| 0 | PASS | `python scripts/check_environment.py` | console versions | NumPy 2.2.6, sklearn 1.7.2, Torch 2.5.1+cu124, PennyLane 0.42.3, pytest 9.1.1 |
| 1 | PASS | `python phase_runner.py --phase 1` (2 passed) | train/validation/test splits | scaler fitted on training only; all outputs clipped to TTFS domain |
| 2 | PASS | `python phase_runner.py --phase 2` (2 passed) | TTFS times | |
| 3 | PASS | `python phase_runner.py --phase 3` (2 passed) | quantum angles | |
| 4 | PASS | `python phase_runner.py --phase 4` (1 passed) | `[2,4] -> [2,3]`, 47 parameters | batch indexing uses `inputs[..., i]` |
| 5 | PASS | `python phase_runner.py --phase 5` (1 passed) | `checkpoints/iris_qsnn_best.pt`, history CSV | finite loss/gradients, weight update, checkpoint round trip |
| 6 | PASS | `python phase_runner.py --phase 6` (1 passed) | `results/iris_clean_metrics.json` | test accuracy 0.8667; validation-only loss tie-break |
| 7 | PASS | `python phase_runner.py --phase 7` (1 passed) | `results/iris_depth_ablation.{csv,json}` | fixed seed/config; validation is selection metric |
| 8 | PASS | `python phase_runner.py --phase 8` (2 passed) | randomized jitter | budgets 1%, 2%, 5%, 10% and boundaries verified |
| 9 | PASS | `python phase_runner.py --phase 9` (2 passed) | product-state drift metrics | aligned with four-qubit `RY(theta)` input state |
| 10 | PASS | `python phase_runner.py --phase 10` (2 passed) | classical mismatch | duplicate/order/boundary/small perturbation cases verified |
| 11 | PASS | `python phase_runner.py --phase 11` (1 passed) | `results/iris_attack_comparison.{csv,json}` | hard stealth feasibility; randomized reference only |
| 12 | PASS | `python phase_runner.py --phase 12` (1 passed) | attack comparison JSON/CSV | ASR denominator is 26 clean-correct test samples |
| 13 | PASS | `python phase_runner.py --phase 13` (1 passed) | `results/iris_attack_sweep.{csv,json}` | 12 epsilon/tau configurations; randomized reference only |
| 14 | PASS | `python phase_runner.py --phase 14` (3 passed) | `results/iris_attack_comparison_phase14.{csv,json}` | untargeted classification-loss PGD, 20 iterations, zero start, projected timing budget |
| 14.5 | PASS | `python phase_runner.py --phase 14.5` (3 passed) | `results/iris_attack_comparison_gradient.{csv,json}` | optimizes product-state 1-fidelity; exact final `Delta_cls <= tau`; 40 iterations, 3 restarts |
| 15 | PASS (negative experiment) | `python phase_runner.py --phase 15` (4 passed) | `results/iris_quantum_temp_phase15.{csv,json}` | measured-feature fidelity regularization; clean accuracy preserved but ASR/input-state drift unchanged at lambda 0.1 |
| 15.1 | PASS (negative/mixed experiment) | `python phase_runner.py --phase 15.1` (4 passed) | lambda ablations and `iris_quantum_temp_phase151_final.{csv,json}` | validation selected q=5, pred=0; final clean accuracy fell 3.33 pp, so robustness criterion failed |
| 15.2 | PASS (weak/mixed signal) | `python phase_runner.py --phase 15.2` (4 passed) | paired membership, attack, and drift artifacts | 25 common-correct; maximum net gain +1; no significant paired result |
| 15.3 | PASS (seed-sensitive/negative replication) | `python phase_runner.py --phase 15.3` (3 passed) | five-seed clean, paired, drift, and identity artifacts | PGD 10% positive in 2/5 seeds; gradient 10% positive in 1/5; no repeated rescue IDs |
| 16 | PASS (development; progression gate failed) | `python phase_runner.py --phase 16` | JS/margin ablations, gradients, three-seed validation | selected decision loss failed multi-seed validation gate; test correctly not accessed |
| 17 | PASS (implementation; negative validation) | `python phase_runner.py --phase 17` | training PGD tests, step/objective ablations, gradients, paired three-seed validation | PGD means improve, but 2/3 seeds lose >2 pp clean accuracy and seed 2026 breaks small-epsilon samples; test not accessed |
| 17.1 | PASS (calibration; negative validation) | `python phase_runner.py --phase 17.1` | lambda-adv ablation, class-2 samples, classwise margins/gradients, paired multi-seed validation | lower weights either hurt small-epsilon robustness or reproduce class-2 degradation; test not accessed |
| 17.2 | PASS (diagnosis only) | `python phase_runner.py --phase 17.2` | six frozen trajectories, fragile samples, margins, centroids, pressure, gradient conflict | sample 119 is intrinsically fragile; checkpoint selection contributes at seed 777 and boundary compression at seed 2026; test not accessed |
| 16-25 | NOT IMPLEMENTED | no gates | none | Iris defense onward remains scientifically incomplete |
