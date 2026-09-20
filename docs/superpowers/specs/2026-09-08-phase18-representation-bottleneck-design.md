# Phase 18 Representation-Bottleneck Diagnostic Design

## Objective

Determine the earliest QSNN pipeline stage at which Iris classes 1 and 2 lose measurable separability. Phase 18 is diagnostic only: it will not retrain models, tune parameters, redesign the defense or architecture, modify Phase 14 attacks, access held-out test observations, or make a robustness claim.

## Frozen Inputs

- Interpreter: `C:\Users\jafari.h\Desktop\ai_project\.venv\Scripts\python.exe`
- Canonical source: `sklearn.datasets.load_iris`
- Split seed: 42
- Model seeds: 42, 777, 2026
- Models per seed: Phase 17.2 baseline and representative Phase 17.1 defense checkpoints
- Defense configuration: PGD-1, `epsilon_train=0.02T`, `alpha=0.02T`, `lambda_adv=0.5`, `lambda_margin=0.5`, `margin_target=0.1`, `lambda_js=0`, `lambda_q=0`
- Attacks: unchanged Phase 14 Classical PGD at 2% and 10%

The training/validation-only loader will provide normalized training and validation values plus stable original sample IDs. Raw values will be indexed from the canonical Iris source only for dataset provenance, training/validation representations, and the explicitly requested validation sample 119 analysis. No held-out observations will enter model evaluation, fitting, selection, plotting, or representation diagnostics.

## Architecture

Add `experiments/iris/phase18.py` containing deterministic, independently tested diagnostic functions. Add `scripts/run_phase18_representation_diagnosis.py` to orchestrate frozen data/checkpoint loading, extraction, attacks, tables, plots, gate metadata, and the report. Add `tests/test_phase18_representation_diagnosis.py` and register Phase 18 in `phase_runner.py`.

The runner will reuse existing checkpoint state dictionaries. Missing required checkpoints will cause an explicit failure rather than silent retraining.

## Representation Flow

For every training and validation sample retained in scope, preserve its original Iris index and extract:

1. Raw four-feature vector.
2. Training-fitted MinMax normalized vector.
3. Continuous TTFS timing vector, `T(1-x)`.
4. Four measured quantum features before the linear head.
5. Three classifier logits.
6. Three softmax probabilities.

All row alignment will be asserted against stable original sample IDs.

## Descriptive Geometry

For every seed, model, and stage, compute class centroids, mean Euclidean within-class spread, pairwise centroid distances, nearest-centroid assignments, and Fisher-style descriptive separation. The primary class-1/class-2 ratio is:

`distance(centroid_1, centroid_2) / (spread_1 + spread_2)`

Zero denominators will return a documented finite-safe value or null status rather than infinity. Nearest-centroid accuracy is descriptive and will not be called model accuracy.

For class-1/class-2 overlap, use deterministic nearest-centroid assignment and local purity with fixed `k=3`. Self-neighbors will be excluded. Ties will follow stable sample-index and class ordering.

## Sample Controls and Raw Analysis

Trace validation samples 119, 122, and 142 through every stage. Report representation values, distances to class-1 and class-2 centroids, nearest centroid, three nearest neighbor labels, logits, prediction, true-class margin, and confidence where meaningful.

For sample 119, compute each raw feature's class-1 and class-2 mean, sample standard deviation, and z-score. Zero-standard-deviation safeguards will be explicit.

## TTFS Information and Collision Analysis

Compare normalized and TTFS centroid distances, spreads, and separation ratios. Raw-space quantities will also be reported, but raw-to-TTFS change will be interpreted cautiously because feature units differ before normalization.

An exact collision requires identical TTFS vectors. A near-collision is prespecified as cross-class `L-infinity <= 0.5` timing units, excluding exact collisions and self-pairs. The tolerance will be stored in output metadata and will not be tuned after inspection. Feature saturation counts and ordering preservation will also be reported.

Because continuous TTFS is affine after normalization, equal separation ratios are expected absent clipping or numerical effects; this is a tested prediction, not an assumed result.

## Linear Diagnostic

For stages raw, normalized, TTFS, and quantum features, fit a deterministic binary logistic regression using class-1/class-2 training representations only. Evaluate it on the corresponding validation representations. Fixed settings will be declared before results are viewed, with no hyperparameter search. Raw, normalized, and TTFS diagnostics are model-independent but may be repeated under each seed/model key to preserve the required table schema; the report will identify these duplicated values.

Compare the diagnostic classifier, nearest-centroid result, and frozen QSNN head on the same validation subset. These comparisons diagnose whether information is available to a simple linear boundary; they do not estimate final generalization performance.

## Attack and Amplification Analysis

Generate unchanged Phase 14 Classical PGD timings for every validation sample at 2% and 10%. For each class and model, compare clean and attacked timing, measured-feature, logit, probability-JS, and prediction states.

Use mean per-sample L2 displacement for timing, quantum features, and logits. Amplification ratios will divide by `max(denominator, 1e-12)` and will be reported as descriptive diagnostics only. ASR will retain the established clean-correct denominator. No attacked result will select a model, checkpoint, tolerance, or diagnostic rule.

## Visualization

Generate validation-only PCA plots for raw features, TTFS timings, and measured quantum features, plus class-1/class-2 margin histograms. Fit each PCA only to the validation representation displayed. Clearly mark samples 119, 122, and 142. PCA is illustrative; numerical geometry tables remain primary evidence.

## Root-Cause Decision Logic

Classify evidence as raw-data ambiguity, TTFS information loss, quantum representation compression, classifier boundary instability, adversarial amplification, or mixed cause. The report will not force a unique cause. If multiple stages degrade, prioritize the earliest reproducible loss across seeds while retaining downstream contributors.

No single arbitrary threshold will establish causation. Conclusions will triangulate centroid separation, spread, overlap, linear diagnostics, frozen-head behavior, attack movement, seed consistency, and the three prespecified sample controls.

## Artifacts and Reporting

Generate every required Phase 18 CSV/JSON artifact and the four requested plots under `results/plots`. `results/phase18_results.md` will contain the exact 25 requested numbered sections and explicitly answer all 12 scientific questions.

The gate artifact will record `test_set_accessed=false`, `test_loader_invoked=false`, checkpoint provenance, input hashes, Phase 14 source hash, fixed collision tolerance, fixed neighbor count, and the absence of final-test files.

## Testing and Verification

Tests will be written before production changes and will cover canonical dataset identity and shape, balanced classes, original sample mapping, example-CSV exclusion, representation/sample-ID alignment, centroid math, deterministic collisions and neighbors, train-only classifier fitting, validation-only attacks, forbidden test-loader absence, unchanged Phase 14 attack hash, artifact schemas, and Phase 18 registration.

Verification order:

1. Observe focused Phase 18 tests fail for missing behavior.
2. Implement the minimum diagnostic functions and runner.
3. Run the Phase 18 experiment with the required interpreter.
4. Run `phase_runner.py --phase 18`.
5. Run the full pytest suite.
6. Audit artifact row counts, schemas, hashes, plots, test-access flags, and all report sections.

