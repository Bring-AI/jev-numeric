"""Finite-grid numerical interfaces over a structured Choice oracle."""

import math
from decimal import Decimal, InvalidOperation, localcontext


def bounds(lower, upper):
    try:
        lo, hi = Decimal(str(lower)), Decimal(str(upper))
    except InvalidOperation as exc:
        raise ValueError("Bounds must be finite decimal numbers") from exc
    if not lo.is_finite() or not hi.is_finite() or hi <= lo:
        raise ValueError("Require finite lower < upper")
    return lo, hi


def decode_number(
    client,
    state,
    target,
    *,
    lower,
    upper,
    resolution="0.01",
    branching=10,
    reverse=False,
    max_calls=128,
):
    """Greedily locate a value in [lower, upper). Return its bin's lower endpoint.

    Resolution is representational precision, not an accuracy guarantee. The caller
    must supply a containing range. No escape branch or automatic range expansion.
    """
    lo, hi = bounds(lower, upper)
    try:
        step = Decimal(str(resolution))
    except InvalidOperation as exc:
        raise ValueError("Resolution must be a finite positive decimal") from exc
    if not step.is_finite() or step <= 0:
        raise ValueError("Resolution must be finite and positive")
    size = (hi - lo) / step
    if size != size.to_integral_value():
        raise ValueError("Range width must be an integer multiple of resolution")
    if not isinstance(branching, int) or not 2 <= branching <= 255:
        raise ValueError("branching must be an integer in [2,255]")
    left, right = 0, int(size)
    trace = []
    while right - left > 1:
        if len(trace) >= max_calls:
            raise RuntimeError("Call limit reached before requested resolution")
        n = min(branching, right - left)
        cuts = [left + (right - left) * i // n for i in range(n + 1)]
        criteria = {
            str(i): f"{lo + step * cuts[i]} <= value < {lo + step * cuts[i + 1]}" for i in range(n)
        }
        if reverse:
            criteria = dict(reversed(list(criteria.items())))
        q = {
            "type": "choice",
            "instructions": f"Determine {target} using the state. Select the interval containing this numerical value. "
            "Include the lower bound; exclude the upper bound. Option labels identify intervals, "
            "not the value itself.",
            "criteria": criteria,
        }
        answer = client.ask(state, {"number": q})["answers"]["number"]
        label = answer["choice"]
        if label not in criteria:
            raise ValueError("Oracle selected an unknown interval")
        i = int(label)
        left, right = cuts[i], cuts[i + 1]
        trace.append(
            {
                "lower": str(lo + step * left),
                "upper": str(lo + step * right),
                "choice": label,
                "probabilities": answer.get("probabilities", {}),
            }
        )
    return {
        "value": str(lo + step * left),
        "lower": str(lo + step * left),
        "upper": str(lo + step * right),
        "resolution": str(step),
        "calls": len(trace),
        "branching": branching,
        "trace": trace,
    }


def digit_layout(lower, upper, resolution):
    """Validate the direct decimal format: [0, 10**n), step 10**-d, n,d >= 0."""
    lo, hi = bounds(lower, upper)
    try:
        step = Decimal(str(resolution))
    except InvalidOperation as exc:
        raise ValueError("digits resolution must be a nonpositive power of ten") from exc
    if lo != 0 or hi < 1:
        raise ValueError("digits requires range [0, 10**n), with integer n >= 0")
    if not step.is_finite() or not 0 < step <= 1:
        raise ValueError("digits resolution must be a nonpositive power of ten")
    exponents = []
    for value in (hi, step):
        parts = value.as_tuple()
        if parts.digits[0] != 1 or any(parts.digits[1:]):
            raise ValueError("digits upper bound and resolution must be powers of ten")
        exponents.append(parts.exponent + len(parts.digits) - 1)
    return exponents[0], -exponents[1]


def decode_digits(
    client, state, target, *, lower, upper, resolution="0.01", reverse=False, max_calls=128
):
    """Select decimal digits through Choice, preserving the prefix. No logits needed.

    Supports [0, 10**n) at resolution 10**-d for nonnegative integers n,d.
    The fixed decimal point is inserted locally; leading/trailing zeros are retained
    in the prefix. Truncation gives the same lower-endpoint grid as interval decoding.
    """
    integer_digits, decimal_places = digit_layout(lower, upper, resolution)
    total = integer_digits + decimal_places
    if type(max_calls) is not int or max_calls < 0:
        raise ValueError("max_calls must be a nonnegative integer")
    if total > max_calls:
        raise RuntimeError("Call limit is too small for the requested decimal format")
    digits, trace = "", []
    prefix = "" if integer_digits else ("0." if decimal_places else "0")
    with localcontext() as context:
        context.prec = max(context.prec, total + 2)
        step = Decimal(1).scaleb(-decimal_places)
        value = Decimal(0).quantize(step)
        for position in range(total):
            exponent = integer_digits - position - 1
            place = {
                3: "thousands",
                2: "hundreds",
                1: "tens",
                0: "units",
                -1: "tenths",
                -2: "hundredths",
                -3: "thousandths",
            }.get(exponent, f"10^{exponent} place")
            criteria = {str(i): f"The {place} digit is {i}." for i in range(10)}
            if reverse:
                criteria = dict(reversed(list(criteria.items())))
            instructions = (
                f"Determine {target} using the state. The value is in [0, {upper}). "
                f"Write it in decimal with exactly {max(integer_digits, 1)} integer digits "
                f"and {decimal_places} digits after the decimal point. "
                "Pad with leading and trailing zeros as needed. Truncate extra fractional "
                "digits; do not round. Do not use scientific notation. "
            )
            if exponent >= 0:
                instructions += (
                    f"Select the {place} digit (integer place value {Decimal(1).scaleb(exponent)}). "
                    "Count integer positions from the units digit, moving left. "
                    "If this leading position is absent, its digit is 0. "
                )
            else:
                instructions += (
                    f"Select the {place} digit: decimal digit d{-exponent}, "
                    "counting after the decimal point. "
                )
            instructions += (
                f'Previously selected prefix: "{prefix}". '
                "The prefix is a previous prediction, not a new numerical input. "
                "Compute the value from the original state and select the requested digit. "
                "Each option names the digit itself, not the whole numerical answer."
            )
            question = {"type": "choice", "instructions": instructions, "criteria": criteria}
            answer = client.ask(state, {"number": question})["answers"]["number"]
            label = answer["choice"]
            if label not in criteria:
                raise ValueError("Oracle selected an unknown decimal digit")
            digits += label
            prefix += label
            if len(digits) == integer_digits and decimal_places:
                prefix += "."
            width = Decimal(1).scaleb(integer_digits - len(digits))
            value = Decimal(int(digits)) * width
            trace.append(
                {
                    "position": position + 1,
                    "prefix": prefix,
                    "choice": label,
                    "lower": str(value),
                    "upper": str(value + width),
                    "probabilities": answer.get("probabilities", {}),
                }
            )
        return {
            "value": str(value),
            "lower": str(value),
            "upper": str(value + step),
            "resolution": str(step),
            "calls": len(trace),
            "branching": 10,
            "trace": trace,
        }


def isotonic(values):
    blocks = []
    for p in values:
        blocks.append((p, 1))
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            b, a = blocks.pop(), blocks.pop()
            blocks.append(((a[0] * a[1] + b[0] * b[1]) / (a[1] + b[1]), a[1] + b[1]))
    return [p for p, n in blocks for _ in range(n)]


def estimate_distribution(client, state, target, *, lower, upper, bins=16):
    """Experimental threshold CDF -> isotonic CDF -> finite histogram.

    Assumes the variable lies in (lower, upper]. Bins are right-closed. Calibration
    and correctness are NOT guaranteed. A midpoint rule yields an approximate mean.
    """
    lo, hi = bounds(lower, upper)
    if not isinstance(bins, int) or not 2 <= bins <= 128:
        raise ValueError("bins must be an integer in [2,128]")
    edges = [lo + (hi - lo) * i / bins for i in range(bins + 1)]
    questions = {
        f"cdf_{i}": {
            "type": "choice",
            "instructions": f"For {target}, given the state, is the value <= {t}? Equality counts as yes.",
            "criteria": {"yes": f"value <= {t}", "no": f"value > {t}"},
        }
        for i, t in enumerate(edges[1:-1])
    }
    answers = client.ask(state, questions)["answers"]
    raw = []
    for k in questions:
        p = answers[k]["probabilities"]
        vals = [float(p[s]) for s in ("yes", "no")]
        if any(not math.isfinite(v) or not 0 <= v <= 1 for v in vals) or sum(vals) <= 0:
            raise ValueError("Invalid threshold probabilities")
        raw.append(vals[0] / sum(vals))
    cdf = isotonic(raw)
    masses = [b - a for a, b in zip([0] + cdf, cdf + [1])]
    return {
        "edges": list(map(str, edges)),
        "raw_cdf": raw,
        "cdf": cdf,
        "masses": masses,
        "raw_monotonicity_violations": sum(a > b for a, b in zip(raw, raw[1:])),
        "mean_midpoint_approximation": sum(
            float((a + b) / 2) * p for a, b, p in zip(edges, edges[1:], masses)
        ),
        "calibrated": False,
    }
