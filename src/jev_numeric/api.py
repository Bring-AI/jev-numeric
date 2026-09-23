"""Official-shaped JSON adapter implemented locally over Jev Choice calls."""

import json
import math
from decimal import Decimal, InvalidOperation

from .client import JevClient
from .decoding import bounds, decode_digits, decode_number, digit_layout, estimate_distribution


def _validate(request):
    if not isinstance(request, dict) or set(request) - {"model", "state", "questions"}:
        raise ValueError("Request fields: model (optional), state, questions")
    if "state" not in request:
        raise ValueError("state is required")
    try:
        json.dumps(request["state"], allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("state must be valid JSON with finite numbers") from exc
    model = request.get("model")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ValueError("model must be a nonempty string")
    questions = request.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be a nonempty object")
    for name, q in questions.items():
        if not isinstance(name, str) or not name or not isinstance(q, dict):
            raise ValueError("Each question needs a name and an object")
        kind = q.get("type")
        if kind not in ("number", "distribution"):
            raise ValueError("Question type must be number or distribution")
        allowed = {"type", "instructions", "range"} | (
            {"resolution", "branching", "method"} if kind == "number" else {"bins"}
        )
        if set(q) - allowed:
            raise ValueError(f"Unsupported fields for question {name}")
        if not isinstance(q.get("instructions"), str) or not q["instructions"].strip():
            raise ValueError("instructions must be a nonempty string")
        interval = q.get("range")
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError("range must be [lower, upper]")
        lo, hi = bounds(*interval)
        if not all(math.isfinite(float(x)) for x in (lo, hi)):
            raise ValueError("Range exceeds the finite JSON-number interface")
        if kind == "number":
            try:
                step = Decimal(str(q.get("resolution", ".01")))
            except InvalidOperation as exc:
                raise ValueError("resolution must be positive and finite") from exc
            if not step.is_finite() or step <= 0:
                raise ValueError("resolution must be positive and finite")
            size = (hi - lo) / step
            if size != size.to_integral_value():
                raise ValueError("Range width must be a multiple of resolution")
            branching = q.get("branching", 10)
            if type(branching) is not int or not 2 <= branching <= 255:
                raise ValueError("branching must be an integer in [2,255]")
            method = q.get("method", "interval")
            if method not in ("interval", "digits"):
                raise ValueError("method must be interval or digits")
            if method == "digits":
                digit_layout(lo, hi, step)
                if branching != 10:
                    raise ValueError(
                        "digits uses exactly 10 digit choices; omit branching or use 10"
                    )
        else:
            bins = q.get("bins", 16)
            if type(bins) is not int or not 2 <= bins <= 128:
                raise ValueError("bins must be an integer in [2,128]")
    return model, questions


def evaluate(request, *, client=None, details=False, max_calls=128):
    """Evaluate number/distribution JSON questions. Validate all before paid calls.

    New types belong to this adapter, not the upstream API. Multiple questions are
    evaluated sequentially. details=True includes exact decimals and diagnostics.
    """
    model, questions = _validate(request)
    if client is None:
        with JevClient(model=model, max_calls=max_calls) as owned:
            return evaluate(request, client=owned, details=details, max_calls=max_calls)
    if model is not None and model != client.model:
        raise ValueError("Request model differs from the supplied client model")
    start = len(client.records)
    answers = {}
    for name, q in questions.items():
        lo, hi = q["range"]
        if q["type"] == "number":
            method = q.get("method", "interval")
            decoder = decode_digits if method == "digits" else decode_number
            options = {} if method == "digits" else {"branching": q.get("branching", 10)}
            r = decoder(
                client,
                request["state"],
                q["instructions"],
                lower=lo,
                upper=hi,
                resolution=q.get("resolution", ".01"),
                max_calls=max_calls,
                **options,
            )
            answer = {"type": "number", "value": float(r["value"])}
            if details:
                answer.update(
                    method=method,
                    exact=r["value"],
                    interval=[r["lower"], r["upper"]],
                    resolution=r["resolution"],
                    calls=r["calls"],
                    trace=r["trace"],
                )
        else:
            r = estimate_distribution(
                client,
                request["state"],
                q["instructions"],
                lower=lo,
                upper=hi,
                bins=q.get("bins", 16),
            )
            answer = {
                "type": "distribution",
                "edges": list(map(float, r["edges"])),
                "probabilities": r["masses"],
                "calibrated": False,
                "raw_monotonicity_violations": r["raw_monotonicity_violations"],
            }
            if details:
                answer.update(raw_cdf=r["raw_cdf"], cdf=r["cdf"], exact_edges=r["edges"])
        answers[name] = answer
    served = {record["response"].get("model", client.model) for record in client.records[start:]}
    if len(served) > 1:
        raise ValueError("Upstream model identity changed during the request")
    return {"model": next(iter(served), client.model), "answers": answers}
