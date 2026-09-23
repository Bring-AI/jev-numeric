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
| `branching` | Choices per level | `10` |

Bounds/resolution may be JSON numbers or decimal strings. Width must be an integer multiple
of resolution. The range must contain the answer; there is no automatic range expansion.
The reported value is the final cell's lower endpoint, not a confidence bound.

The compact response uses ordinary JSON numbers (Python floats). For exact decimal storage,
use `--details`: each number answer also includes `exact`, `interval`, `resolution`, `calls`
and `trace`, with decimal strings preserved. Resolution is not an accuracy guarantee.

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
each number question involves successive interval decisions. It validates every question
before making the first paid call. Total upstream calls are capped at 128 by default.
A request's `model` overrides the model environment setting; credentials and gateway still
come from the environment. The returned model is the identity reported by upstream.

Existing Python calls and the old CLI flags remain available. To call the JSON adapter
from Python: `evaluate(request)` (exported by `jev_numeric`).
