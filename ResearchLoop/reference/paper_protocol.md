# Locked reference protocol

Source: “Time Is All It Takes: Spike-Retiming Attacks on Event-Driven Spiking Neural Networks”, arXiv:2602.03284v1, 3 February 2026.

Primary source: https://arxiv.org/html/2602.03284v1

## Threat model

- Untargeted white-box attack in the main experiments.
- Existing spike packets are moved only along time on their fixed event line.
- No packet is created, deleted, split, rescaled, moved spatially, or moved across polarity.
- Discrete timestamps remain in `[0, T)`; the main protocol uses `T=10`.
- Capacity-1/non-overlap is enforced for every event-line/time-bin.
- PIL-PGD evaluates the strict projected input on the forward pass and follows the soft retiming surrogate on the backward pass.

## Main attack defaults

- temperature kappa = 1
- logit step alpha = 1
- logit clip = 10
- iterations = 20 for B_inf, 40 for B1/B0
- capacity penalty = 20
- budget penalty = 10

## Evaluation

- ASR is measured only on clean-correct examples.
- Paper subsets: all DVS-Gesture clean-correct test examples, 1000 N-MNIST clean-correct test examples, and 100 CIFAR10-DVS clean-correct test examples.
- Both binary and integer event grids are reported.
- `reference_results.csv` transcribes Tables 1 and 2. It is immutable reference data, not an experiment output.
- The paper does not provide the five-seed protocol requested for this project. Reference-table comparisons therefore require an explicit provenance/methodology warning; the project's mean/SD/CI are new results rather than claimed paper replications.

## Comparison rule

Only exact matches of dataset, representation, T, model, attack definition, metric denominator, budget type, beta, and attacked-subset policy may be labeled `PAPER_COMPARABLE`. All others must be `NON_COMPARABLE` and may be shown only as contextual evidence.

