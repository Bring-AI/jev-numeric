"""Verify immutable evidence and recompute central claims; no network calls."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "artifacts"


def main():
    manifest = json.loads((A / "manifest.json").read_text())
    for name, digest in manifest.items():
        path = ROOT / name
        assert path.is_file(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    paths = {
        tag: next(A.glob(tag + "-*"))
        for tag in ("jev-index-history", "jev-index-provided", "jev-alternatives")
    }
    oracle = json.loads((paths["jev-index-provided"] / "results.json").read_text())
    for r in oracle:
        lo, hi = 0, 1000000
        for depth in range(6):
            name = f"job-{r['job']:02d}-depth-{depth}.json"
            record = json.loads((paths["jev-index-provided"] / name).read_text())
            baseline = json.loads((paths["jev-index-history"] / name).read_text())
            state = record["request"]["state"].copy()
            supplied = state.pop("closing_level_index_points")
            assert float(supplied) == r["truth"]
            assert state == baseline["request"]["state"]
            assert record["response"]["model"] == baseline["response"]["model"]
            q = record["request"]["questions"]["hierarchy"]
            assert (
                q["instructions"] == baseline["request"]["questions"]["hierarchy"]["instructions"]
            )
            if depth == 0:
                assert record["request"]["questions"] == baseline["request"]["questions"]
            assert list(q["criteria"]) == list(
                map(str, reversed(range(10)) if r["reverse"] else range(10))
            )
            width = (hi - lo) // 10
            lo += int(record["response"]["answers"]["hierarchy"]["choice"]) * width
            hi = lo + width
            assert lo == r["path"][depth]["lo_cents"]
            assert hi == r["path"][depth]["hi_cents"]
            assert lo / 100 <= r["truth"] < hi / 100
        assert hi - lo == 1 and r["final_interval"] == [lo / 100, hi / 100]
    recall = json.loads((paths["jev-index-history"] / "results.json").read_text())
    mape = sum(abs(r["final_interval"][0] - r["truth"]) / r["truth"] * 100 for r in recall) / len(
        recall
    )
    assert round(mape, 2) == 4.58
    assert len(oracle) == 12
    alternatives = json.loads((paths["jev-alternatives"] / "results.json").read_text())
    assert len(alternatives) == 48
    assert sum(r["correct"]["interval_selection"] for r in alternatives) == 39
    assert sum(r["correct"]["direct"] for r in alternatives) == 40
    assert sum(r["cdf_adjacent_violations"] > 0 for r in alternatives) == 25
    metrics = json.loads((A / "metrics.json").read_text())
    for method, groups in metrics["arithmetic_mape_percent"].items():
        for group, recorded in groups.items():
            rows = [r for r in alternatives if group == "all" or r["kind"] == group]
            assert all(r["target"] != 0 for r in rows)
            measured = sum(
                abs(r["predictions"][method] - r["target"]) / abs(r["target"]) * 100
                for r in rows
            ) / len(rows)
            assert abs(measured - recorded) < 1e-10, (method, group)
    assert round(metrics["arithmetic_mape_percent"]["interval_selection"]["all"], 2) == 2.42
    assert round(metrics["arithmetic_mape_percent"]["direct"]["all"], 2) == 3.37
    print(
        f"{len(manifest)} artifact hashes verified; oracle-input state isolation and all 72 branches checked."
    )
    print(
        "Verified MAPE: recall 4.58%, oracle 0%, arithmetic intervals 2.42% vs direct 3.37%."
    )


if __name__ == "__main__":
    main()
