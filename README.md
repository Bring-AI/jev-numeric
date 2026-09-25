# A simple algorithm that turns Jev decisions into accurate numerical outputs

<p align="center">
  <a href="https://bring-ai.github.io/jev-numeric/"><img src="https://img.shields.io/badge/Website-Live%20Demo-2563eb?style=flat-square" alt="Website: Live Demo"></a>
  <a href="https://github.com/Bring-AI/jev-numeric/stargazers"><img src="https://img.shields.io/github/stars/Bring-AI/jev-numeric?style=flat-square" alt="GitHub stars"></a>
  <a href="https://arxiv.org/abs/2609.28587"><img src="https://img.shields.io/badge/arXiv-2609.28587-b31b1b?style=flat-square" alt="arXiv: 2609.28587"></a>
</p>

<p align="center">
  <img src="assets/hero.svg" alt="JevNeo: decisions become numerical outputs through a multiway interval tree" width="100%">
</p>

<p align="center"><strong>JevNeo · More than Choice</strong></p>
<p align="center">Numerical decoding with multiway decision trees, using interval or decimal-digit branches.</p>
<p align="center">
  <a href="README.zh-CN.md">中文</a> ·
  <a href="#turning-jev-to-numerical-output">Examples</a> ·
  <a href="#the-algorithm">How it works</a> ·
  <a href="#results">Results</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="artifacts/metrics.json">Recorded metrics</a>
</p>

**Jev is built for structured decisions. JevNeo turns them into numerical outputs through a multiway decision tree.** Each Choice selects a branch; the final leaf identifies a finite-precision value. Branches can be described as numerical intervals or decimal digits. **Both representations use ordinary Jev Choice calls—no training, regression head, or access to token logits.**

## What this adds

| Capability | Jev<br>Decision-only (official) | JevNeo (Ours) |
|---|:---:|:---:|
| Decisions & option probabilities | ✅ | ✅ |
| Rubric scores | ✅ | ✅ |
| Interval decoding | ❌ | ✅ |
| Digit-by-digit decoding | ❌ | ✅ |
| CDF / histogram construction | ❌ | ✅* |

