
# Automated Workflow

All reports are stored in:

Reports/

Required:

status.json


Phase transition:

PASS -> continue automatically

FAIL/BLOCKED -> stop


Execution chain:

Phase 0
 ↓
Phase 0.5
 ↓
Phase 1
 ↓
Phase 2
 ↓
Phase 3
 ↓
Phase 4
 ↓
Phase 5
 ↓
Phase 6
 ↓
Phase 7
 ↓
Phase 8
 ↓
Phase 9


Resume rule:

If interrupted:
- read status.json
- inspect reports
- continue from last valid checkpoint


No completed valid experiment should be rerun.
