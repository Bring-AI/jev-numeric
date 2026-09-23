import re
from decimal import Decimal

import pytest

from jev_numeric import decode_number, estimate_distribution


class ExactOracle:
    def ask(self, state, questions):
        y = Decimal(state["value"])
        answers = {}
        for name, q in questions.items():
            if name.startswith("cdf_"):
                t = Decimal(q["criteria"]["yes"].split("<= ")[1])
                selected = "yes" if y <= t else "no"
            else:
                selected = None
                for label, description in q["criteria"].items():
                    lo, hi = re.match(r"(.+) <= value < (.+)", description).groups()
                    if Decimal(lo) <= y < Decimal(hi):
                        selected = label
                        break
                assert selected is not None
            answers[name] = {
                "choice": selected,
                "type": "choice",
                "probabilities": {k: float(k == selected) for k in q["criteria"]},
            }
        return {"answers": answers}


@pytest.mark.parametrize("branching", [2, 4, 10])
@pytest.mark.parametrize("reverse", [False, True])
def test_exact_boundaries_and_uneven_tree(branching, reverse):
    for value in ["-1.00", "-0.99", "0", "0.01", "1.30"]:
        r = decode_number(
            ExactOracle(),
            {"value": value},
            "the provided value",
            lower="-1",
            upper="1.31",
            resolution=".01",
            branching=branching,
            reverse=reverse,
        )
        assert Decimal(r["value"]) == Decimal(value)
        assert Decimal(r["upper"]) - Decimal(r["lower"]) == Decimal(".01")
        assert r["calls"] <= 8


def test_precision_is_a_grid_not_a_claim_of_accuracy():
    r = decode_number(
        ExactOracle(), {"value": "3.14159"}, "value", lower="0", upper="10", resolution=".01"
    )
    assert r["lower"] == "3.14"
    assert r["upper"] == "3.15"


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(lower="1", upper="0"),
        dict(resolution="0"),
        dict(resolution=".3"),
        dict(branching=1),
        dict(lower="NaN"),
    ],
)
def test_invalid_grid(kwargs):
    args = dict(lower="0", upper="1", resolution=".01", branching=2)
    args.update(kwargs)
    with pytest.raises(ValueError):
        decode_number(ExactOracle(), {}, "value", **args)


def test_histogram_contains_oracle_and_is_normalized():
    r = estimate_distribution(
        ExactOracle(), {"value": ".42"}, "value", lower="0", upper="1", bins=10
    )
    assert sum(r["masses"]) == pytest.approx(1)
    assert r["masses"][4] == pytest.approx(1)
    assert r["raw_monotonicity_violations"] == 0


def test_inconsistent_cdf_is_reported_before_repair():
    class Inconsistent:
        def ask(self, state, questions):
            return {
                "answers": {
                    k: {"probabilities": {"yes": p, "no": 1 - p}}
                    for k, p in zip(questions, [0.8, 0.2])
                }
            }

    r = estimate_distribution(Inconsistent(), {}, "value", lower="0", upper="1", bins=3)
    assert r["raw_cdf"] == [0.8, 0.2]
    assert r["cdf"] == [0.5, 0.5]
    assert r["raw_monotonicity_violations"] == 1
    assert r["masses"] == [0.5, 0, 0.5]
