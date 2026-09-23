# Publication plan

Publish to Bring-AI/jev-numeric, retaining its existing visibility.

- Export the five completed experiment suites, exact requests, responses and metrics.
- Build a small portable Jev client and numeric interval decoder; multiway splitting is the default,
  branching=10 matches the historical-stock experiment. Use integer grid indices and
  Decimal bounds to avoid floating-point boundary errors. Test with an independent oracle.
- Expose experimental threshold-to-histogram conversion with raw monotonicity diagnostics;
  do not claim calibrated uncertainty.
- Make historical reproduction scripts portable; credentials only through environment or
  user-provided files. Do not bundle local credentials, training data or checkpoints.
- Create an original SVG teaser that explains the decision tree, finite resolution, and
  the three-date evidence. Provide English and Chinese README files.
- Verify offline artifact integrity, recomputed headline results, software tests, links,
  asset rendering and credential exclusion. Commit and push after checks.

Claims: 4.58% mean absolute percentage error is from the ten-way historical recall run,
not an all-sample 5% bound. The oracle-input control supplies the correct value in context;
zero error describes 12 runs on three unique values, not forecasting. Native Jev already
returns numeric scores and categorical probabilities. The contribution is a numeric
interface built on those decisions, not a new model or a claim to invent interval refinement.
