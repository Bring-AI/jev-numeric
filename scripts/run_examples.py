"""Run the exact input/output examples shown near the top of the README."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from jev_numeric import JevClient, decode_number

EXAMPLES = [
    ("What is 1 + 1?", "2.00"),
    ("A stock costs USD 10. It rises by USD 1. What is its new price in USD?", "11.00"),
    ("A stock costs USD 10.50. It rises by USD 1.25. What is its new price in USD?", "11.75"),
]
TARGET = "the numerical answer to the question, in the stated units"


def main():
    out = Path("runs") / ("readme-examples-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for i, (question, expected) in enumerate(EXAMPLES):
        with JevClient(max_calls=4) as client:
            result = decode_number(
                client,
                {"question": question},
                TARGET,
                lower="0",
                upper="100",
                resolution="0.01",
                branching=10,
            )
            row = {
                "question": question,
                "expected": expected,
                "result": result,
                "correct": Decimal(result["value"]) == Decimal(expected),
                "records": client.records,
            }
        (out / f"example-{i:02d}.json").write_text(json.dumps(row, indent=2))
        rows.append({k: v for k, v in row.items() if k != "records"})
        print(
            json.dumps(
                {
                    "question": question,
                    "expected": expected,
                    "actual": result["value"],
                    "correct": row["correct"],
                }
            ),
            flush=True,
        )
    (out / "results.json").write_text(json.dumps(rows, indent=2))
    print(f"Saved all examples: {out}")


if __name__ == "__main__":
    main()
