# Jev binary prompt and order controls

Model: typesafe/jev-1.13-20260917
12 fixed cases; two repeats per cell, randomly interleaved. No training.
Option keys and descriptions kept together when reversing serialized criterion order.
API internal ordering/caching is unknown; repeats are not independent new problems.

| Prompt | Order | Direct correct /24 | Binary correct /24 | Bits correct /96 |
|---|---|---:|---:|---:|
| original | forward | 20 | 6 | 74 |
| original | reverse | 20 | 7 | 75 |
| explicit | forward | 20 | 15 | 83 |
| explicit | reverse | 20 | 14 | 82 |

## Stability

```json
{
  "original_forward": {
    "n": 24,
    "direct_correct": 20,
    "binary_correct": 6,
    "correct_bits": 74
  },
  "original_reverse": {
    "n": 24,
    "direct_correct": 20,
    "binary_correct": 7,
    "correct_bits": 75
  },
  "explicit_forward": {
    "n": 24,
    "direct_correct": 20,
    "binary_correct": 15,
    "correct_bits": 83
  },
  "explicit_reverse": {
    "n": 24,
    "direct_correct": 20,
    "binary_correct": 14,
    "correct_bits": 82
  },
  "original_stability": {
    "order_bit_flips_of_96": 3,
    "mean_order_p1_delta": 0.018229166666666664,
    "repeat_bit_flips_of_96": 3
  },
  "explicit_stability": {
    "order_bit_flips_of_96": 1,
    "mean_order_p1_delta": 0.0165625,
    "repeat_bit_flips_of_96": 1
  },
  "reported_cost": 0.005360544,
  "unpriced_requests": 0
}
```

## Individual results

