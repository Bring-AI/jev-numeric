# Jev binary arithmetic smoke test

{"n": 12, "direct_correct": 10, "binary_correct": 3, "correct_bits": 36, "total_bits": 48, "reported_cost": 0.000550368, "unpriced_requests": 0}

One run, 12 hand-picked exact cases, English prompts. No training or OOD claim.
Four independent bit questions, not a conditional joint distribution. Direct control has 16 options.
Raw API probabilities retained; marginal means normalize rounding error.

| Expression | Target | Truth bits | Predicted bits | Binary value | Direct choice |
|---|---:|---|---|---:|---:|
| 1 + 1 | 2.0 | 0010 | 0000 | 0.0 | 2.0 |
| 2 + 3 | 5.0 | 0101 | 0110 | 6.0 | 5.0 |
| 7 - 4 | 3.0 | 0011 | 0000 | 0.0 | 3.0 |
| 3 * 4 | 12.0 | 1100 | 0110 | 6.0 | 12.0 |
| 12 / 3 | 4.0 | 0100 | 0110 | 6.0 | 4.0 |
| 7 + 8 | 15.0 | 1111 | 1111 | 15.0 | 15.0 |
| 1 / 2 | 0.5 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 4 + 1 / 8 | 0.375 | 0110 | 0110 | 0.375 | 0.375 |
| 3 / 4 - 1 / 4 | 0.5 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 8 + 5 / 16 | 0.6875 | 1011 | 0011 | 0.1875 | 0.4375 |
| (1 / 2) * (1 / 2) | 0.25 | 0100 | 0000 | 0.0 | 0.25 |
| 7 / 8 - 1 / 16 | 0.8125 | 1101 | 1111 | 0.9375 | 0.6875 |
