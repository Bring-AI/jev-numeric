import argparse
import json
import sys
from pathlib import Path

from . import JevClient, decode_number, evaluate


def main():
    p = argparse.ArgumentParser(description="Numerical output through Jev interval choices")
    p.add_argument("--request", help="JSON request file, or - for stdin")
    p.add_argument(
        "--details", action="store_true", help="Include exact decimals and decision trace"
    )
    p.add_argument("--state", help="JSON object or string (legacy flag mode)")
    p.add_argument("--target")
    p.add_argument("--lower")
    p.add_argument("--upper")
    p.add_argument("--resolution", default=None)
    p.add_argument("--branching", type=int, default=None)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    legacy = (args.state, args.target, args.lower, args.upper, args.resolution, args.branching)
    if args.request:
        if any(x is not None for x in legacy):
            p.error("--request cannot be combined with legacy decoding flags")
        try:
            text = sys.stdin.read() if args.request == "-" else Path(args.request).read_text()
            result = evaluate(json.loads(text), details=args.details)
        except (OSError, ValueError, RuntimeError) as exc:
            p.error(str(exc))
        saved = result
    else:
        if any(x is None for x in legacy[:4]):
            p.error("Provide --request, or all of --state --target --lower --upper")
        with JevClient(max_calls=128) as client:
            result = decode_number(
                client,
                json.loads(args.state),
                args.target,
                lower=args.lower,
                upper=args.upper,
                resolution=args.resolution or "0.01",
                branching=10 if args.branching is None else args.branching,
            )
            saved = {"result": result, "records": client.records}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(saved, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
