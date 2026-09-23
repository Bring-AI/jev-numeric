# JSON interface

Use the familiar `model` / `state` / `questions` → `answers` shape.
**`number` and `distribution` are local adapter types, not native TypeSafe API types.**
The CLI translates them into multiple Jev Choice calls. No HTTP service is required or provided.

## Number

Input: [stock-price.json](../examples/stock-price.json)

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

Recorded output:

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

| Field | Meaning | Default |
|---|---|---|
| `model` | Gateway-specific Jev identifier | Environment setting |
| `state` | Shared JSON input | Required |
| `questions` | Named questions | Required |
| `instructions` | Which quantity to determine | Required |
| `range` | `[lower, upper)` for number decoding | Required |
| `resolution` | Final cell width | `0.01` |
| `method` | `interval` or `digits` | `interval` |
| `branching` | Interval choices per level; digits requires `10` | `10` |

Bounds/resolution may be JSON numbers or decimal strings. Width must be an integer multiple
of resolution. The range must contain the answer; there is no automatic range expansion.
The reported value is the final cell's lower endpoint, not a confidence bound.

The compact response uses ordinary JSON numbers (Python floats). For exact decimal storage,
use `--details`: each number answer also includes `method`, `exact`, `interval`, `resolution`, `calls`
and `trace`, with decimal strings preserved. Resolution is not an accuracy guarantee.

## Digit-by-digit Choice

Add `"method": "digits"` to a `number` question. Input:
[stock-price-digits.json](../examples/stock-price-digits.json).
The response keeps the same `{"type": "number", "value": ...}` shape.

At each step, Jev receives the original state, the numerical question, a fixed decimal
format, and the previously selected prefix. Its ten Choice options are `"0"` through
`"9"`, with place-specific descriptions such as `"The tenths digit is 7."`.
Instructions name the units/tens position or the index after the decimal point explicitly.
The adapter appends the selected digit and inserts the decimal point locally.
**No raw logits, vocabulary scores, or free-text generation are used.**

Requirements:

- Range is `[0, 10ⁿ)`, where `n` is a nonnegative integer (`[0,1)`, `[0,10)`, etc.).
- Resolution is `10⁻ᵈ`, where `d` is a nonnegative integer (`1`, `0.1`, `0.01`, etc.).
- Use `n` integer digits and `d` fractional digits, with leading/trailing zeros as needed.
  For `[0,1)`, the fixed `0.` prefix requires no Choice call.
- The requested representation truncates extra fractional digits, matching the interval
  decoder's lower-endpoint convention for nonnegative values. It does not round.
- The method makes `n+d` sequential calls; `branching` must be omitted or `10`.
- Signed values, arbitrary bounds, and other grid steps use `method: "interval"`.

With `--details`, each trace entry includes the selected `choice`, `prefix`, its implied
`lower`/`upper` interval, and the returned option `probabilities`. These probabilities are
conditional on the supplied question and prefix; they are not a calibrated distribution
over numerical outcomes. A wrong earlier digit cannot be revised by this greedy decoder.

```bash
jev-numeric --request examples/stock-price-digits.json --details
python scripts/compare_digit_decoding.py
```

Python callers can use `decode_digits(client, state, target, lower=0, upper=100,
resolution="0.01", reverse=False)`. `reverse=True` reverses insertion order while keeping
each digit's label and description. `evaluate(request)` selects the decoder from `method`;
the legacy individual CLI flags continue to use interval decoding.

## Distribution (experimental)

Input: [distribution.json](../examples/distribution.json)

```json
{
  "state": {"value": "0.42"},
  "questions": {
    "value_distribution": {
      "type": "distribution",
      "instructions": "the supplied value",
      "range": [0, 1],
      "bins": 8
    }
  }
}
```

The answer contains `type`, `edges`, `probabilities`, `calibrated: false`, and
`raw_monotonicity_violations`. Here support is `(lower, upper]`; bins are right-closed.
`probabilities[i]` is the mass for `(edges[i], edges[i+1]]` after monotonic repair.
`bins` defaults to 16 (allowed: 2–128). `--details` adds raw/repaired CDF and exact edge strings.
This is a constructed histogram, not validated predictive uncertainty.

## Run

```bash
jev-numeric --request examples/stock-price.json
cat examples/addition.json | jev-numeric --request -
jev-numeric --request examples/distribution.json --details
jev-numeric --request examples/stock-price.json --output runs/response.json
```

Multiple named questions can share one state. This adapter evaluates them sequentially;
each number question involves successive interval or digit decisions. It validates every question
before making the first paid call. Total upstream calls are capped at 128 by default.
A request's `model` overrides the model environment setting; credentials and gateway still
come from the environment. The returned model is the identity reported by upstream.

Existing Python calls and the old CLI flags remain available. To call the JSON adapter
from Python: `evaluate(request)` (exported by `jev_numeric`).
