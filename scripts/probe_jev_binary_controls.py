"""Cross prompt clarity and option order on the pre-existing arithmetic suite."""

import json
import math
import random
import time
from datetime import UTC, datetime
from fractions import Fraction

import httpx
from probe_jev_binary import CASES, ROOT, questions

from jev_numeric.client import settings


def controlled_questions(kind, prompt, reverse):
    result = questions(kind)
    if prompt == "explicit":
        scale = 1 if kind == "integer" else 16
        equation = (
            "x = 8*b1 + 4*b2 + 2*b3 + b4"
            if kind == "integer"
            else "x = (1/2)*b1 + (1/4)*b2 + (1/8)*b3 + (1/16)*b4"
        )
        for i, weight in enumerate((8, 4, 2, 1), start=1):
            w = str(Fraction(weight, scale))
            result[f"bit{i}"] = {
                "type": "choice",
                "instructions": (
                    "First compute the exact numerical result x of the arithmetic expression in state. "
                    f"Encode x using four bits, each either 0 or 1, defined by {equation}. "
                    "b1 is the LEFTMOST bit and b4 the RIGHTMOST; include leading zeros. "
                    f"This question asks ONLY for b{i}, the bit with numerical weight {w}. "
                    f"Equivalently, b{i} = floor(x / ({w})) modulo 2. "
                    "Select the bit value, not the whole answer, not a decimal digit, "
                    "and not a bit of either operand. Option labels 0 and 1 are literal bit values, "
                    "not option positions."
                ),
                "criteria": {
                    "0": f"b{i}=0: the {w}-weight bit is OFF; floor(x / ({w})) is even.",
                    "1": f"b{i}=1: the {w}-weight bit is ON; floor(x / ({w})) is odd.",
                },
            }
    if reverse:
        for question in result.values():
            question["criteria"] = dict(reversed(list(question["criteria"].items())))
    return result


