import argparse
import json
from pathlib import Path

from . import JevClient, decode_number


def main():
    p = argparse.ArgumentParser(description="Decode a number through Jev interval choices")
    p.add_argument("--state", required=True, help="JSON object or string")
    p.add_argument("--target", required=True)
    p.add_argument("--lower", required=True)
    p.add_argument("--upper", required=True)
    p.add_argument("--resolution", default="0.01")
    p.add_argument("--branching", type=int, default=10)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    with JevClient(max_calls=128) as client:
        result = decode_number(
            client,
            json.loads(args.state),
            args.target,
            lower=args.lower,
            upper=args.upper,
            resolution=args.resolution,
            branching=args.branching,
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps({"result": result, "records": client.records}, indent=2)
            )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
