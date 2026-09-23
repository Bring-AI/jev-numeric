# Walker continuation: from arithmetic errors to interval comparisons

All results below are recorded live Jev API episodes or explicitly separated offline diagnostics. Normal `BipedalWalker-v3`, fixed seeds 7 and 19, unchanged physics and 1600-frame horizon. No model training, action override, or fallback controller.

## Recorded episodes

The comparison-table protocol completed **1 of 2 development trajectories**. An interrupted source and its continuation count as one trajectory here, while both records remain listed below. This small, selected development sample is not a general success-rate estimate. All prior attempts remain in the public experiment history.

| Protocol | Seed | Physics frames | Reward | Final torso x | Outcome | API calls | Wall minutes |
|---|---:|---:|---:|---:|---|---:|---:|
| composed-v1 | 7 | 164 | -79.6081 | 11.3605 | fall | 656 | 2.94 |
| comparison-v2 | 7 | 979 | 43.4381 | 44.9946 | fall | 3916 | 21.18 |
| comparison-v2 (continued) | 19 | 1504 | 298.9605 | 84.3435 | api or runner error | 6021 | 34.52 |
| comparison-v2 (continued) | 19 | 1588 | 315.1637 | 88.7057 | Terrain completed | 6354 | 36.80 |
| comparison-v2 (interrupted) | 19 | 1075 | 215.9069 | 62.2428 | api or runner error | 4303 | 24.45 |

The native finish is x > 88.6666667, with environment termination and no torso fall. Each action lasts one 50-Hz physics frame. Videos show simulation speed and omit API waiting; these results do not demonstrate real-time control. Every recorded episode, including the failed arithmetic-composition trial, has a complete video and full API/action log.

Seed 19 was interrupted by a transport read timeout after 1075 frames, without a fall or environment termination. Its continuations restore the exact recorded model-response prefix and verify every replayed request payload before making new live requests. The controller, seed, physics, and all prior actions remain unchanged. A separate response-origin log distinguishes cached historical responses from new API outputs; bounded retries apply only to transport failures. The interrupted prefixes are not independent rollouts. Each continued row's API calls and wall time sum its linked recorded sessions (excluding the between-session debugging gaps); no combined mean inference latency is reported.

The first continuation then stopped at frame 1504, x=84.3435, because the endpoint returned HTTP 402. It had not fallen, but that segment had not reached the finish, so its own archived record remains **not completed**. This payment/credit-related response was not retried automatically. After the user restored API access, a second linked continuation resumed the exact saved trajectory; its measured outcome is listed separately above.

## What changed

The original controller asked Jev to evaluate an entire four-term motor equation. Splitting the calculation into separately decoded signed terms substantially reduced error, but live `composed-v1` still fell. Its gait comparisons were correct; multiplication and subtraction sometimes produced tenfold errors. Examples include `-0.1375 * 0.323208` read as approximately -0.445 instead of -0.04444. Diagnostic exact arithmetic is evaluated after inference and never used to replace live actions.

`comparison-v2` keeps the same disclosed feedback rule and gait, but compiles each fixed affine rule into a table of input intervals. For a signed term y = a(x − b), a candidate term interval determines an equivalent interval for the observed x. Only a, b, and candidate boundaries enter the threshold calculation. The current observed value is printed in the question; Python never evaluates its correct term, selects its interval, or supplies an exact motor command. Jev chooses the interval.

This is an explicitly **rule-guided comparison-table controller**. The walking rule is supplied by the experimenter; these experiments do not show that Jev independently discovered a locomotion policy. The final motor is a sum of model-selected term values, distinct from the earlier direct whole-motor decoder.

1. Jev answers four independent yes/no comparisons: support hip < 0.10, moving foot contact == 1, support knee > 0.88, forward scaled velocity > 0.348.
2. Disclosed chained Boolean logic combines those model answers into a gait phase. Fixed phase templates set angle goals; no code compares the raw observations for gait selection.
3. Three K=20 refinements locate each displayed raw number in input intervals. Each selected leaf maps to a signed term center on a 0.005 grid over [-16,16]. This is at most 6401 centers, not 6401 choices in a single request.
4. The adapter sums the **model-selected integer grid units**, clips the sum to [-200,199], then multiplies by 0.005. The four executed motor commands lie on [-1,0.995]. No per-state correct term or motor target is evaluated by this adapter.

