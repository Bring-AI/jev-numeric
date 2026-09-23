import copy
import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from jev_numeric import evaluate


class Oracle:
    model = "test-jev"

    def __init__(self):
        self.records = []

    def ask(self, state, questions):
        answers = {}
        y = Decimal(state["value"])
        for name, q in questions.items():
            if name.startswith("cdf_"):
                t = Decimal(q["criteria"]["yes"].split("<= ")[1])
                key = "yes" if y <= t else "no"
            else:
                matches = []
                for k, text in q["criteria"].items():
                    lo, hi = text.split(" <= value < ")
                    if Decimal(lo) <= y < Decimal(hi):
                        matches.append(k)
                assert len(matches) == 1
                key = matches[0]
            answers[name] = {
                "type": "choice",
                "choice": key,
                "probabilities": {k: int(k == key) for k in q["criteria"]},
            }
        data = {"model": "served-jev", "answers": answers}
        self.records.append({"request": {"state": state, "questions": questions}, "response": data})
        return data


def payload():
    return {
        "state": {"value": "11.75"},
        "questions": {
            "price": {
                "type": "number",
                "instructions": "the supplied value",
                "range": [0, 100],
                "resolution": 0.01,
            }
        },
    }


def test_official_style_request_and_numeric_answer():
    client = Oracle()
    request = payload()
    saved = copy.deepcopy(request)
    result = evaluate(request, client=client)
    assert request == saved
    assert result == {
        "model": "served-jev",
        "answers": {"price": {"type": "number", "value": 11.75}},
    }
    assert len(client.records) == 4
    assert json.loads(json.dumps(result)) == result


def test_multiple_questions_and_distribution_details():
    request = payload()
    request["questions"]["uncertainty"] = {
        "type": "distribution",
        "instructions": "the supplied value",
        "range": [0, 100],
        "bins": 10,
    }
    result = evaluate(request, client=Oracle(), details=True)
    assert result["answers"]["price"]["exact"] == "11.75"
    assert result["answers"]["price"]["interval"] == ["11.75", "11.76"]
    dist = result["answers"]["uncertainty"]
    assert sum(dist["probabilities"]) == pytest.approx(1)
    assert dist["probabilities"][1] == 1
    assert dist["calibrated"] is False
    assert dist["raw_monotonicity_violations"] == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"type": "number", "instructions": "value", "range": [0, 1], "resolution": 0.3},
        {"type": "number", "instructions": "value", "range": [0, 1], "resolution": 0},
        {"type": "number", "instructions": "value", "range": [0, 1], "branching": True},
        {"type": "distribution", "instructions": "value", "range": [0, 1], "bins": 0},
        {"type": "distribution", "instructions": "value", "range": [0, 1], "resolution": 0.01},
        {"type": "choice", "instructions": "value", "range": [0, 1]},
        {"type": "number", "instructions": "value", "range": [0, float("inf")]},
    ],
)
def test_all_questions_validated_before_any_paid_call(bad):
    request = payload()
    request["questions"]["bad"] = bad
    client = Oracle()
    with pytest.raises(ValueError):
        evaluate(request, client=client)
    assert not client.records


def test_request_model_is_applied_to_owned_client():
    client = Oracle()
    client.model = "chosen-model"
    request = payload() | {"model": "chosen-model"}
    with patch("jev_numeric.api.JevClient") as factory:
        factory.return_value.__enter__.return_value = client
        evaluate(request)
        factory.assert_called_once_with(model="chosen-model", max_calls=128)


def test_injected_client_model_mismatch_rejected():
    with pytest.raises(ValueError):
        evaluate(payload() | {"model": "different-model"}, client=Oracle())


def test_json_cli_from_stdin(capsys):
    from jev_numeric.cli import main

    request = payload()
    with (
        patch("sys.argv", ["jev-numeric", "--request", "-"]),
        patch("sys.stdin", SimpleNamespace(read=lambda: json.dumps(request))),
        patch("jev_numeric.cli.evaluate", return_value={"answers": {}}) as run,
    ):
        main()
    assert json.loads(capsys.readouterr().out) == {"answers": {}}
    assert run.call_args.args[0] == request
