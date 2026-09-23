# Jev historical S&P 500 recall

Ground truth: https://fred.stlouisfed.org/data/SP500
Model: typesafe/jev-1.13-20260917
Three dates x two option orders x two repeats. 72 API requests; no training.
Verified close supplied in state; all question text unchanged.
Fixed range [0,10000), six ten-way levels. Direct control uses 100 bins of width 100, so compare it with hierarchy depth 2, not cent precision.
Last intervals represent numeric resolution, NOT confidence intervals. Lower endpoints are used for reported absolute errors.

{"evaluations": 12, "direct_100_correct": 12, "hierarchy_100_correct": 12, "hierarchy_cent_correct": 12, "reported_cost": 0.003941784}

| Date | Reverse | Repeat | Truth | Direct interval | Hierarchy final interval | Error |
|---|---|---|---:|---|---|---:|
| 2019-12-31 | False | 0 | 3230.78 | [3200.0, 3300.0] | [3230.78, 3230.79] | 0.0 |
| 2019-12-31 | False | 1 | 3230.78 | [3200.0, 3300.0] | [3230.78, 3230.79] | 0.0 |
| 2019-12-31 | True | 0 | 3230.78 | [3200.0, 3300.0] | [3230.78, 3230.79] | 0.0 |
| 2019-12-31 | True | 1 | 3230.78 | [3200.0, 3300.0] | [3230.78, 3230.79] | 0.0 |
| 2020-12-31 | False | 0 | 3756.07 | [3700.0, 3800.0] | [3756.07, 3756.08] | 0.0 |
| 2020-12-31 | False | 1 | 3756.07 | [3700.0, 3800.0] | [3756.07, 3756.08] | 0.0 |
| 2020-12-31 | True | 0 | 3756.07 | [3700.0, 3800.0] | [3756.07, 3756.08] | 0.0 |
| 2020-12-31 | True | 1 | 3756.07 | [3700.0, 3800.0] | [3756.07, 3756.08] | 0.0 |
| 2023-12-29 | False | 0 | 4769.83 | [4700.0, 4800.0] | [4769.83, 4769.84] | 0.0 |
| 2023-12-29 | False | 1 | 4769.83 | [4700.0, 4800.0] | [4769.83, 4769.84] | 0.0 |
| 2023-12-29 | True | 0 | 4769.83 | [4700.0, 4800.0] | [4769.83, 4769.84] | 0.0 |
| 2023-12-29 | True | 1 | 4769.83 | [4700.0, 4800.0] | [4769.83, 4769.84] | 0.0 |