def main():
    gateway, key, base, configured_model = settings()
    model = "typesafe/jev-1.13-20260917" if gateway == "openrouter" else "jev-1.13-20260917"
    jobs = [
        (i, prompt, reverse, repeat)
        for i in range(len(CASES))
        for prompt in ("original", "explicit")
        for reverse in (False, True)
        for repeat in range(2)
    ]
    random.Random(7).shuffle(jobs)
    out = ROOT / "runs" / ("jev-binary-controls-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    (out / "design.json").write_text(
        json.dumps(
            {
                "model": model,
                "gateway": gateway,
                "seed": 7,
                "jobs": jobs,
                "cases": [(x, str(y), k) for x, y, k in CASES],
                "design": "2 prompts x 2 criterion insertion orders x 2 repeats x 12 fixed cases; randomized schedule; no prompt revision during run",
                "limits": "API may canonicalize option order internally; repeats may be cached. Independent bits, no conditional prefix, no training.",
            },
            indent=2,
        )
    )
    rows = []
    with httpx.Client(timeout=60, follow_redirects=False) as client:
        for n, (case, prompt, reverse, repeat) in enumerate(jobs):
            expression, target, kind = CASES[case]
            scale = 1 if kind == "integer" else 16
            truth = f"{int(target * scale):04b}"
            payload = {
                "model": model,
                "state": {"expression": expression},
                "questions": controlled_questions(kind, prompt, reverse),
            }
            start = time.monotonic()
            response = client.post(
                base.rstrip("/") + "/systemone",
                headers={"Authorization": "Bearer " + key},
                json=payload,
            )
            if response.status_code != 200:
                (out / "error.json").write_text(
                    json.dumps({"job": n, "status": response.status_code})
                )
                raise SystemExit(f"HTTP {response.status_code}; stopped without retries. {out}")
            data = response.json()
            (out / f"request-{n:03d}.json").write_text(
                json.dumps({"request": payload, "response": data}, indent=2)
            )
            answers = data["answers"]
            assert set(answers) == set(payload["questions"])
            for name, answer in answers.items():
                options = payload["questions"][name]["criteria"]
                probs = answer["probabilities"]
                assert answer["type"] == "choice" and answer["choice"] in options
                assert set(probs) == set(options)
                assert all(math.isfinite(p) and 0 <= p <= 1 for p in probs.values())
                assert abs(sum(probs.values()) - 1) <= len(probs) * 0.005 + 0.001
            bits = "".join(answers[f"bit{i}"]["choice"] for i in range(1, 5))
            direct = float(answers["direct"]["choice"])
            row = {
                "job": n,
                "case": case,
                "expression": expression,
                "target": float(target),
                "kind": kind,
                "prompt": prompt,
                "reverse": reverse,
                "repeat": repeat,
                "truth_bits": truth,
                "predicted_bits": bits,
                "binary_value": int(bits, 2) / scale,
                "direct_value": direct,
                "binary_correct": bits == truth,
                "direct_correct": direct == target,
                "correct_bits": sum(a == b for a, b in zip(bits, truth)),
                "p1": [answers[f"bit{i}"]["probabilities"]["1"] for i in range(1, 5)],
                "model": data.get("model"),
                "usage": data.get("usage", {}),
                "elapsed_s": time.monotonic() - start,
            }
            rows.append(row)
            (out / "results.json").write_text(json.dumps(rows, indent=2))
            if (n + 1) % 12 == 0:
                print(f"Completed {n + 1}/{len(jobs)} requests", flush=True)
    summary = {}
    lines = [
        "# Jev binary prompt and order controls",
        "",
        f"Model: {model}",
        "12 fixed cases; two repeats per cell, randomly interleaved. No training.",
        "Option keys and descriptions kept together when reversing serialized criterion order.",
        "API internal ordering/caching is unknown; repeats are not independent new problems.",
        "",
        "| Prompt | Order | Direct correct /24 | Binary correct /24 | Bits correct /96 |",
        "|---|---|---:|---:|---:|",
    ]
    for prompt in ("original", "explicit"):
        for reverse in (False, True):
            subset = [r for r in rows if r["prompt"] == prompt and r["reverse"] == reverse]
            name = prompt + ("_reverse" if reverse else "_forward")
            item = {
                "n": len(subset),
                "direct_correct": sum(r["direct_correct"] for r in subset),
                "binary_correct": sum(r["binary_correct"] for r in subset),
                "correct_bits": sum(r["correct_bits"] for r in subset),
            }
            summary[name] = item
            lines.append(
                f"| {prompt} | {'reverse' if reverse else 'forward'} | {item['direct_correct']} | {item['binary_correct']} | {item['correct_bits']} |"
            )
    pairs = {(r["case"], r["prompt"], r["reverse"], r["repeat"]): r for r in rows}
    for prompt in ("original", "explicit"):
        flipped = 0
        delta = []
        repeat_flips = 0
        for case in range(len(CASES)):
            for repeat in range(2):
                a, b = (pairs[case, prompt, rev, repeat] for rev in (False, True))
                flipped += sum(x != y for x, y in zip(a["predicted_bits"], b["predicted_bits"]))
                delta.extend(abs(x - y) for x, y in zip(a["p1"], b["p1"]))
            for rev in (False, True):
                a, b = (pairs[case, prompt, rev, repeat] for repeat in range(2))
                repeat_flips += sum(
                    x != y for x, y in zip(a["predicted_bits"], b["predicted_bits"])
                )
        summary[prompt + "_stability"] = {
            "order_bit_flips_of_96": flipped,
            "mean_order_p1_delta": sum(delta) / len(delta),
            "repeat_bit_flips_of_96": repeat_flips,
        }
    summary["reported_cost"] = sum(r["usage"].get("cost") or 0 for r in rows)
    summary["unpriced_requests"] = sum(r["usage"].get("cost") is None for r in rows)
    lines += [
        "",
        "## Stability",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
        "## Individual results",
        "",
        "| Expression | Prompt | Reversed | Repeat | Truth | Bits | Binary value | Direct |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for r in sorted(rows, key=lambda r: (r["case"], r["prompt"], r["reverse"], r["repeat"])):
        lines.append(
            f"| {r['expression']} | {r['prompt']} | {r['reverse']} | {r['repeat']} | {r['truth_bits']} | {r['predicted_bits']} | {r['binary_value']} | {r['direct_value']} |"
        )
    (out / "report.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"out": str(out), "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