| Expression | Prompt | Reversed | Repeat | Truth | Bits | Binary value | Direct |
|---|---|---|---|---|---|---:|---:|
| 1 + 1 | explicit | False | 0 | 0010 | 0010 | 2.0 | 2.0 |
| 1 + 1 | explicit | False | 1 | 0010 | 0010 | 2.0 | 2.0 |
| 1 + 1 | explicit | True | 0 | 0010 | 0010 | 2.0 | 2.0 |
| 1 + 1 | explicit | True | 1 | 0010 | 0010 | 2.0 | 2.0 |
| 1 + 1 | original | False | 0 | 0010 | 0000 | 0.0 | 2.0 |
| 1 + 1 | original | False | 1 | 0010 | 0000 | 0.0 | 2.0 |
| 1 + 1 | original | True | 0 | 0010 | 0000 | 0.0 | 2.0 |
| 1 + 1 | original | True | 1 | 0010 | 0000 | 0.0 | 2.0 |
| 2 + 3 | explicit | False | 0 | 0101 | 0111 | 7.0 | 5.0 |
| 2 + 3 | explicit | False | 1 | 0101 | 0111 | 7.0 | 5.0 |
| 2 + 3 | explicit | True | 0 | 0101 | 0111 | 7.0 | 5.0 |
| 2 + 3 | explicit | True | 1 | 0101 | 0111 | 7.0 | 5.0 |
| 2 + 3 | original | False | 0 | 0101 | 0110 | 6.0 | 5.0 |
| 2 + 3 | original | False | 1 | 0101 | 0110 | 6.0 | 5.0 |
| 2 + 3 | original | True | 0 | 0101 | 0110 | 6.0 | 5.0 |
| 2 + 3 | original | True | 1 | 0101 | 0110 | 6.0 | 5.0 |
| 7 - 4 | explicit | False | 0 | 0011 | 0011 | 3.0 | 3.0 |
| 7 - 4 | explicit | False | 1 | 0011 | 0011 | 3.0 | 3.0 |
| 7 - 4 | explicit | True | 0 | 0011 | 0011 | 3.0 | 3.0 |
| 7 - 4 | explicit | True | 1 | 0011 | 0011 | 3.0 | 3.0 |
| 7 - 4 | original | False | 0 | 0011 | 0010 | 2.0 | 3.0 |
| 7 - 4 | original | False | 1 | 0011 | 0000 | 0.0 | 3.0 |
| 7 - 4 | original | True | 0 | 0011 | 0010 | 2.0 | 3.0 |
| 7 - 4 | original | True | 1 | 0011 | 0010 | 2.0 | 3.0 |
| 3 * 4 | explicit | False | 0 | 1100 | 1100 | 12.0 | 12.0 |
| 3 * 4 | explicit | False | 1 | 1100 | 1100 | 12.0 | 12.0 |
| 3 * 4 | explicit | True | 0 | 1100 | 1100 | 12.0 | 12.0 |
| 3 * 4 | explicit | True | 1 | 1100 | 1100 | 12.0 | 12.0 |
| 3 * 4 | original | False | 0 | 1100 | 0110 | 6.0 | 12.0 |
| 3 * 4 | original | False | 1 | 1100 | 1110 | 14.0 | 12.0 |
| 3 * 4 | original | True | 0 | 1100 | 0110 | 6.0 | 12.0 |
| 3 * 4 | original | True | 1 | 1100 | 0110 | 6.0 | 12.0 |
| 12 / 3 | explicit | False | 0 | 0100 | 0100 | 4.0 | 4.0 |
| 12 / 3 | explicit | False | 1 | 0100 | 0000 | 0.0 | 4.0 |
| 12 / 3 | explicit | True | 0 | 0100 | 0000 | 0.0 | 4.0 |
| 12 / 3 | explicit | True | 1 | 0100 | 0000 | 0.0 | 4.0 |
| 12 / 3 | original | False | 0 | 0100 | 0110 | 6.0 | 4.0 |
| 12 / 3 | original | False | 1 | 0100 | 0110 | 6.0 | 4.0 |
| 12 / 3 | original | True | 0 | 0100 | 0110 | 6.0 | 4.0 |
| 12 / 3 | original | True | 1 | 0100 | 0110 | 6.0 | 4.0 |
| 7 + 8 | explicit | False | 0 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | explicit | False | 1 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | explicit | True | 0 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | explicit | True | 1 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | original | False | 0 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | original | False | 1 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | original | True | 0 | 1111 | 1111 | 15.0 | 15.0 |
| 7 + 8 | original | True | 1 | 1111 | 1111 | 15.0 | 15.0 |
| 1 / 2 | explicit | False | 0 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | explicit | False | 1 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | explicit | True | 0 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | explicit | True | 1 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | original | False | 0 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | original | False | 1 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | original | True | 0 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 2 | original | True | 1 | 1000 | 1000 | 0.5 | 0.5 |
| 1 / 4 + 1 / 8 | explicit | False | 0 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | explicit | False | 1 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | explicit | True | 0 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | explicit | True | 1 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | original | False | 0 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | original | False | 1 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | original | True | 0 | 0110 | 0110 | 0.375 | 0.375 |
| 1 / 4 + 1 / 8 | original | True | 1 | 0110 | 0110 | 0.375 | 0.375 |
| 3 / 4 - 1 / 4 | explicit | False | 0 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | explicit | False | 1 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | explicit | True | 0 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | explicit | True | 1 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | original | False | 0 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | original | False | 1 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | original | True | 0 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 4 - 1 / 4 | original | True | 1 | 1000 | 0000 | 0.0 | 0.5 |
| 3 / 8 + 5 / 16 | explicit | False | 0 | 1011 | 0111 | 0.4375 | 0.4375 |
| 3 / 8 + 5 / 16 | explicit | False | 1 | 1011 | 0111 | 0.4375 | 0.4375 |
| 3 / 8 + 5 / 16 | explicit | True | 0 | 1011 | 0111 | 0.4375 | 0.5625 |
| 3 / 8 + 5 / 16 | explicit | True | 1 | 1011 | 0111 | 0.4375 | 0.625 |
| 3 / 8 + 5 / 16 | original | False | 0 | 1011 | 0011 | 0.1875 | 0.4375 |
| 3 / 8 + 5 / 16 | original | False | 1 | 1011 | 0011 | 0.1875 | 0.4375 |
| 3 / 8 + 5 / 16 | original | True | 0 | 1011 | 0011 | 0.1875 | 0.5625 |
| 3 / 8 + 5 / 16 | original | True | 1 | 1011 | 0011 | 0.1875 | 0.5625 |
| (1 / 2) * (1 / 2) | explicit | False | 0 | 0100 | 0100 | 0.25 | 0.25 |
| (1 / 2) * (1 / 2) | explicit | False | 1 | 0100 | 0100 | 0.25 | 0.25 |
| (1 / 2) * (1 / 2) | explicit | True | 0 | 0100 | 0100 | 0.25 | 0.25 |
| (1 / 2) * (1 / 2) | explicit | True | 1 | 0100 | 0100 | 0.25 | 0.25 |
| (1 / 2) * (1 / 2) | original | False | 0 | 0100 | 0000 | 0.0 | 0.25 |
| (1 / 2) * (1 / 2) | original | False | 1 | 0100 | 0000 | 0.0 | 0.25 |
| (1 / 2) * (1 / 2) | original | True | 0 | 0100 | 0000 | 0.0 | 0.25 |
| (1 / 2) * (1 / 2) | original | True | 1 | 0100 | 0100 | 0.25 | 0.25 |
| 7 / 8 - 1 / 16 | explicit | False | 0 | 1101 | 1011 | 0.6875 | 0.6875 |
| 7 / 8 - 1 / 16 | explicit | False | 1 | 1101 | 1011 | 0.6875 | 0.6875 |
| 7 / 8 - 1 / 16 | explicit | True | 0 | 1101 | 1011 | 0.6875 | 0.6875 |
| 7 / 8 - 1 / 16 | explicit | True | 1 | 1101 | 1011 | 0.6875 | 0.6875 |
| 7 / 8 - 1 / 16 | original | False | 0 | 1101 | 1111 | 0.9375 | 0.6875 |
| 7 / 8 - 1 / 16 | original | False | 1 | 1101 | 1111 | 0.9375 | 0.6875 |
| 7 / 8 - 1 / 16 | original | True | 0 | 1101 | 1111 | 0.9375 | 0.6875 |
| 7 / 8 - 1 / 16 | original | True | 1 | 1101 | 1111 | 0.9375 | 0.6875 |
