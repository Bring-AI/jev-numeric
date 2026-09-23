"""Small live Jev arithmetic probe; no training, GPU, or answer leakage."""

import json
import math
import time
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path

import httpx

from jev_numeric.client import settings

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("1 + 1", 2, "integer"),
    ("2 + 3", 5, "integer"),
    ("7 - 4", 3, "integer"),
    ("3 * 4", 12, "integer"),
    ("12 / 3", 4, "integer"),
    ("7 + 8", 15, "integer"),
    ("1 / 2", Fraction(1, 2), "fraction"),
    ("1 / 4 + 1 / 8", Fraction(3, 8), "fraction"),
    ("3 / 4 - 1 / 4", Fraction(1, 2), "fraction"),
    ("3 / 8 + 5 / 16", Fraction(11, 16), "fraction"),
    ("(1 / 2) * (1 / 2)", Fraction(1, 4), "fraction"),
    ("7 / 8 - 1 / 16", Fraction(13, 16), "fraction"),
]


def questions(kind):
    scale = 1 if kind == "integer" else 16
    encoding = (
        "Represent the result as exactly four unsigned binary digits b1b2b3b4, "
        "with weights 8, 4, 2, 1. The result is an integer from 0 through 15."
        if kind == "integer"
        else "Represent the result as binary fraction 0.b1b2b3b4, with weights "
        "1/2, 1/4, 1/8, 1/16. The result is an exact multiple of 1/16 in [0,1)."
    )
    result = {
        "direct": {
            "type": "choice",
            "instructions": "Compute the arithmetic expression in state exactly. Choose its numerical result.",
            "criteria": {
                str(float(Fraction(k, scale))): str(float(Fraction(k, scale))) for k in range(16)
            },
        }
    }
    for i in range(1, 5):
        result[f"bit{i}"] = {
            "type": "choice",
            "instructions": (
                "Compute the arithmetic expression in state exactly. "
                + encoding
                + f" What is bit b{i}, counting from the left (most significant first)?"
            ),
            "criteria": {"0": "This bit is zero.", "1": "This bit is one."},
        }
    return result


def main():
    gateway, key, base, configured_model = settings()
    model = configured_model
    out = ROOT / "runs" / ("jev-binary-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    (out / "design.json").write_text(
        json.dumps(
            {
                "cases": [(e, str(y), k) for e, y, k in CASES],
                "gateway": gateway,
                "model": model,
                "max_requests": 12,
                "method": "Four independent bit questions and a 16-option direct control per case; no autoregressive conditioning.",
            },
            indent=2,
        )
    )
    rows = []
    with httpx.Client(timeout=60, follow_redirects=False) as client:
        for n, (expression, target, kind) in enumerate(CASES):
            scale = 1 if kind == "integer" else 16
            code = int(target * scale)
            assert Fraction(code, scale) == target and 0 <= code < 16
            truth = f"{code:04b}"
            payload = {
                "model": model,
                "state": {"expression": expression},
                "questions": questions(kind),
            }
            start = time.monotonic()
            response = client.post(
                base.rstrip("/") + "/systemone",
                headers={"Authorization": "Bearer " + key},
                json=payload,
            )
            if response.status_code != 200:
                (out / "error.json").write_text(
                    json.dumps({"case": n, "status": response.status_code})
                )
                raise SystemExit(
                    f"API status {response.status_code}; stopped without retry. Artifacts: {out}"
                )
            data = response.json()
            (out / f"case-{n:02d}.json").write_text(
                json.dumps({"request": payload, "response": data}, indent=2)
            )
            answers = data["answers"]
            for name, answer in answers.items():
                options = payload["questions"][name]["criteria"]
                probs = answer["probabilities"]
                assert answer["type"] == "choice" and answer["choice"] in options
                assert set(probs) == set(options)
                assert all(math.isfinite(p) and 0 <= p <= 1 for p in probs.values())
                assert abs(sum(probs.values()) - 1) <= len(probs) * 0.005 + 0.001
            bits = "".join(answers[f"bit{i}"]["choice"] for i in range(1, 5))
            pred = int(bits, 2) / scale
            direct = float(answers["direct"]["choice"])
            p1 = [
                answers[f"bit{i}"]["probabilities"]["1"]
                / sum(answers[f"bit{i}"]["probabilities"].values())
                for i in range(1, 5)
            ]
            row = {
                "expression": expression,
                "kind": kind,
                "target": float(target),
                "truth_bits": truth,
                "predicted_bits": bits,
                "binary_prediction": pred,
                "direct_prediction": direct,
                "binary_correct": pred == target,
                "direct_correct": direct == target,
                "correct_bits": sum(a == b for a, b in zip(bits, truth)),
                "p1": p1,
                "marginal_mean": sum(p * w / scale for p, w in zip(p1, (8, 4, 2, 1))),
                "elapsed_s": time.monotonic() - start,
                "served_model": data.get("model"),
                "usage": data.get("usage", {}),
            }
            rows.append(row)
            (out / "results.json").write_text(json.dumps(rows, indent=2))
            print(json.dumps(row), flush=True)
    summary = {
        "n": len(rows),
        "direct_correct": sum(r["direct_correct"] for r in rows),
        "binary_correct": sum(r["binary_correct"] for r in rows),
        "correct_bits": sum(r["correct_bits"] for r in rows),
        "total_bits": 4 * len(rows),
        "reported_cost": sum(r["usage"].get("cost") or 0 for r in rows),
        "unpriced_requests": sum(r["usage"].get("cost") is None for r in rows),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    lines = [
        "# Jev binary arithmetic smoke test",
        "",
        json.dumps(summary),
        "",
        "One run, 12 hand-picked exact cases, English prompts. No training or OOD claim.",
        "Four independent bit questions, not a conditional joint distribution. Direct control has 16 options.",
        "Raw API probabilities retained; marginal means normalize rounding error.",
        "",
        "| Expression | Target | Truth bits | Predicted bits | Binary value | Direct choice |",
        "|---|---:|---|---|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['expression']} | {r['target']} | {r['truth_bits']} | {r['predicted_bits']} | {r['binary_prediction']} | {r['direct_prediction']} |"
        )
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"out": str(out), "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
