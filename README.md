<p align="center">
  <img src="assets/hero.svg" alt="Jev Numeric: decisions become numerical outputs through a multiway interval tree" width="100%">
</p>

<h1 align="center">Jev Numeric</h1>
<p align="center"><strong>A simple algorithm that turns Jev decisions into numerical outputs.</strong></p>
<p align="center">Exploring numerical output with Jev through discrete choices and hierarchical interval decoding.</p>
<p align="center">
  <a href="README.zh-CN.md">中文</a> ·
  <a href="#the-algorithm">How it works</a> ·
  <a href="#results">Results</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="artifacts/metrics.json">Recorded metrics</a>
</p>

**Jev is built for structured decisions. We use those decisions to construct a numerical output interface.** Ask which interval contains a value, keep the selected interval, and repeat. A multiway decision tree turns categorical choices into a finite-precision number—without training a model or adding a regression head.

| Capability | Native Jev primitives | This project |
|---|---|---|
| Decisions and probabilities over named options | **Yes** | Used as the building block |
| Numeric scores on a specified rubric | **Yes** | Already supported by Jev |
| A general numerical readout with caller-selected bounds and precision | No dedicated primitive in the documented API | **Multiway interval decoding** |
| A distribution over a numerical grid | Requires defining numeric options or another mapping | **Experimental threshold-to-histogram interface** |
| Guaranteed accuracy or calibrated uncertainty | No such guarantee established here | **Not established** |

