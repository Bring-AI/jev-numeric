"""Additional binary-tree check, distinct from the original ten-way stock results."""

import json
import random
from datetime import UTC, datetime
from pathlib import Path

from probe_jev_index_history import CASES, SOURCE

from jev_numeric import JevClient, decode_number


def main():
    out = Path("runs") / ("binary-api-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    jobs = [
        (date, truth, supplied, reverse)
        for date, truth in CASES
        for supplied in (False, True)
        for reverse in (False, True)
    ]
    random.Random(7).shuffle(jobs)
    (out / "design.json").write_text(
        json.dumps(
            {
                "jobs": jobs,
                "branching": 2,
                "source": SOURCE,
                "note": "New binary implementation/prompt, not the original ten-way protocol. One run per order, three dates, oracle-input and closed-book conditions.",
            },
            indent=2,
        )
    )
    rows = []
    for i, (date, truth, supplied, reverse) in enumerate(jobs):
        state = {
            "index": "S&P 500 price index",
            "date": date,
            "observation": "Official closing level on the final trading day of the calendar year",
        }
        if supplied:
            state["closing_level_index_points"] = f"{truth / 100:.2f}"
        with JevClient(max_calls=24) as client:
            result = decode_number(
                client,
                state,
                "the official S&P 500 price index closing level on the specified date, in index points (not total return, an ETF, annual average, or intraday high)",
                lower="0",
                upper="10000",
                resolution="0.01",
                branching=2,
                reverse=reverse,
            )
            row = {
                "date": date,
                "truth": truth / 100,
                "supplied": supplied,
                "reverse": reverse,
                "result": result,
                "records": client.records,
                "absolute_percentage_error": abs(float(result["value"]) - truth / 100)
                / (truth / 100)
                * 100,
            }
        (out / f"case-{i:02d}.json").write_text(json.dumps(row, indent=2))
        rows.append({k: v for k, v in row.items() if k != "records"})
        (out / "results.json").write_text(json.dumps(rows, indent=2))
        print(
            json.dumps(
                {k: v for k, v in row.items() if k not in ("records", "result")}
                | {"value": result["value"]}
            ),
            flush=True,
        )
    summary = {}
    for supplied in (False, True):
        subset = [r for r in rows if r["supplied"] == supplied]
        summary["oracle_input" if supplied else "closed_book"] = {
            "n": len(subset),
            "mape": sum(r["absolute_percentage_error"] for r in subset) / len(subset),
            "exact": sum(float(r["result"]["value"]) == r["truth"] for r in subset),
        }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"out": str(out), "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
