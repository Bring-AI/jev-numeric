"""Minimal Jev transport; API credentials are never included in saved records."""

import math
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


def settings():
    load_dotenv()
    gateway = os.getenv("JEV_GATEWAY", "auto")
    if gateway == "auto":
        gateway = (
            "openrouter"
            if (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY_FILE"))
            else "typesafe"
        )
    if gateway not in ("openrouter", "typesafe"):
        raise ValueError("JEV_GATEWAY must be openrouter, typesafe, or auto")
    prefix = gateway.upper()
    key = os.getenv(prefix + "_API_KEY", "")
    if not key and os.getenv(prefix + "_API_KEY_FILE"):
        key = Path(os.environ[prefix + "_API_KEY_FILE"]).expanduser().read_text().strip()
    if not key:
        raise ValueError(f"Set {prefix}_API_KEY or {prefix}_API_KEY_FILE")
    base = os.getenv(prefix + "_BASE_URL") or (
        "https://openrouter.ai/api/v1" if gateway == "openrouter" else "https://api.typesafe.ai/v1"
    )
    if not base.startswith("https://"):
        raise ValueError("Use an HTTPS endpoint")
    model = os.getenv(prefix + "_MODEL") or (
        "typesafe/jev-1.13-20260917" if gateway == "openrouter" else "jev-latest"
    )
    return gateway, key, base, model


class JevClient:
    def __init__(self, *, max_calls=256):
        self.gateway, self._key, base, self.model = settings()
        self._url = base.rstrip("/") + "/systemone"
        self._http = httpx.Client(timeout=60, follow_redirects=False)
        self.max_calls = max_calls
        self.records = []
        self.calls = 0

    def ask(self, state, questions):
        if self.calls >= self.max_calls:
            raise RuntimeError("API call budget exhausted")
        self.calls += 1
        payload = {"model": self.model, "state": state, "questions": questions}
        response = self._http.post(
            self._url, headers={"Authorization": "Bearer " + self._key}, json=payload
        )
        if response.status_code != 200:
            raise RuntimeError(f"Jev returned HTTP {response.status_code}; no automatic retry")
        data = response.json()
        answers = data["answers"]
        if set(answers) != set(questions):
            raise ValueError("Response question ids do not match request")
        for name, answer in answers.items():
            criteria = questions[name]["criteria"]
            probs = answer["probabilities"]
            if (
                answer.get("type") != "choice"
                or answer.get("choice") not in criteria
                or set(probs) != set(criteria)
            ):
                raise ValueError("Invalid choice response")
            vals = list(probs.values())
            if (
                any(not math.isfinite(p) or not 0 <= p <= 1 for p in vals)
                or abs(sum(vals) - 1) > len(vals) * 0.005 + 0.001
            ):
                raise ValueError("Invalid probability mass")
        self.records.append({"request": payload, "response": data})
        return data

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
