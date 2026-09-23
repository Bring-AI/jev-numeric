"""Finite-grid numerical interfaces over a structured Choice oracle."""

import math
from decimal import Decimal, InvalidOperation


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
