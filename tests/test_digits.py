import copy
from decimal import Decimal

import pytest

import jev_numeric


class DigitChoices:
    """A Choice-only transport with preselected digits; no token-score interface."""

    model = "test-jev"

    def __init__(self, digits):
        self.digits = iter(digits)
        self.records = []

    def ask(self, state, questions):
        assert len(questions) == 1
        name, question = next(iter(questions.items()))
        assert question["type"] == "choice"
        assert set(question["criteria"]) == set("0123456789")
        digit = next(self.digits)
        response = {
            "model": self.model,
            "answers": {
                name: {
                    "type": "choice",
                    "choice": digit,
                    "probabilities": {key: float(key == digit) for key in question["criteria"]},
                }
            },
        }
        self.records.append(
            {"request": {"state": state, "questions": questions}, "response": response}
        )
        return response


def request(**overrides):
    return {
        "state": "A stock costs USD 10.50 and rises by USD 1.25.",
        "questions": {
            "price": {
                "type": "number",
                "method": "digits",
                "instructions": "the new stock price in USD",
                "range": [0, 100],
                "resolution": "0.01",
                **overrides,
            }
        },
    }


def test_json_digits_preserves_original_question_and_prefix_without_logits():
    client = DigitChoices("1175")
    payload = request()
    original = copy.deepcopy(payload)
    result = jev_numeric.evaluate(payload, client=client, details=True)
    answer = result["answers"]["price"]
    assert payload == original
    assert answer["value"] == 11.75
    assert answer["exact"] == "11.75"
    assert answer["interval"] == ["11.75", "11.76"]
    assert answer["method"] == "digits"
    assert answer["calls"] == 4
    assert [step["prefix"] for step in answer["trace"]] == ["1", "11.", "11.7", "11.75"]
    for record, prefix in zip(client.records, ["", "1", "11.", "11.7"]):
        assert record["request"]["state"] == payload["state"]
        question = next(iter(record["request"]["questions"].values()))
        assert "new stock price in USD" in question["instructions"]
        assert f'Previously selected prefix: "{prefix}"' in question["instructions"]


@pytest.mark.parametrize(
    "upper,resolution,digits,expected",
    [
        (100, ".01", "0075", "0.75"),
        (1, ".0001", "0007", "0.0007"),
        (100, 1, "09", "9"),
        (1, 1, "", "0"),
        (10, ".01", "999", "9.99"),
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_digits_decimal_placement_boundaries_and_option_order(
    upper, resolution, digits, expected, reverse
):
    client = DigitChoices(digits)
    result = jev_numeric.decode_digits(
        client, {}, "value", lower=0, upper=upper, resolution=resolution, reverse=reverse
    )
    assert Decimal(result["value"]) == Decimal(expected)
    assert Decimal(result["upper"]) - Decimal(result["lower"]) == Decimal(str(resolution))
    assert result["calls"] == len(digits)
    for record in client.records:
        question = next(iter(record["request"]["questions"].values()))
        assert list(question["criteria"]) == list("9876543210" if reverse else "0123456789")


@pytest.mark.parametrize(
    "bad",
    [
        {"range": [-10, 10]},
        {"range": [1, 100]},
        {"range": [0, 16]},
        {"range": [0, 0.1]},
        {"resolution": ".02"},
        {"resolution": "NaN"},
        {"resolution": 10},
        {"branching": 2},
        {"branching": True},
        {"method": "unknown"},
    ],
)
def test_invalid_digit_format_is_rejected_before_any_question_is_sent(bad):
    payload = request()
    payload["questions"]["bad"] = request(**bad)["questions"]["price"]
    client = DigitChoices("1175")
    with pytest.raises(ValueError):
        jev_numeric.evaluate(payload, client=client)
    assert client.records == []


def test_digits_rejects_an_unknown_digit_and_insufficient_budget():
    with pytest.raises(ValueError, match="digit"):
        jev_numeric.decode_digits(DigitChoices("x"), {}, "value", lower=0, upper=10)
    client = DigitChoices("1175")
    with pytest.raises(RuntimeError, match="limit"):
        jev_numeric.decode_digits(client, {}, "value", lower=0, upper=100, max_calls=3)
    assert client.records == []


def test_questions_identify_decimal_places_instead_of_ambiguous_character_positions():
    client = DigitChoices("1175")
    jev_numeric.evaluate(request(), client=client)
    for record, place in zip(client.records, ["tens", "units", "tenths", "hundredths"]):
        question = next(iter(record["request"]["questions"].values()))
        assert f"{place} digit" in question["instructions"]
        assert all(f"{place} digit" in description for description in question["criteria"].values())