Jev already returns numeric scores and categorical probability distributions. Our contribution is the **mapping from decisions to a numerical domain**, not the claim that Jev never returns numbers. See the official [Choice](https://docs.typesafe.ai/primitives/choice) and [Score](https://docs.typesafe.ai/primitives/score) documentation.

## The algorithm

**Split → choose → zoom in.** Given bounds `[L, U)`, resolution `ε`, and branching factor `K`:

1. Divide the current interval into up to `K` non-overlapping subintervals.
2. Ask one Jev **Choice** question: which subinterval contains the target value?
3. Follow the selected branch and repeat until one grid cell remains.
4. Return the cell and its lower endpoint as the numerical readout.

For a supplied value of **3230.78**, the recorded ten-way path is:

```text
[0, 10000)
    └── [3000, 4000)
            └── [3200, 3300)
                    └── [3230, 3240)
                            └── [3230, 3231)
                                    └── [3230.7, 3230.8)
                                            └── [3230.78, 3230.79)
```

**Six decisions distinguish one million possible grid values.** For `N = (U−L)/ε` cells, the tree needs at most `ceil(log_K N)` sequential decisions. That is a representational capacity statement: correct decoding still depends on correct branch choices. The implementation uses integer grid indices and decimal bounds, including uneven splits.

The caller must supply a containing range and a stopping precision. An early wrong branch cannot be recovered by this greedy implementation. The final cell is a **resolution interval, not a confidence interval**.

## Results

All primary experiments below used `typesafe/jev-1.13-20260917` through OpenRouter. No fine-tuning, no GPU inference, and no retrieval tool was supplied to Jev. These are small exploratory evaluations; repetitions are not additional unique problems.

### Historical index recall: 4.58% mean relative error

We asked for the S&P 500 **price index's official close on the last trading day** of 2019, 2020, and 2023. Jev received the index and date, but not the closing value. Every run started from `[0,10000)` and used ten-way refinement to `0.01` points. Two option orders × two repeats gave four runs per date.

| Date | Verified close | Range of decoded values across four runs | Absolute percentage error |
|---|---:|---:|---:|
| 2019-12-31 | 3230.78 | 3331.10–3391.10 | 3.11%–4.96% |
| 2020-12-31 | 3756.07 | 3891.00–3999.99 | 3.59%–6.49% |
| 2023-12-29 | 4769.83 | 4999.99 in all four runs | 4.83% |

- **Mean absolute percentage error: 4.58%.** Eleven of twelve runs were within 5%; the maximum error was 6.49%.
- All twelve decoded values were too high. Fine decimal output did not imply fine accuracy.
- At 100-point resolution, both direct 100-bin selection and hierarchical selection missed the correct bin in all twelve runs.

This is **historical factual recall**, not stock forecasting. Ground truth comes from [FRED](https://fred.stlouisfed.org/data/SP500), cross-checked against contemporaneous [2019](https://www.investing.com/news/stock-market-news/futures-dip-as-yearend-rally-cools-off-2050358), [2020](https://www.upi.com/Top_News/US/2020/12/31/Dow-SP-500-hit-record-highs-on-final-day-of-trading-in-2020/8081609454170/), and [2023](https://apnews.com/article/c8fbba7de1750cac49d770c8c7440710) reports. [Raw experiment and report →](artifacts/jev-index-history-20260923T081058Z/report.md)

### Ground-truth oracle input: 0% readout error

Next we changed **one thing**: add the verified close to the input state.

```json
{
  "index": "S&P 500 price index",
  "date": "2019-12-31",
  "observation": "Official closing level on the final trading day of the calendar year",
  "closing_level_index_points": "3230.78"
}
```

Question wording, model, initial bounds, branching factor, and order controls stayed unchanged. Later intervals followed each run's predictions.

| Measurement | Historical recall | Ground-truth oracle input |
|---|---:|---:|
| Direct 100-point bin correct | 0/12 | **12/12** |
| Hierarchical 0.01-point cell correct | 0/12 | **12/12** |
| Mean absolute percentage error | 4.58% | **0%** |
| Correct individual tree decisions | — | **72/72** |

**Jev could read these supplied values and select the right intervals.** This supports separating factual recall from numerical readout. “Oracle input” means the correct answer is deliberately supplied in context; it is a readout control, not a prediction benchmark or evidence of universal numerical reasoning. Only three unique values were tested. [Raw control and report →](artifacts/jev-index-provided-20260923T081655Z/report.md)

### Why not just ask for digits or bits?

We tried that too. Twelve hand-picked arithmetic problems—six integers and six exact binary fractions—were evaluated with two option orders and two repeats: **48 evaluations per method**.

| Method | Integer correct /24 | Fraction correct /24 | Total correct /48 | Sequential rounds |
|---|---:|---:|---:|---:|
| Direct 16-value choice | 24 | 16 | **40** | 1 |
| **Four-way interval decoding** | **24** | **15** | **39** | **2** |
| Explicit candidate-set membership | 24 | 14 | 38 | 1 |
| Decimal digits with previous-digit prefix | 24 | 8 | 32 | 2 / 4 |
| Adaptive threshold search | 24 | 4 | 28 | 4 |
| Parallel thresholds + monotonic repair | 24 | 4 | 28 | 1 |
| Independent binary bits, explicit prompt | 16 | 12 | 28 | 1 |

**Direct selection was slightly better on this tiny fixed grid.** Multiway refinement's attraction is that it can address a finer grid without listing every possible value in a single question. We have not established superior accuracy or latency at scale. Methods shared API calls for efficiency; rounds measure dependency depth, not isolated latency.

What these experiments suggest:

- **Encoding is another task.** Asking which explicit set contains the result scored 38/48; asking for its bit representation scored 28/48. The representations are mathematically related, but the prompts impose different demands.
- **Prompt clarity matters.** In an earlier crossed control, clearer bit instructions improved 6–7/24 to 14–15/24. This change included an explicit computation rule, not just cleaner phrasing.
- **Fractions were harder.** Threshold comparisons and decimal-digit decoding performed much worse on fractions than on integers in this suite.
- **An ordering constraint is not automatic.** Threshold probabilities were nonmonotone in **25/48** runs. For one query, `P(Y ≤ 0.4375)=0.57` but `P(Y ≤ 0.5)=0.01`.

These are failure observations, not proofs that the other methods cannot work. [Full method comparison →](artifacts/jev-alternatives-20260923T080125Z/report.md) · [Prompt/order controls →](artifacts/jev-binary-controls-20260923T075624Z/report.md)

### A note on robustness

We also recorded a follow-up with **two branches and a different prompt** using the reusable decoder: closed-book recall had **31.17% MAPE** across six runs, while the six supplied-value runs were exact. This was not a controlled branching-factor ablation. It shows why the 4.58% result must stay attached to the recorded **ten-way protocol**, rather than being advertised as a general accuracy guarantee. [Follow-up evidence →](artifacts/binary-api-20260923T085013Z/summary.json)

## What about distributions?

A greedy path yields a point readout, **not a full numerical probability distribution**. The experimental `estimate_distribution` function separately asks threshold questions, normalizes each returned yes/no pair, projects the CDF values onto a monotone sequence, and differences adjacent values into histogram masses.

```python
from jev_numeric import JevClient, estimate_distribution

with JevClient() as client:
    histogram = estimate_distribution(
        client,
        state={"value": "0.42"},
        target="the supplied value",
        lower="0", upper="1", bins=16,
    )
print(histogram["masses"])
print(histogram["raw_monotonicity_violations"])
```

The implementation assumes support within `(lower, upper]` and uses right-closed histogram bins. It returns the raw CDF, repaired CDF, masses, and a midpoint approximation of the mean. **Repair enforces a valid shape; it does not establish calibration or accuracy.** The arithmetic threshold results above are the current warning against treating these outputs as validated predictive uncertainty.

## Quick start

Python 3.11+; an existing Jev API credential is required only for live calls.

```bash
git clone https://github.com/Bring-AI/jev-numeric.git
cd jev-numeric
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# Set OPENROUTER_API_KEY in .env, or configure the TypeSafe gateway.
```

```python
from jev_numeric import JevClient, decode_number

with JevClient() as client:
    result = decode_number(
        client,
        state={"closing_level_index_points": "3230.78"},
        target="the supplied closing level in index points",
        lower="0", upper="10000", resolution="0.01",
        branching=10,
    )

print(result["value"])  # Decimal string; preserves precision.
print(result["lower"], result["upper"])
print(result["trace"])  # Every interval choice and its returned probabilities.
```

Or use the CLI:

```bash
jev-numeric \
  --state '{"closing_level_index_points":"3230.78"}' \
  --target 'the supplied closing level in index points' \
  --lower 0 --upper 10000 --resolution 0.01 --branching 10 \
  --output runs/example.json
```

The reusable decoder uses a general prompt. **To reproduce the headline protocols, use the experiment scripts below**, which retain their original specialized prompts. Gateway settings and file-based keys are documented in [.env.example](.env.example); historical scripts pin their model version, whose future availability depends on the provider.

## Reproduce & audit

Offline—no API key or network:

```bash
pytest -q
python scripts/verify_artifacts.py
python scripts/build_artifact_summary.py
```

Live calls—billable; new results go into the ignored `runs/` directory:

```bash
python scripts/probe_jev_binary.py             # original 12-case bit probe
python scripts/probe_jev_binary_controls.py    # prompt × order controls
python scripts/probe_jev_alternatives.py       # seven numeric interfaces
python scripts/probe_jev_index_history.py      # historical recall, ten-way
python scripts/probe_jev_index_history.py --provided-close  # oracle-input control
python scripts/probe_binary_api.py            # separately reported follow-up
```

Every archived API record includes the submitted state, question text, option ordering, response probabilities, and reported model/usage. Headers and credentials are excluded. [Metrics](artifacts/metrics.json) are recomputed from records; [SHA-256 hashes](artifacts/manifest.json) cover the archived evidence. The scripts were ported from a private experiment workspace; original archived requests remain unchanged. See [experiment notes](docs/experiments.md).

## Scope

This repository demonstrates a **regression-style interface over a decision model**. It does not introduce a new trained regressor, establish out-of-distribution generalization, or claim to invent hierarchical search. Known bounds, finite precision, irreversible greedy choices, a small reused test suite, and unverified probability calibration remain important limitations. The model's training-data membership and internal option handling are unknown.

Related reading: [Do NLP Models Know Numbers? Probing Numeracy in Embeddings](https://aclanthology.org/D19-1534/) motivates separating numerical representation, computation, and generalization. It does not validate this Jev-specific method.

Code and original documentation/figures: [MIT](LICENSE). Unaffiliated with TypeSafe; Jev is their model.
