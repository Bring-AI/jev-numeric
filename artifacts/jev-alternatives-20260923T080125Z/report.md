# Jev numeric interface comparison

Model: typesafe/jev-1.13-20260917
12 fixed cases x 2 option orders x 2 repeats; 48 evaluations per method. 192 batched API calls.
No training, no new held-out questions, no OOD or probability-calibration claim. Choice-map order reversed with labels/descriptions together.
CDF mode uses PAVA; ties select smallest candidate. Decimal predictions are not snapped onto the candidate grid.
Methods share calls for efficiency; rounds below are logical sequential depth, not isolated latency measurements.

| Method | Correct /48 | Forward /24 | Reverse /24 | Integers /24 | Fractions /24 | Sequential rounds |
|---|---:|---:|---:|---:|---:|---|
| direct | 40 | 20 | 20 | 24 | 16 | 1 |
| explicit_bits | 28 | 14 | 14 | 16 | 12 | 1 |
| explicit_groups | 38 | 19 | 19 | 24 | 14 | 1 |
| adaptive_bisection | 28 | 14 | 14 | 24 | 4 | 4 |
| parallel_thresholds | 28 | 14 | 14 | 24 | 4 | 1 |
| decimal_digits | 32 | 16 | 16 | 24 | 8 | 2 integer / 4 fraction |
| interval_selection | 39 | 20 | 19 | 24 | 15 | 2 |

## Diagnostics

```json
{
  "direct": {
    "correct": 40,
    "total": 48,
    "forward_correct": 20,
    "reverse_correct": 20,
    "integer_correct": 24,
    "fraction_correct": 16
  },
  "explicit_bits": {
    "correct": 28,
    "total": 48,
    "forward_correct": 14,
    "reverse_correct": 14,
    "integer_correct": 16,
    "fraction_correct": 12
  },
  "explicit_groups": {
    "correct": 38,
    "total": 48,
    "forward_correct": 19,
    "reverse_correct": 19,
    "integer_correct": 24,
    "fraction_correct": 14
  },
  "adaptive_bisection": {
    "correct": 28,
    "total": 48,
    "forward_correct": 14,
    "reverse_correct": 14,
    "integer_correct": 24,
    "fraction_correct": 4
  },
  "parallel_thresholds": {
    "correct": 28,
    "total": 48,
    "forward_correct": 14,
    "reverse_correct": 14,
    "integer_correct": 24,
    "fraction_correct": 4
  },
  "decimal_digits": {
    "correct": 32,
    "total": 48,
    "forward_correct": 16,
    "reverse_correct": 16,
    "integer_correct": 24,
    "fraction_correct": 8
  },
  "interval_selection": {
    "correct": 39,
    "total": 48,
    "forward_correct": 20,
    "reverse_correct": 19,
    "integer_correct": 24,
    "fraction_correct": 15
  },
  "cdf_diagnostics": {
    "runs_with_violations": 25,
    "total_adjacent_violations": 54,
    "max_downward_step": 0.5599999999999999,
    "median_correct": 28
  },
  "cost": 0.011527908,
  "unpriced_calls": 0
}
```

## Predictions

