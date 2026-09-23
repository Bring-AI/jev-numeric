# Interval and digit Choice: integration smoke check

Both methods use the same Jev Choice transport. No token logits, numerical head, training, retrieval, or supplied answer was used. Expected answers are recorded separately for scoring and never sent in requests.

Three reused questions, two methods, two option orders, one rollout per condition: 12 predictions and 48 Choice calls per prompt version. Every prediction uses four dependent decisions. This is a small development check, not held-out evaluation or evidence of general accuracy.

The first prompt used ordinal character positions. After seeing large positional errors, we made one revision: name the tens/units/fractional position in both the instructions and option descriptions, and clarify that the previous prefix is a prediction rather than a new numerical input. The revised prompt is the one shipped in `decode_digits`. Both runs, including all failures, are retained. Interval instructions were unchanged between versions.

Resolution: `[0,100)` / `0.01` for the first two questions, `[0,1)` / `0.0001` for the fraction. Models in the raw records identify the exact served version. Results below use absolute relative error, `100 × |prediction − target| / |target|`.

## Initial ordinal-position prompt

| Question | Target | Method | Forward / reverse output | Relative error, forward / reverse |
|---|---:|---|---|---|
| 1 + 1 | 2.00 | interval | 2.00 / 2.00 | 0.0000% / 0.0000% |
| 1 + 1 | 2.00 | digits | 0.00 / 20.00 | 100.0000% / 900.0000% |
| Stock: $10.50 + $1.25 | 11.75 | interval | 11.75 / 11.75 | 0.0000% / 0.0000% |
| Stock: $10.50 + $1.25 | 11.75 | digits | 17.55 / 77.05 | 49.3617% / 555.7447% |
| 7 / 8 − 1 / 16 | 0.8125 | interval | 0.7800 / 0.7000 | 4.0000% / 13.8462% |
| 7 / 8 − 1 / 16 | 0.8125 | digits | 0.7300 / 0.7300 | 10.1538% / 10.1538% |

[All requests, responses, and traces](../digit-decoding-20260924/summary.json).

## Current place-specific prompt

| Question | Target | Method | Forward / reverse output | Relative error, forward / reverse |
|---|---:|---|---|---|
| 1 + 1 | 2.00 | interval | 2.00 / 2.00 | 0.0000% / 0.0000% |
| 1 + 1 | 2.00 | digits | 2.00 / 2.00 | 0.0000% / 0.0000% |
| Stock: $10.50 + $1.25 | 11.75 | interval | 11.75 / 11.75 | 0.0000% / 0.0000% |
| Stock: $10.50 + $1.25 | 11.75 | digits | 11.77 / 11.77 | 0.1702% / 0.1702% |
| 7 / 8 − 1 / 16 | 0.8125 | interval | 0.7800 / 0.7800 | 4.0000% / 4.0000% |
| 7 / 8 − 1 / 16 | 0.8125 | digits | 0.7670 / 0.7770 | 5.6000% / 4.3692% |

[All requests, responses, and traces](../digit-decoding-place-prompt-20260924/summary.json).

## Interpretation

The current prompt makes the digit interface usable without logits, but it still misestimates the stock example and the fractional expression. Prefix formatting alone does not guarantee numerical reasoning. Do not use this smoke check to claim digit decoding is better than interval decoding or equivalent to native language-model token generation. The README keeps interval decoding as the default.
