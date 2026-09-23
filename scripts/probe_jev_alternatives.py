"""Fixed arithmetic comparison: five alternative numeric interfaces and two controls."""

import json
import math
import random
import time
from datetime import UTC, datetime
from itertools import pairwise

import httpx
from probe_jev_binary import CASES, ROOT
from probe_jev_binary_controls import controlled_questions

from jev_numeric.client import settings


def choice(instructions, criteria):
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def value(k, scale):
    return str(k / scale)


def threshold(t):
    return choice(
        f"Compute the exact result x of the expression in state. Is x less than or equal to {t}? Equality counts as yes.",
        {"yes": f"x <= {t}", "no": f"x > {t}"},
    )


def interval(lo, hi, scale):
    step = (hi - lo) // 4
    assert step >= 1 and (hi - lo) % 4 == 0
    return choice(
        "Compute the exact result x of the expression in state. Choose the interval containing x. Each interval includes its lower bound and excludes its upper bound.",
        {
            str(i): f"{value(lo + i * step, scale)} <= x < {value(lo + (i + 1) * step, scale)}"
            for i in range(4)
        },
    )


def digit(kind, prefix):
    if kind == "integer":
        position = len(prefix)
        text = (
            "Write the exact arithmetic result x as a two-digit nonnegative decimal integer, including a leading zero if needed. "
            + (
                "Select the tens digit."
                if position == 0
                else f"The previously selected tens digit is {prefix}. Select the units digit."
            )
        )
    else:
        position = len(prefix)
        text = (
            f"Compute the exact arithmetic result x, which is in [0,1) and has at most four decimal places. Write it as 0.d1d2d3d4, appending trailing zeros if needed. Select decimal digit d{position + 1}, counting after the decimal point. "
            + (f"The previously selected decimal prefix is 0.{prefix}." if prefix else "")
        )
    return choice(text, {str(i): f"The requested decimal digit is {i}." for i in range(10)})


def isotonic(values):
    blocks = []
    for v in values:
        blocks.append([v, 1])
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            b, a = blocks.pop(), blocks.pop()
            blocks.append([(a[0] * a[1] + b[0] * b[1]) / (a[1] + b[1]), a[1] + b[1]])
    return [v for v, n in blocks for _ in range(n)]


def self_check():
    for scale in (1, 16):
        for code in range(16):
            cdf = [float(code <= k) for k in range(15)]
            fixed = isotonic(cdf)
            masses = [b - a for a, b in zip([0] + fixed, fixed + [1])]
            assert masses.index(max(masses)) == code
            lo, hi = 0, 16
            for _ in range(4):
                mid = (lo + hi) // 2
                if code <= mid - 1:
                    hi = mid
                else:
                    lo = mid
            assert lo == code and hi == code + 1
            group = code // 4
            assert group * 4 + (code % 4) == code
            text = f"{code:02d}" if scale == 1 else f"{code / scale:.4f}"[2:]
            recovered = int(text) if scale == 1 else int(text) / 10000
            assert recovered == code / scale
    assert isotonic([0.8, 0.2]) == [0.5, 0.5]
    print("Exhaustive 16-value decoder and isotonic checks passed.", flush=True)


