# Jev historical S&P 500 recall

Ground truth: https://fred.stlouisfed.org/data/SP500
Model: typesafe/jev-1.13-20260917
Three dates x two option orders x two repeats. 72 API requests; no training or supplied quotes.
Fixed range [0,10000), six ten-way levels. Direct control uses 100 bins of width 100, so compare it with hierarchy depth 2, not cent precision.
Last intervals represent numeric resolution, NOT confidence intervals. Lower endpoints are used for reported absolute errors.

{"evaluations": 12, "direct_100_correct": 0, "hierarchy_100_correct": 0, "hierarchy_cent_correct": 0, "reported_cost": 0.003890376}

| Date | Reverse | Repeat | Truth | Direct interval | Hierarchy final interval | Error |
|---|---|---|---:|---|---|---:|
| 2019-12-31 | False | 0 | 3230.78 | [3300.0, 3400.0] | [3331.1, 3331.11] | 100.32 |
| 2019-12-31 | False | 1 | 3230.78 | [3900.0, 4000.0] | [3391.1, 3391.11] | 160.32 |
| 2019-12-31 | True | 0 | 3230.78 | [3900.0, 4000.0] | [3389.99, 3390.0] | 159.21 |
| 2019-12-31 | True | 1 | 3230.78 | [3900.0, 4000.0] | [3389.99, 3390.0] | 159.21 |
| 2020-12-31 | False | 0 | 3756.07 | [4000.0, 4100.0] | [3899.99, 3900.0] | 143.92 |
| 2020-12-31 | False | 1 | 3756.07 | [4000.0, 4100.0] | [3891.0, 3891.01] | 134.93 |
| 2020-12-31 | True | 0 | 3756.07 | [4000.0, 4100.0] | [3999.99, 4000.0] | 243.92 |
| 2020-12-31 | True | 1 | 3756.07 | [4000.0, 4100.0] | [3899.99, 3900.0] | 143.92 |
| 2023-12-29 | False | 0 | 4769.83 | [4900.0, 5000.0] | [4999.99, 5000.0] | 230.16 |
| 2023-12-29 | False | 1 | 4769.83 | [4900.0, 5000.0] | [4999.99, 5000.0] | 230.16 |
| 2023-12-29 | True | 0 | 4769.83 | [4900.0, 5000.0] | [4999.99, 5000.0] | 230.16 |
| 2023-12-29 | True | 1 | 4769.83 | [4900.0, 5000.0] | [4999.99, 5000.0] | 230.16 |