Feedback coefficients are unchanged: hip proportional gain 0.495, knee proportional gain 2.2, joint damping 0.1375, body-angle gain 0.495, body-rotation gain 0.825, and vertical-velocity gain 8.25. Observations are rounded to six decimal places; printed inverse thresholds use twelve. Negative-slope intervals reverse inequalities and endpoint inclusivity. Shared body terms reuse the same model prediction for both relevant motors.

Each frame uses four API requests: one for gait comparisons plus three batched term refinements. There is no image input, terrain lookahead, lidar input, or torso-position input. Those last two fields are retained only in diagnostic logs.

## Matched archived-state diagnostic

Ten archived states yield 40 motor outputs. Angle goals are held fixed from those records; therefore this small comparison evaluates numerical execution, not full gait choice or a held-out control benchmark. Ground truth is computed only after actual model inference.

| Numerical protocol | Motor MAE | Maximum absolute error | Absolute errors > 0.2 |
|---|---:|---:|---:|
| Direct whole-motor arithmetic | 0.159695 | 0.908259 | 11 / 40 |
| Signed arithmetic terms + explicit composition | 0.033456 | 0.398194 | 1 / 40 |
| Input-interval comparisons + explicit composition | 0.001905 | 0.008110 | 0 / 40 |

These errors compare physical motor outputs with the unquantized feedback rule. Centered term quantization itself contributes some error. The comparison-table method changes the task presented to Jev; the improvement must not be described as a prompt-only gain on identical arithmetic questions.

## Independent action and physics audit

An independent script parses recorded questions and selected option keys, validates inverse thresholds against fixed rules, reconstructs term readouts and integer composition, checks model-predicate gait transitions, and replays every action in a fresh simulator. Source snapshots and summaries are checked. The script does not import the production decoder or call an API.

| Protocol | Seed | Audited frames | Correct gait comparisons | Motor MAE vs quantized reference at the same model gait | Maximum motor error | Maximum replay reward error |
|---|---:|---:|---:|---:|---:|---:|
| comparison-v2 (interrupted) | 19 | 1075 | 4300/4300 | 0.000479 | 0.045000 | 0.0e+00 |
| comparison-v2 (continued) | 19 | 1504 | 6016/6016 | 0.000760 | 0.410000 | 0.0e+00 |
| comparison-v2 (continued) | 19 | 1588 | 6352/6352 | 0.000733 | 0.410000 | 0.0e+00 |
| comparison-v2 | 7 | 979 | 3916/3916 | 0.000414 | 0.045000 | 0.0e+00 |
| composed-v1 | 7 | 164 | 656/656 | 0.041250 | 0.785000 | 0.0e+00 |

Reference motor errors above are post-hoc diagnostics using the same model-chosen gait; they are not an alternative executed controller. Exact agreement of physical replay validates recording provenance, not optimality of the chosen actions.

Offline sensitivity tests also found that a persistent extra -0.005 motor bias can stall the reference rule even when small random perturbations are tolerated. Consequently, new term readouts use interval centers and exact integer summation instead of separately flooring every signed term. Offline reference-controller completions are never counted as Jev game results.

Seed 7 exposes a remaining controller-robustness limit: a prolonged SWING phase loses forward momentum without entering LOWER. Exact-reference continuations from multiple recorded prefixes after frame 780 still fall, so merely correcting later numerical answers does not rescue that trajectory. A tighter offline counterfactual found that an exact continuation after the first 757 recorded actions completes, while including recorded decision 757 and then continuing with the same exact controller falls. That one additional action differs from the centered reference by -0.005 in one knee command. These are deterministic counterfactual diagnostics, not additional Jev completions. Bounded timeout and support-hip recovery variants were tested offline and did not provide a validated rescue; none was inserted into the live controller. Diagnostic configurations and outcomes are retained in the supplemental archive.

Public evidence: [complete audits](walker-redesign-audit.json), [independent audit source](walker-redesign-audit.py), [archived numerical probes](walker-redesign-diagnostics.tar.gz). Each row of the website's Walker ledger links its full recorded trace and media. Source snapshots retain original local import paths; they are audit evidence rather than a portable benchmark package.