def main():
    self_check()
    gateway, key, base, configured_model = settings()
    model = "typesafe/jev-1.13-20260917" if gateway == "openrouter" else "jev-1.13-20260917"
    jobs = [(i, rev, rep) for i in range(12) for rev in (False, True) for rep in range(2)]
    random.Random(7).shuffle(jobs)
    out = ROOT / "runs" / ("jev-alternatives-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    (out / "design.json").write_text(
        json.dumps(
            {
                "jobs": jobs,
                "model": model,
                "cases": [(e, str(t), k) for e, t, k in CASES],
                "protocol": "All five alternatives plus direct and explicit-bit controls. Two orders x two repeats x twelve fixed cases. Four dependent API rounds per job, independent method questions batched. No answers in state, no prompt changes during run.",
                "cdf_decoder": "Normalize returned yes/no probabilities; equal-weight PAVA on 15 thresholds; adjacent differences including endpoints give 16 masses; choose modal mass, ties smallest value. Save raw violations, mean and median.",
                "limits": "Hand-picked reused cases, not held-out or OOD. Internal API ordering and caching unknown. Decimal greedy prefix; interval/bisection greedy irreversible paths.",
            },
            indent=2,
        )
    )
    rows = []
    with httpx.Client(timeout=60, follow_redirects=False) as client:
        for job, (case, rev, rep) in enumerate(jobs):
            expression, target, kind = CASES[case]
            scale = 1 if kind == "integer" else 16
            lo, hi = 0, 16
            decimal = ""
            interval_lo = 0
            first = None
            calls = []
            for round_id in range(4):
                mid = (lo + hi) // 2
                qs = {"bisect": threshold(value(mid - 1, scale))}
                if round_id == 0:
                    qs.update(controlled_questions(kind, "explicit", False))
                    for k in range(15):
                        qs[f"threshold{k}"] = threshold(value(k, scale))
                    for i, w in enumerate((8, 4, 2, 1)):
                        qs[f"group{i}"] = choice(
                            "Compute the exact result x of the expression in state. Which set contains x? Select the set label; labels do not represent the numerical answer.",
                            {
                                str(b): "x is one of {"
                                + ", ".join(value(k, scale) for k in range(16) if (k // w) % 2 == b)
                                + "}"
                                for b in (0, 1)
                            },
                        )
                    qs["interval"] = interval(0, 16, scale)
                elif round_id == 1:
                    qs["interval"] = interval(interval_lo, interval_lo + 4, scale)
                if round_id < (2 if kind == "integer" else 4):
                    qs["decimal"] = digit(kind, decimal)
                if rev:
                    for q in qs.values():
                        q["criteria"] = dict(reversed(list(q["criteria"].items())))
                payload = {"model": model, "state": {"expression": expression}, "questions": qs}
                start = time.monotonic()
                response = client.post(
                    base.rstrip("/") + "/systemone",
                    headers={"Authorization": "Bearer " + key},
                    json=payload,
                )
                if response.status_code != 200:
                    (out / "error.json").write_text(
                        json.dumps({"job": job, "round": round_id, "status": response.status_code})
                    )
                    raise SystemExit(f"HTTP {response.status_code}, stopped: {out}")
                data = response.json()
                elapsed = time.monotonic() - start
                (out / f"job-{job:02d}-round-{round_id}.json").write_text(
                    json.dumps(
                        {"request": payload, "response": data, "elapsed_s": elapsed}, indent=2
                    )
                )
                answers = data["answers"]
                assert set(answers) == set(qs)
                for name, a in answers.items():
                    probs = a["probabilities"]
                    assert a["type"] == "choice" and a["choice"] in qs[name]["criteria"]
                    assert set(probs) == set(qs[name]["criteria"])
                    assert all(math.isfinite(p) and 0 <= p <= 1 for p in probs.values())
                    assert abs(sum(probs.values()) - 1) <= len(probs) * 0.005 + 0.001
                if first is None:
                    first = answers
                if answers["bisect"]["choice"] == "yes":
                    hi = mid
                else:
                    lo = mid
                if "decimal" in answers:
                    decimal += answers["decimal"]["choice"]
                if round_id == 0:
                    interval_lo = int(answers["interval"]["choice"]) * 4
                elif round_id == 1:
                    interval_pred = (interval_lo + int(answers["interval"]["choice"])) / scale
                calls.append(
                    {
                        "usage": data.get("usage", {}),
                        "elapsed_s": elapsed,
                        "model": data.get("model"),
                        "questions": len(qs),
                    }
                )
            raw = [
                first[f"threshold{k}"]["probabilities"]["yes"]
                / sum(first[f"threshold{k}"]["probabilities"].values())
                for k in range(15)
            ]
            cdf = isotonic(raw)
            masses = [b - a for a, b in zip([0] + cdf, cdf + [1])]
            assert min(masses) >= -1e-12 and abs(sum(masses) - 1) < 1e-12
            predictions = {
                "direct": float(first["direct"]["choice"]),
                "explicit_bits": int("".join(first[f"bit{i}"]["choice"] for i in range(1, 5)), 2)
                / scale,
                "explicit_groups": int("".join(first[f"group{i}"]["choice"] for i in range(4)), 2)
                / scale,
                "adaptive_bisection": lo / scale,
                "parallel_thresholds": max(range(16), key=lambda k: masses[k]) / scale,
                "decimal_digits": int(decimal) / (1 if kind == "integer" else 10000),
                "interval_selection": interval_pred,
            }
            row = {
                "job": job,
                "case": case,
                "expression": expression,
                "target": float(target),
                "kind": kind,
                "reverse": rev,
                "repeat": rep,
                "predictions": predictions,
                "correct": {m: p == target for m, p in predictions.items()},
                "decimal_string": decimal,
                "raw_cdf": raw,
                "isotonic_cdf": cdf,
                "masses": masses,
                "cdf_adjacent_violations": sum(a > b + 1e-9 for a, b in pairwise(raw)),
                "cdf_max_downward_step": max([0] + [a - b for a, b in pairwise(raw)]),
                "cdf_mean": sum(k * p / scale for k, p in enumerate(masses)),
                "cdf_median": next((k for k, p in enumerate(cdf) if p >= 0.5), 15) / scale,
                "calls": calls,
            }
            rows.append(row)
            (out / "results.json").write_text(json.dumps(rows, indent=2))
            if (job + 1) % 6 == 0:
                print(f"Completed {job + 1}/48 jobs ({(job + 1) * 4}/192 calls)", flush=True)
    methods = list(rows[0]["predictions"])
    summary = {
        m: {
            "correct": sum(r["correct"][m] for r in rows),
            "total": 48,
            "forward_correct": sum(r["correct"][m] for r in rows if not r["reverse"]),
            "reverse_correct": sum(r["correct"][m] for r in rows if r["reverse"]),
            "integer_correct": sum(r["correct"][m] for r in rows if r["kind"] == "integer"),
            "fraction_correct": sum(r["correct"][m] for r in rows if r["kind"] == "fraction"),
        }
        for m in methods
    }
    summary["cdf_diagnostics"] = {
        "runs_with_violations": sum(r["cdf_adjacent_violations"] > 0 for r in rows),
        "total_adjacent_violations": sum(r["cdf_adjacent_violations"] for r in rows),
        "max_downward_step": max(r["cdf_max_downward_step"] for r in rows),
        "median_correct": sum(r["cdf_median"] == r["target"] for r in rows),
    }
    summary["cost"] = sum(c["usage"].get("cost") or 0 for r in rows for c in r["calls"])
    summary["unpriced_calls"] = sum(
        c["usage"].get("cost") is None for r in rows for c in r["calls"]
    )
    rounds = {
        "direct": "1",
        "explicit_bits": "1",
        "explicit_groups": "1",
        "adaptive_bisection": "4",
        "parallel_thresholds": "1",
        "decimal_digits": "2 integer / 4 fraction",
        "interval_selection": "2",
    }
    lines = [
        "# Jev numeric interface comparison",
        "",
        f"Model: {model}",
        "12 fixed cases x 2 option orders x 2 repeats; 48 evaluations per method. 192 batched API calls.",
        "No training, no new held-out questions, no OOD or probability-calibration claim. Choice-map order reversed with labels/descriptions together.",
        "CDF mode uses PAVA; ties select smallest candidate. Decimal predictions are not snapped onto the candidate grid.",
        "Methods share calls for efficiency; rounds below are logical sequential depth, not isolated latency measurements.",
        "",
        "| Method | Correct /48 | Forward /24 | Reverse /24 | Integers /24 | Fractions /24 | Sequential rounds |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for m in methods:
        s = summary[m]
        lines.append(
            f"| {m} | {s['correct']} | {s['forward_correct']} | {s['reverse_correct']} | {s['integer_correct']} | {s['fraction_correct']} | {rounds[m]} |"
        )
    lines += [
        "",
        "## Diagnostics",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
        "## Predictions",
        "",
        "| Expression | Order | Repeat | Target | " + " | ".join(methods) + " |",
        "|---|---|---|---:|" + "---:|" * len(methods),
    ]
    for r in sorted(rows, key=lambda x: (x["case"], x["reverse"], x["repeat"])):
        lines.append(
            f"| {r['expression']} | {r['reverse']} | {r['repeat']} | {r['target']} | "
            + " | ".join(str(r["predictions"][m]) for m in methods)
            + " |"
        )
    (out / "report.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"out": str(out), "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
