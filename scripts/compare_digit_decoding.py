"""Small matched smoke check of interval and decimal-digit Choice decoding.

Expected values are evaluated locally and never sent to Jev. One run per problem,
method, and option order; this is an integration check, not an accuracy benchmark.
"""

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from jev_numeric import JevClient, decode_digits, decode_number

CASES = [
    ("What is 1 + 1?", "2.00", "100", "0.01"),
    (
        "A stock costs USD 10.50. It rises by USD 1.25. What is its new price in USD?",
        "11.75",
        "100",
        "0.01",
    ),
    ("What is 7 / 8 - 1 / 16?", "0.8125", "1", "0.0001"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    out = args.output or Path("runs") / (
        "digit-decoding-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    )
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for index, (question, expected, upper, resolution) in enumerate(CASES):
        for method, decoder in [("interval", decode_number), ("digits", decode_digits)]:
            for reverse in (False, True):
                with JevClient(max_calls=4) as client:
                    result = decoder(
                        client,
                        question,
                        "the numerical answer to the question",
                        lower=0,
                        upper=upper,
                        resolution=resolution,
                        reverse=reverse,
                    )
                    relative_error = (
                        abs(Decimal(result["value"]) - Decimal(expected))
                        / abs(Decimal(expected))
                        * 100
                    )
                    row = {
                        "question": question,
                        "expected": expected,
                        "method": method,
                        "reverse": reverse,
                        "value": result["value"],
                        "relative_error_percent": float(relative_error),
                        "calls": result["calls"],
                    }
                    filename = f"case-{index}-{method}-{'reverse' if reverse else 'forward'}.json"
                    record = {**row, "result": result, "records": client.records}
                    (out / filename).write_text(json.dumps(record, indent=2) + "\n")
                    results.append({**row, "record": filename})
                    (out / "summary.json").write_text(
                        json.dumps(
                            {
                                "protocol": "Three fixed questions; two methods; two option orders; "
                                "one run per condition. No answer supplied to Jev. "
                                "Integration smoke check, not a general accuracy estimate.",
                                "results": results,
                            },
                            indent=2,
                        )
                        + "\n"
                    )
                    print(json.dumps(row), flush=True)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
