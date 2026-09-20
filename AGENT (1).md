
# TEMP-DRIFT Automated Research Agent v4

## Mission

Automate the complete research workflow for:

SNN + TEMP-DRIFT benchmark evaluation

Compared against:
"Time Is All It Takes: Spike-Retiming Attacks on Event-Driven Spiking Neural Networks"

The agent performs:
- experiment management
- validation
- auditing
- reporting
- phase transitions

No paper writing.
No figures.

---

## Environment

Repository:
C:\Users\jafari.h.SPADANACO\Desktop\ai_project\testing\qsnn_temp_drift_project

Python:
C:\Users\jafari.h.SPADANACO\Desktop\ai_project\.venv\Scripts\python.exe

Always use this interpreter.

---

## Automatic Execution Rule

No human approval is required between phases.

After every phase:

Check:
Reports/status.json

Continue automatically only if:

STATUS = PASS

and:
- tests passed
- audit passed
- no unresolved blockers

If FAIL/BLOCKED:
stop and create diagnostic report.

---

# Phase 0
Repository inspection.

Tasks:
- inspect code
- inspect checkpoints
- inspect datasets
- inspect attacks
- inspect audit system
- update readme_jafar.md

Output:

Reports/phase_0_report.md

---

# Phase 0.5
Benchmark Contract.

Implement:

## Budget constraints

B∞:
maximum timestamp displacement

B1:
total timestamp displacement

B0:
number of modified timestamps


Create:

- budget projectors
- independent auditor
- result schema
- unit tests


Output:

Reports/phase_0_5_report.md


Only after PASS continue.

---

# Phase 1
N-MNIST Benchmark

Model:
SNN

Attack:
TEMP-DRIFT


Seeds:

42
123
777
2026
6543


Budget grid:

B∞:
1,2,3

B1:
500,750,1000,1500

B0:
200,300,400,600


For every seed:

1. Run experiment
2. Audit results
3. Compare with reference table
4. Generate report


Outputs:

Reports/phase_1_seed_report.md
Reports/phase_1_NMNIST_final_report.md


If seed passes:
automatically continue next seed.

---

# Phase 2
DVS-Gesture Benchmark

Model:
SNN

Attack:
TEMP-DRIFT


Budgets:

B∞:
1,2,3

B1:
2000,4000,8000,16000

B0:
1000,2000,4000,8000


Output:

Reports/phase_2_DVSGesture_report.md

---

# Phase 3
CIFAR10-DVS Benchmark

Model:
SNN

Attack:
TEMP-DRIFT


Budgets:

B∞:
1,2,3

B1:
2000,4000,8000,16000

B0:
1000,2000,4000,8000


Output:

Reports/phase_3_CIFAR10DVS_report.md

---

# Phase 4
Reference Comparison

Generate:

benchmark_comparison.csv
benchmark_comparison.md

Compare:

Reference:
- ConvNet
- ResNet18
- VGGSNN
- SpResF

Ours:
- SNN + TEMP-DRIFT


Output:

Reports/phase_4_comparison_report.md

---

# Phase 5
Statistical Analysis

Calculate:

- mean
- std
- confidence interval
- seed variance

Output:

Reports/phase_5_statistics_report.md

---

# Phase 6
Stealth and Distortion Analysis

Metrics:

Temporal:
- mean timestamp shift
- max shift
- changed event ratio

Frame:
- L0
- L1
- L2
- Linf

Stealth:
- ISI histogram
- Δcls


Output:

Reports/phase_6_stealth_report.md

---

# Phase 7
QSNN Quantum Analysis

Separate extension.

Metrics:

- fidelity
- trace distance
- density matrix

Clean vs adversarial quantum state.


Output:

Reports/phase_7_quantum_report.md

---

# Phase 8
Defense Evaluation

Evaluate:

- filtering
- smoothing
- temporal regularization
- adversarial training


Measure:

- ASR reduction
- accuracy impact
- distortion


Output:

Reports/phase_8_defense_report.md

---

# Phase 9
Final Research Package

Generate:

Reports/final_report.md

Include:

- datasets
- seeds
- attacks
- defenses
- audits
- comparisons

---

# Global Rules

Always:

- resume after interruption
- save checkpoints
- update progress
- update status.json
- store reports in Reports/

Never:

- invent results
- weaken audits
- change attack definitions
- overwrite valid results
