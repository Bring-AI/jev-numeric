"""Recompute publication metrics and content hashes without network access."""

import hashlib
import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts"


def load(prefix):
    paths = list(A.glob(prefix + "*"))
    assert len(paths) == 1, paths
    return json.loads((paths[0] / "results.json").read_text())


def main():
    recall = load("jev-index-history-")
    provided = load("jev-index-provided-")
    alternatives = load("jev-alternatives-")
    prompt = load("jev-binary-controls-")
    errors = [abs(r["final_interval"][0] - r["truth"]) / r["truth"] * 100 for r in recall]
    oracle_errors = [abs(r["final_interval"][0] - r["truth"]) / r["truth"] * 100 for r in provided]
    assert all(r["target"] != 0 for r in alternatives + prompt), "MAPE requires nonzero targets"
    metrics = {
        "recall": {
            "n": len(recall),
            "unique_dates": len({r["date"] for r in recall}),
            "mape_percent": sum(errors) / len(errors),
            "median_ape_percent": median(errors),
            "max_ape_percent": max(errors),
            "within_5_percent": sum(e <= 5 for e in errors),
            "mean_absolute_error_points": sum(r["absolute_error_lower_endpoint"] for r in recall)
            / len(recall),
            "all_predictions_above_truth": all(r["final_interval"][0] > r["truth"] for r in recall),
        },
        "oracle_input": {
            "n": len(provided),
            "unique_values": len({r["truth"] for r in provided}),
            "mape_percent": mean(oracle_errors),
            "median_ape_percent": median(oracle_errors),
            "max_ape_percent": max(oracle_errors),
            "exact": sum(r["final_correct"] for r in provided),
            "correct_steps": sum(p["contains_truth"] for r in provided for p in r["path"]),
        },
        "arithmetic": {
            m: sum(r["correct"][m] for r in alternatives) for m in alternatives[0]["correct"]
        },
        "arithmetic_mape_percent": {
            m: {
                group: mean(
                    abs(r["predictions"][m] - r["target"]) / abs(r["target"]) * 100
                    for r in alternatives
                    if group == "all" or r["kind"] == group
                )
                for group in ("integer", "fraction", "all")
            }
            for m in alternatives[0]["predictions"]
        },
        "cdf_nonmonotone_runs": sum(r["cdf_adjacent_violations"] > 0 for r in alternatives),
        "prompt_controls": {
            f"{p}_{rev}": sum(
                r["binary_correct"] for r in prompt if r["prompt"] == p and r["reverse"] == rev
            )
            for p in ("original", "explicit")
            for rev in (False, True)
        },
        "prompt_controls_mape_percent": {
            f"{p}_{rev}": mean(
                abs(r["binary_value"] - r["target"]) / abs(r["target"]) * 100
                for r in prompt if r["prompt"] == p and r["reverse"] == rev
            )
            for p in ("original", "explicit")
            for rev in (False, True)
        },
    }
    assert round(metrics["recall"]["mape_percent"], 2) == 4.58
    assert metrics["oracle_input"]["exact"] == 12
    assert metrics["arithmetic"]["interval_selection"] == 39
    (A / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    manifest = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(A.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    (A / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
