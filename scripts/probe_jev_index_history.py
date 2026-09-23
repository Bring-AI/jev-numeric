"""Closed-book index recall with fixed-grid versus hierarchical interval choices."""

import argparse
import json
import math
import random
from datetime import UTC, datetime

import httpx
from probe_jev_binary import ROOT

from jev_numeric.client import settings

CASES = [("2019-12-31", 323078), ("2020-12-31", 375607), ("2023-12-29", 476983)]
SOURCE = "https://fred.stlouisfed.org/data/SP500"


def question(lo, hi, n):
    step = (hi - lo) // n
    assert (hi - lo) % n == 0 and step >= 1
    return {
        "type": "choice",
        "instructions": "Recall the historical S&P 500 price index official closing level on the date in state, in index points. "
        "Use the price index, NOT a total-return index, ETF share price, annual average, annual return, or intraday high. "
        "Choose the interval containing that closing level. Lower bounds are inclusive and upper bounds exclusive. "
        "This is historical factual recall, not a forecast.",
        "criteria": {
            str(
                i
            ): f"{(lo + i * step) / 100:.2f} <= closing level < {(lo + (i + 1) * step) / 100:.2f} index points"
            for i in range(n)
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provided-close", action="store_true")
    args = parser.parse_args()
    gateway, key, base, configured_model = settings()
    model = "typesafe/jev-1.13-20260917" if gateway == "openrouter" else "jev-1.13-20260917"
    jobs = [(i, rev, rep) for i in range(3) for rev in (False, True) for rep in range(2)]
    random.Random(7).shuffle(jobs)
    run_prefix = "jev-index-provided-" if args.provided_close else "jev-index-history-"
    out = ROOT / "runs" / (run_prefix + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    (out / "design.json").write_text(
        json.dumps(
            {
                "source": SOURCE,
                "truth": CASES,
                "model": model,
                "jobs": jobs,
                "provided_close": args.provided_close,
                "protocol": "Three S&P 500 year-end closes. Fixed [0,10000) range, six ten-way greedy levels down to .01 points. Single-call 100-bin control at width 100. Two orders and two repeats, English prompts. No prompt revision mid-run."
                + (
                    " Verified closing_level_index_points added to state; questions unchanged from closed-book run."
                    if args.provided_close
                    else " Truth never sent in state."
                ),
                "limits": "Historical recall, not forecasting or known training-set membership. Closed-book request but server internals unknown. Three dates only; greedy refinement can add false precision.",
            },
            indent=2,
        )
    )
    rows = []
    with httpx.Client(timeout=60, follow_redirects=False) as client:
        for job, (case, rev, rep) in enumerate(jobs):
            date, truth = CASES[case]
            lo, hi = 0, 1000000
            path = []
            for depth in range(6):
                qs = {"hierarchy": question(lo, hi, 10)}
                if depth == 0:
                    qs["direct_100_bins"] = question(0, 1000000, 100)
                if rev:
                    for q in qs.values():
                        q["criteria"] = dict(reversed(list(q["criteria"].items())))
                payload = {
                    "model": model,
                    "state": {
                        "index": "S&P 500 price index",
                        "date": date,
                        "observation": "Official closing level on the final trading day of the calendar year",
                    },
                    "questions": qs,
                }
                if args.provided_close:
                    payload["state"]["closing_level_index_points"] = f"{truth / 100:.2f}"
                response = client.post(
                    base.rstrip("/") + "/systemone",
                    headers={"Authorization": "Bearer " + key},
                    json=payload,
                )
                if response.status_code != 200:
                    (out / "error.json").write_text(
                        json.dumps({"job": job, "depth": depth, "status": response.status_code})
                    )
                    raise SystemExit(f"HTTP {response.status_code}; stopped: {out}")
                data = response.json()
                (out / f"job-{job:02d}-depth-{depth}.json").write_text(
                    json.dumps({"request": payload, "response": data}, indent=2)
                )
                answers = data["answers"]
                assert set(answers) == set(qs)
                for name, a in answers.items():
                    p = a["probabilities"]
                    assert a["type"] == "choice" and a["choice"] in qs[name]["criteria"]
                    assert set(p) == set(qs[name]["criteria"])
                    assert all(math.isfinite(v) and 0 <= v <= 1 for v in p.values())
                    assert abs(sum(p.values()) - 1) <= len(p) * 0.005 + 0.001
                if depth == 0:
                    direct_lo = int(answers["direct_100_bins"]["choice"]) * 10000
                step = (hi - lo) // 10
                lo += int(answers["hierarchy"]["choice"]) * step
                hi = lo + step
                path.append(
                    {
                        "lo_cents": lo,
                        "hi_cents": hi,
                        "contains_truth": lo <= truth < hi,
                        "probabilities": answers["hierarchy"]["probabilities"],
                        "usage": data.get("usage", {}),
                        "model": data.get("model"),
                    }
                )
            row = {
                "date": date,
                "truth": truth / 100,
                "reverse": rev,
                "repeat": rep,
                "job": job,
                "direct_interval": [direct_lo / 100, (direct_lo + 10000) / 100],
                "direct_correct": direct_lo <= truth < direct_lo + 10000,
                "hierarchy_100_correct": path[1]["contains_truth"],
                "path": path,
                "final_interval": [lo / 100, hi / 100],
                "final_correct": lo <= truth < hi,
                "absolute_error_lower_endpoint": abs(lo - truth) / 100,
            }
            rows.append(row)
            (out / "results.json").write_text(json.dumps(rows, indent=2))
            print(json.dumps({k: v for k, v in row.items() if k != "path"}), flush=True)
    summary = {
        "evaluations": len(rows),
        "direct_100_correct": sum(r["direct_correct"] for r in rows),
        "hierarchy_100_correct": sum(r["hierarchy_100_correct"] for r in rows),
        "hierarchy_cent_correct": sum(r["final_correct"] for r in rows),
        "reported_cost": sum(x["usage"].get("cost") or 0 for r in rows for x in r["path"]),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    lines = [
        "# Jev historical S&P 500 recall",
        "",
        f"Ground truth: {SOURCE}",
        f"Model: {model}",
        "Three dates x two option orders x two repeats. 72 API requests; no training.",
        "Verified close supplied in state; all question text unchanged."
        if args.provided_close
        else "No closing values supplied in state.",
        "Fixed range [0,10000), six ten-way levels. Direct control uses 100 bins of width 100, so compare it with hierarchy depth 2, not cent precision.",
        "Last intervals represent numeric resolution, NOT confidence intervals. Lower endpoints are used for reported absolute errors.",
        "",
        json.dumps(summary),
        "",
        "| Date | Reverse | Repeat | Truth | Direct interval | Hierarchy final interval | Error |",
        "|---|---|---|---:|---|---|---:|",
    ]
    for r in sorted(rows, key=lambda x: (x["date"], x["reverse"], x["repeat"])):
        lines.append(
            f"| {r['date']} | {r['reverse']} | {r['repeat']} | {r['truth']} | {r['direct_interval']} | {r['final_interval']} | {r['absolute_error_lower_endpoint']} |"
        )
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"out": str(out), "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
