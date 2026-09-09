# QSNN Scientific Workflow Rules for OpenCode

This project uses K-Dense Scientific Agent Skills through OpenCode.

## Required scientific behavior
- Use the relevant skill before making scientific conclusions.
- Keep implementation success separate from scientific success.
- Preserve train/validation/test separation.
- Never tune on held-out test data.
- Use paired common-clean-correct samples for attack comparisons when denominators differ.
- Report rescued, broken, both-fail, and both-robust outcomes when applicable.
- Use multi-seed evidence before robustness claims.
- Do not silently change Phase 14 attack definitions or frozen experiment protocols.
- Negative results are valid results and must be retained.
- For QSNN diagnosis, trace: raw Iris features -> normalization -> TTFS -> quantum/measured representation -> logits -> prediction.
- Treat sample-specific failures as sample-specific unless evidence shows a class-wide or representation-wide effect.
- Do not invent experimental values, citations, or files.

## Preferred skill routing
- experiment planning / ablation design -> experimental-design
- claim validity / methodological critique -> scientific-critical-thinking
- statistical evidence / significance / uncertainty -> statistical-analysis
- dataset and representation inspection -> exploratory-data-analysis
- quantum circuit / QSNN implementation context -> pennylane or cirq
- figures -> scientific-visualization
- manuscript writing -> scientific-writing
- reviewer-style audit -> peer-review
- related work -> literature-review

## Project-specific scientific gate
A defense is not considered successful merely because code/tests pass.
A robustness claim requires reproducible, paired, clean-preserving evidence under frozen evaluation.
