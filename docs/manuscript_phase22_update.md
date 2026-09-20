# Manuscript Update: Phase 22

## Mechanism Analysis

Phase 22 examined model-seed sensitivity using the fixed development split (split
seed 271) and existing frozen Phase 21 validation artifacts. Classical Timing PGD
was evaluated at timing budgets of 2% and 10% for model seeds 42, 777, and 2026.
Across all three seeds, TTFS coordinate 2 had the largest mean absolute attack
update. In contrast, attack outcomes were not seed-invariant, with the greatest
difference observed at the 10% budget. Among samples that were clean-correct for
all three seeds, both shared robust outcomes and mixed success/failure outcomes
were observed.

Across independently trained QSNN instances, TTFS coordinate 2 was consistently
identified as the most sensitive timing dimension. However, identical attack
budgets produced different classification outcomes across model seeds,
particularly at epsilon = 10%. This indicates that attack success is governed not
only by input-coordinate sensitivity but also by the seed-dependent geometry of
the learned decision boundary. Thus, the evidence supports decision-boundary seed
dependence more strongly than inconsistent TTFS coordinate sensitivity.

These observations extend the earlier diagnosis. Phase 18 did not support TTFS
information loss as the main mechanism, and Phase 21 did not support reproducible
representation instability as the explanation. Phase 22 therefore identifies
decision-boundary dependence as the currently best-supported explanation for the
observed seed variation. This remains a bounded, descriptive conclusion for one
fixed development split and the evaluated Classical Timing PGD attack.

Separate quantum-feature and logit gradient norms were not available in the frozen
artifacts. Phase 22 therefore does not identify the exact internal layer at which
the seed-dependent boundary sensitivity emerges.

## Experiment Summary

| Phase | Purpose | Outcome |
|---|---|---|
| Phase 22 | Seed-sensitivity diagnosis | Diagnostic success; coordinate-2 sensitivity consistent; attack failures seed-dependent; decision-boundary dependence supported |

## Defense Discussion

No additional defense is proposed at this stage. The Phase 22 result motivates a
future, falsifiable hypothesis about whether stabilizing decision-boundary
geometry across training seeds can reduce timing-attack variability. Such a
hypothesis should be tested only in a separately specified experiment with a
held-out evaluation protocol. Until that evidence exists, defense implications
remain provisional; Phase 22 does not establish a quantum-layer-specific defense
target.

## Revised Conclusion

The completed diagnosis supports the following mechanistic statement:

**Timing vulnerability is real, input sensitivity is partly consistent, but attack
success is strongly modulated by seed-dependent decision geometry.**

Phase 22 does not show that the quantum circuit is unstable, that coordinate 2
universally causes failure, that the classifier head alone is responsible, or that
representation instability is proven. It also does not resolve the internal layer
through which the seed-dependent sensitivity arises.

## Claim Audit

### Claims added

- TTFS coordinate 2 was the most sensitive timing coordinate for seeds 42, 777,
  and 2026 on split 271.
- Attack success differed across seeds, especially at epsilon = 10%.
- Common clean-correct samples included mixed success/failure outcomes.
- The current best-supported explanation is seed-dependent decision-boundary
  geometry, not inconsistent coordinate sensitivity.
- Separate quantum-feature and logit gradient norms were unavailable, limiting
  internal-layer attribution.

### Claims intentionally not made

- The quantum circuit is unstable.
- Coordinate 2 universally causes attack failure.
- The classifier head alone causes the failures.
- Representation instability is proven.
- Phase 22 establishes a new defense or general robustness.

### Remaining placeholders

- Author names, institution, email, and any venue-specific submission metadata
  remain placeholders in the source manuscript.
- The source manuscript's broader planned evaluations and empirical result
  sections remain unresolved where corresponding completed artifacts are absent.

### Conflict audit

The original manuscript conflicts with Phase 22 where it presents the evaluation
as a completed multi-benchmark study or states that empirical results will be
provided, while the available Phase 22 evidence is limited to one Iris
development split and frozen validation artifacts. The original manuscript also
contains stronger quantum-temporal drift and defense claims than Phase 22 can
support. Those claims should not be attributed to Phase 22 without additional
verified evidence.
