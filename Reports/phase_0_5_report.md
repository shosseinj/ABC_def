# Phase 0.5 — Benchmark contract

**Status before independent gate:** implementation complete  
**Generated:** 2026-09-20T10:53:16.236667+00:00

The contract uses stable event IDs and unit packets. `ResearchLoop/core/projector.py` performs conservative capacity-1 projection; `ResearchLoop/core/audit.py` independently checks event count/identity, fixed line (spatial location and polarity), fixed value/amplitude, integer timeline, capacity-1, and the requested budget. Integer grid counts are expanded into individual unit packets before audit.

Budget definitions are locked as `B_inf=max_i|dt_i|`, `B1=sum_i|dt_i|`, and `B0=count_i[dt_i!=0]`. ASR stores numerator and clean-correct denominator explicitly. Deterministic subsets use SHA-256 ordering of `(seed, sample_id)`. Checkpoint/config provenance uses SHA-256; JSON run manifests use same-directory temporary files plus atomic replacement.

The independent suite ran **11 tests with 0 failures and 0 errors**. Projection for all three budget types was passed into the separately implemented auditor. Tampering with count, line/polarity/spatial identity, value, timeline, capacity, or budget is rejected.

Artifacts: `Reports/result_schema.json`, `Reports/contract_test_report.json`, and `Reports/logs/phase_0_5_contract_tests.log`. This phase defines mechanics only and reports no attack metrics.