| Expression | Order | Repeat | Target | direct | explicit_bits | explicit_groups | adaptive_bisection | parallel_thresholds | decimal_digits | interval_selection |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 + 1 | False | 0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| 1 + 1 | False | 1 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| 1 + 1 | True | 0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| 1 + 1 | True | 1 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| 2 + 3 | False | 0 | 5.0 | 5.0 | 7.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| 2 + 3 | False | 1 | 5.0 | 5.0 | 7.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| 2 + 3 | True | 0 | 5.0 | 5.0 | 7.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| 2 + 3 | True | 1 | 5.0 | 5.0 | 7.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| 7 - 4 | False | 0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 |
| 7 - 4 | False | 1 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 |
| 7 - 4 | True | 0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 |
| 7 - 4 | True | 1 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 |
| 3 * 4 | False | 0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 |
| 3 * 4 | False | 1 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 |
| 3 * 4 | True | 0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 |
| 3 * 4 | True | 1 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 | 12.0 |
| 12 / 3 | False | 0 | 4.0 | 4.0 | 0.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| 12 / 3 | False | 1 | 4.0 | 4.0 | 0.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| 12 / 3 | True | 0 | 4.0 | 4.0 | 0.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| 12 / 3 | True | 1 | 4.0 | 4.0 | 0.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| 7 + 8 | False | 0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 |
| 7 + 8 | False | 1 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 |
| 7 + 8 | True | 0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 |
| 7 + 8 | True | 1 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 | 15.0 |
| 1 / 2 | False | 0 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| 1 / 2 | False | 1 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| 1 / 2 | True | 0 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| 1 / 2 | True | 1 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 |
| 1 / 4 + 1 / 8 | False | 0 | 0.375 | 0.375 | 0.375 | 0.375 | 0.3125 | 0.3125 | 0.35 | 0.375 |
| 1 / 4 + 1 / 8 | False | 1 | 0.375 | 0.375 | 0.375 | 0.375 | 0.3125 | 0.3125 | 0.35 | 0.375 |
| 1 / 4 + 1 / 8 | True | 0 | 0.375 | 0.375 | 0.375 | 0.375 | 0.3125 | 0.3125 | 0.35 | 0.375 |
| 1 / 4 + 1 / 8 | True | 1 | 0.375 | 0.375 | 0.375 | 0.375 | 0.3125 | 0.3125 | 0.35 | 0.375 |
| 3 / 4 - 1 / 4 | False | 0 | 0.5 | 0.5 | 0.0 | 0.0 | 0.375 | 0.375 | 0.5 | 0.5 |
| 3 / 4 - 1 / 4 | False | 1 | 0.5 | 0.5 | 0.0 | 0.5 | 0.375 | 0.375 | 0.5 | 0.5 |
| 3 / 4 - 1 / 4 | True | 0 | 0.5 | 0.5 | 0.0 | 0.0 | 0.3125 | 0.3125 | 0.5 | 0.4375 |
| 3 / 4 - 1 / 4 | True | 1 | 0.5 | 0.5 | 0.0 | 0.5 | 0.3125 | 0.3125 | 0.5 | 0.5 |
| 3 / 8 + 5 / 16 | False | 0 | 0.6875 | 0.4375 | 0.4375 | 0.9375 | 0.4375 | 0.5625 | 0.017 | 0.5625 |
| 3 / 8 + 5 / 16 | False | 1 | 0.6875 | 0.4375 | 0.4375 | 0.9375 | 0.4375 | 0.4375 | 0.01 | 0.5625 |
| 3 / 8 + 5 / 16 | True | 0 | 0.6875 | 0.625 | 0.4375 | 0.9375 | 0.4375 | 0.4375 | 0.01 | 0.5625 |
| 3 / 8 + 5 / 16 | True | 1 | 0.6875 | 0.5625 | 0.4375 | 0.9375 | 0.4375 | 0.4375 | 0.01 | 0.5625 |
| (1 / 2) * (1 / 2) | False | 0 | 0.25 | 0.25 | 0.25 | 0.25 | 0.1875 | 0.1875 | 0.055 | 0.25 |
| (1 / 2) * (1 / 2) | False | 1 | 0.25 | 0.25 | 0.25 | 0.25 | 0.1875 | 0.1875 | 0.055 | 0.25 |
| (1 / 2) * (1 / 2) | True | 0 | 0.25 | 0.25 | 0.25 | 0.25 | 0.1875 | 0.1875 | 0.055 | 0.25 |
| (1 / 2) * (1 / 2) | True | 1 | 0.25 | 0.25 | 0.25 | 0.25 | 0.1875 | 0.1875 | 0.055 | 0.25 |
| 7 / 8 - 1 / 16 | False | 0 | 0.8125 | 0.6875 | 0.5625 | 0.6875 | 0.5625 | 0.5625 | 0.76 | 0.75 |
| 7 / 8 - 1 / 16 | False | 1 | 0.8125 | 0.6875 | 0.5625 | 0.6875 | 0.5625 | 0.5625 | 0.765 | 0.75 |
| 7 / 8 - 1 / 16 | True | 0 | 0.8125 | 0.6875 | 0.5625 | 0.6875 | 0.4375 | 0.5625 | 0.745 | 0.75 |
| 7 / 8 - 1 / 16 | True | 1 | 0.8125 | 0.6875 | 0.6875 | 0.6875 | 0.4375 | 0.5625 | 0.745 | 0.75 |