Native API: [Choice](https://docs.typesafe.ai/primitives/choice), [Score](https://docs.typesafe.ai/primitives/score). *Experimental; calibration unverified.

| Branch representation | Each decision | Model returns |
|---|---|---|
| **`interval`** (default) | Which interval contains the value? | Interval label |
| **[`digits`](#digit-by-digit-decoding-no-logits)** | Given the selected prefix, what is the next decimal digit? | Digit `0–9` |

**Both are multiway decision trees; decimal-digit decoding is a ten-way instance.** On an aligned decimal grid, they can have identical branches and leaves, expressed through different prompts. The digit is a **Choice option**, not a vocabulary token; Jev returns the option probabilities directly.

## Even Better Performance Than Choosing from an Answer List

<p align="center">
  <img src="assets/performance.svg" alt="JevNeo reaches 83.40% within 5% relative error versus 80.47% for direct choice on 256 arithmetic expressions" width="100%">
</p>

**83.40% vs. 80.47% (+2.93 percentage points)** within 5% relative error on 256 arithmetic expressions—even when the direct-choice list contains the correct answer.

<sub>JevNeo bars use interval decoding. Error bars: 95% family-bootstrap intervals. LoRA heads are transfer baselines trained on causal distributions with different backbones; hatched bars supply the answer.</sub>

## Application example: token billing

Give Jev a pricing rule and an input-token count, and ask for the request's total cost. Example flat rate: **$2 per million input tokens**.

| Input tokens | Exact cost ($) | Jev forward / reverse ($) | Relative error |
|---:|---:|---:|---:|
| 1,000 | 0.002000 | 0.002000 / 0.002000 | 0% |
| 12,345 | 0.024690 | 0.024690 / 0.024690 | 0% |
| 123,456 | 0.246912 | 0.246900 / 0.246910 | 0.00081%–0.00486% |
| 987,654 | 1.975308 | 1.975200 / 1.975200 | 0.00547% |

<sub>Actual runs with an illustrative input-only rate; expected answers were not supplied. Forward/reverse means option order. Each output used seven ten-way decisions at $0.000001 resolution. [Full results, including tiered and cached pricing](artifacts/token-billing-20260923/summary.json).</sub>

## Application example: continuous game control

**[Watch full videos and all 69 attempts →](https://bring-ai.github.io/jev-numeric/)**

| Game | Numeric controls | Featured result | Video |
|---|---|---|---|
| CarRacing | Steering + signed throttle/brake | **100% track coverage** in 84.12s; all four K / precision settings completed | https://github.com/user-attachments/assets/e88496d5-c280-4dbe-8503-916486268f8e |
| LunarLander | Main + lateral engine | **Safe landing**, reward 243.91 | https://github.com/user-attachments/assets/c05a2498-43be-4739-8600-c1a3cf7666bf |
| MountainCar | Motor force | **Goal reached**, both seeds | https://github.com/user-attachments/assets/bd18b739-557c-4048-b5d9-84a7385246ec |
| BipedalWalker | Four joint commands | **Terrain completed**, reward 315.16 | https://github.com/user-attachments/assets/b61fb921-8549-4cf5-8bd1-71c62d175b44 |

Jev receives structured telemetry and explicit control guidance; JevNeo decodes the actual motor commands. No training or fallback controller. These recordings are selected after prompt and controller development; all earlier failures remain available. Videos omit API waiting.

Comparison-table Walker completed 1 of 2 development trajectories; an API-interrupted trajectory was continued from its exact recorded prefix. Its fixed feedback rules are compiled into input intervals; Jev selects each term bin, and the adapter explicitly sums and clips those values into joint commands. [Walker protocol and audits](docs/evidence/control/walker-redesign-REPORT.md).

| CarRacing, seed 7 · revised prompt | Resolution 0.020 | Resolution 0.005 |
|---|---:|---:|
| K=10 | **100% — 84.54s** | **100% — 84.06s** |
| K=20 | **100% — 85.44s** | **100% — 84.12s** |

<sub>Same revised prompt, forward option order, 180-second horizon; one rollout per setting. K=20 / 0.005 also completed seed 19 in 93.78s. K=10 / 0.005 needs three motor-refinement requests; the other settings need two. LunarLander's v14 prompt produced four safe terminations scoring above 200 across two seeds and their repeats. These selected development results are not general success-rate estimates. [Prompt changes, latency, and full evidence](docs/experiment-notes.md).</sub>

## Turning Jev to Numerical Output

| Your question | Numerical output |
|---|---:|
| **What is 1 + 1?** | **`2.00`** |
| **A stock costs USD 10. It rises by USD 1. What is its new price?** | **`11.00`** |
| **A stock costs USD 10.50. It rises by USD 1.25. What is its new price?** | **`11.75`** |

These are **actual Jev runs**, not expected-output placeholders. Each used ten-way interval decoding over `[0,100)` at `0.01` resolution: four Choice calls per answer. The input contained the question, **not the answer**. The JSON interface returns a number; Jev selects the branches underneath.

**JSON in**

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "state": "A stock costs USD 10. It rises by USD 1.",
  "questions": {
    "new_price": {
      "type": "number",
      "instructions": "What is the new stock price in USD?",
      "range": [0, 100],
      "resolution": 0.01
    }
  }
}
```

**JSON out — recorded response**

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {
    "new_price": {
      "type": "number",
      "value": 11.0
    }
  }
}
```

```bash
jev-numeric --request examples/stock-price.json
```

`number` is this project's local adapter type; upstream Jev still receives Choice questions. [JSON API reference](docs/json-api.md) · [Live request/response](artifacts/json-api-usd-20260923T091856Z/stock-price.json) · [All three examples](artifacts/readme-examples-20260923T091853Z/results.json).

## The algorithm

Follow a multiway tree from root to leaf, using one Jev Choice per branch. The `interval` and `digits` settings select how those branches are described to the model.

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

### Digit-by-digit decoding: no logits

Set **`"method": "digits"`** to select decimal digits instead of intervals:

```json
{
  "state": "A stock costs USD 10.50. It rises by USD 1.25.",
  "questions": {
    "new_price": {
      "type": "number",
      "method": "digits",
      "instructions": "What is the new stock price in USD?",
      "range": [0, 100],
      "resolution": 0.01
    }
  }
}
```

```text
Each step: original question + selected prefix → Choice(0, 1, …, 9)
Illustrative path: "" → "1" → "11." → "11.7" → "11.75" → numeric value 11.75
```

```bash
jev-numeric --request examples/stock-price-digits.json --details
```

The adapter inserts the decimal point and preserves leading zeros. The supported format is `[0, 10ⁿ)` at resolution `10⁻ᵈ`, with nonnegative integers `n,d`; it takes `n+d` sequential Choice calls. Extra fractional digits are truncated, not rounded. Signed values or other ranges can use `interval`. [JSON API and Python usage](docs/json-api.md#digit-by-digit-choice).

With ten equal branches on this decimal grid, both representations describe the same tree: prefix `0.81` identifies interval `[0.81, 0.82)`. **The difference is how the decision is presented to the model, not the tree structure.** Equivalent partitions do not imply identical model choices or probabilities. Choosing digit labels does not require a digit to be one tokenizer token, and does not establish that this prompt better matches Jev's training. Neither representation guarantees accurate or calibrated predictions.

[Live smoke check, including prompt revisions and all outputs](artifacts/digit-decoding-place-prompt-20260924/report.md). Historical accuracy results below remain tied to their original interval and digit prompts.

## Results

All primary experiments below used `typesafe/jev-1.13-20260917` through OpenRouter. No fine-tuning, no GPU inference, and no retrieval tool was supplied to Jev. These are small exploratory evaluations; repetitions are not additional unique problems.

### Historical index recall: 4.58% mean relative error

We asked for the S&P 500 **price index's official close on the last trading day** of 2019, 2020, and 2023. Jev received the index and date, but not the closing value. Every run started from `[0,10000)` and used ten-way refinement to `0.01` points. Two option orders × two repeats gave four runs per date.

| Date | Verified close | Range of decoded values across four runs | Absolute percentage error |
|---|---:|---:|---:|
| 2019-12-31 | 3230.78 | 3331.10–3391.10 | 3.11%–4.96% |
| 2020-12-31 | 3756.07 | 3891.00–3999.99 | 3.59%–6.49% |
| 2023-12-29 | 4769.83 | 4999.99 in all four runs | 4.83% |

- **Mean absolute percentage error: 4.58%.** Median: 4.83%; maximum: 6.49%.
- All twelve decoded values were too high. Fine decimal output did not imply fine accuracy.

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
| Mean absolute percentage error | 4.58% | **0%** |
| Median absolute percentage error | 4.83% | **0%** |
| Maximum absolute percentage error | 6.49% | **0%** |

Relative error = `100 × |decoded value − ground truth| / |ground truth|`, using the final cell's lower endpoint.

**Jev could read these supplied values and select the right intervals.** This supports separating factual recall from numerical readout. “Oracle input” means the correct answer is deliberately supplied in context; it is a readout control, not a prediction benchmark or evidence of universal numerical reasoning. Only three unique values were tested. [Raw control and report →](artifacts/jev-index-provided-20260923T081655Z/report.md)

### Measured comparison: intervals, digits, and bits

Both interval and decimal-digit decoding are available in the adapter. In our earlier experiment, twelve hand-picked arithmetic problems—six integers and six exact binary fractions—were evaluated with two option orders and two repeats: **48 evaluations per method**. These numbers describe the archived prompts, not a new benchmark of the current adapter.

Mean absolute percentage error (MAPE); all targets are nonzero.

| Method | Integers | Fractions | Overall | Sequential rounds |
|---|---:|---:|---:|---:|
| Direct 16-value choice | 0% | 6.73% | 3.37% | 1 |
| **Four-way interval decoding** | **0%** | **4.83%** | **2.42%** | **2** |
| Explicit candidate-set membership | 0% | 16.96% | 8.48% | 1 |
| Decimal digits with previous-digit prefix | 0% | 31.70% | 15.85% | 2 / 4 |
| Adaptive threshold search | 0% | 24.62% | 12.31% | 4 |
| Parallel thresholds + monotonic repair | 0% | 22.58% | 11.29% | 1 |
| Independent binary bits, explicit prompt | 23.33% | 27.21% | 25.27% | 1 |

**Multiway refinement had the lowest mean relative error on this tiny fixed grid.** It can also address a finer grid without listing every possible value in a single question. We have not established superior accuracy or latency at scale. Methods shared API calls for efficiency; rounds measure dependency depth, not isolated latency.

What these experiments suggest:

- **Encoding is another task.** Explicit-set questions had 8.48% MAPE; bit representation had 25.27%. The representations are mathematically related, but the prompts impose different demands.
- **Prompt clarity matters.** In an earlier crossed control, clearer bit instructions reduced MAPE from 40.95%–46.51% to 20.15%–24.31% across option orders. This change included an explicit computation rule, not just cleaner phrasing.
- **Fractions were harder.** Threshold comparisons and decimal-digit decoding performed much worse on fractions than on integers in this suite.
- **An ordering constraint is not automatic.** Threshold probabilities were nonmonotone in **25/48** runs. For one query, `P(Y ≤ 0.4375)=0.57` but `P(Y ≤ 0.5)=0.01`.

These are failure observations, not proofs that the other methods cannot work. [Full method comparison →](artifacts/jev-alternatives-20260923T080125Z/report.md) · [Prompt/order controls →](artifacts/jev-binary-controls-20260923T075624Z/report.md)

### A note on robustness

We also recorded a follow-up with **two branches and a different prompt** using the reusable decoder: closed-book recall had **31.17% MAPE** across six runs, while the six supplied-value runs had **0% MAPE**. This was not a controlled branching-factor ablation. It shows why the 4.58% result must stay attached to the recorded **ten-way protocol**, rather than being advertised as a general accuracy guarantee. [Follow-up evidence →](artifacts/binary-api-20260923T085013Z/summary.json)

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

The existing repository URL, `jev-numeric` command, and `jev_numeric` Python package remain compatible.

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

```bash
jev-numeric --request examples/stock-price.json
jev-numeric --request examples/addition.json
# Read a request from stdin:
cat examples/stock-price.json | jev-numeric --request -
# Include exact decimal strings, intervals and the decision path:
jev-numeric --request examples/stock-price.json --details --output runs/response.json
```

<details>
<summary>Python API (optional)</summary>

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

</details>

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

## Paper

JevNeo was previously named NumericJev. The paper and archived experiment recordings retain the original name.

[NumericJev: Jev-like LLM Numerical Decoding with Multiway Decision Trees](https://arxiv.org/abs/2609.28587) — Weiwei Ye, Hangchen Liu, Renhe Jiang.

## Scope

This repository demonstrates a **regression-style interface over a decision model**. It does not introduce a new trained regressor, establish out-of-distribution generalization, or claim to invent hierarchical search. Known bounds, finite precision, irreversible greedy choices, a small reused test suite, and unverified probability calibration remain important limitations. The model's training-data membership and internal option handling are unknown.

Unaffiliated with TypeSafe; Jev is their model.

## License

**[PolyForm Noncommercial 1.0.0](LICENSE).** Code and original documentation/figures are available for permitted noncommercial use, modification, and redistribution under these terms. Commercial use outside the license's permitted purposes requires separate permission from the copyright holders. Third-party components and materials retain their own licenses.

This licensing change does not revoke permissions already granted for versions previously distributed under MIT. Those versions retain their original license.
