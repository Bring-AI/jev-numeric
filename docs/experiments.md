# Experimental record

## Frozen evidence

The five `jev-*` directories were exported from completed experiments in the source workspace.
Their payloads and responses are unchanged. The public copies of their scripts replace local
credential loading with portable environment-based settings; no successful response has been
regenerated or replaced. The initial bit experiment had a credential-path failure before any
request; only the successful run directory exists in the evidence.

The extra `binary-api-*` directory is a separately labeled follow-up with a different generic
prompt and two branches. It must not be pooled with the headline ten-way historical protocol.
All completed conditions are included, including this substantially worse closed-book result.

## What was and was not controlled

- Arithmetic: fixed 12 hand-picked expressions, six integers in 0..15 and six dyadic fractions.
  Direct choice lists 16 possible values; the range/grid are priors supplied by the experiment.
- Option-order controls reverse criterion insertion order while retaining the key-description
  pairing. Backend canonicalization, caching, and internal inference mechanics are unknown.
- Prompt controls cross original/explicit bit prompts with order and two repeated calls.
  Explicit prompts add both definitions and an arithmetic rule.
- Alternative interfaces share independent questions in API calls. Their logical sequential
  depths are known; their isolated latencies were not measured.
- Index recall: three fixed year-end dates, identical [0,10000) bounds, ten branches, six levels,
  lower-inclusive/upper-exclusive bins, final lower endpoint as the displayed value.
- Oracle-input: same question templates and initial options; only the verified close is added to
  state. Subsequent options differ because they depend on the model's preceding selections.
- Oracle-input is deliberately answer-provided. It separates reading a visible number from
  recalling an absent one. It is not a forecasting dataset or a claim of zero general error.
- All signed errors in the ten-way closed-book run are positive. We do not establish whether
  this is memory, prompt, label, or decision-path bias.

## Metrics

For truth y and decoded lower endpoint y_hat:

`APE = 100 * abs(y_hat - y) / abs(y)`; MAPE averages APE over runs, equally weighted.

Three dates have the same four repetitions each. MAPE is therefore also the mean of the
three per-date mean APEs. The README reports mean, median, and maximum relative error.

Arithmetic is also summarized with MAPE; all targets in this suite are nonzero. The original
exact-equality counts remain in the archived records. Decimal predictions are
not snapped onto that grid. Parallel thresholds are normalized, repaired with equal-weight
PAVA, converted to grid masses, and decoded using their mode with lower-value tie breaking.
Raw monotonicity violations are always retained. Calibration was not measured.

## Reproducibility boundaries

Live scripts call an external, versioned model; exact output replay is not guaranteed. The
archived responses, their hashes, offline metrics and deterministic decoder tests are the
reproducible evidence. Provider-reported costs are recorded, not independently billed costs.
Dates being historical does not establish inclusion in any model's pretraining data.

## Claim check

| Claim | Evidence | Scope |
|---|---|---|
| 4.58% MAPE | 12 ten-way recall runs | Three unique dates; max 6.49% |
| 0% readout error | 12 oracle-input runs | Answer is supplied; three unique values |
| Lower arithmetic relative error | Interval MAPE 2.42% versus direct 3.37% | Reused 12-case arithmetic suite |
| Distribution construction | Implemented thresholds + PAVA + histogram | Not validated calibrated uncertainty |
| Universally best method / OOD | No evidence | Not claimed |

## Self-review

Contribution: a concrete decision-to-number interface and controlled exploratory observations,
not a new numerical model. Clarity: native scores are distinguished from arbitrary numeric
readout. Strength: small samples and all completed negative controls are disclosed. Completeness:
requests, responses, costs, prompt/order variants and hashes are retained. Soundness: greedy
search, known bounds, finite precision and uncalibrated probabilities are explicit.

## Optional GitHub Actions

[github-actions-checks.yml](github-actions-checks.yml) is a ready-to-use workflow template.
Move it to `.github/workflows/checks.yml` with a GitHub credential that has workflow-write
permission to enable automatic checks. The publishing credential could not create workflows;
all documented offline checks were run locally before publication.
