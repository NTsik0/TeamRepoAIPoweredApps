"""The only file that talks to a model. Every call writes one usage line: tokens, cost, latency."""
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3.8-flash"

# USD per million tokens (input, output). Same prices as the course reference llm.py;
# re-check at openrouter.ai/models before trusting a cost figure.
PRICES = {
    "google/gemini-3.8-flash": (0.75, 3.75),
}


@dataclass(frozen=True)
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int


class DeadlineError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Unknown models cost 0.0 in the log rather than crashing the call."""
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return round((prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000, 6)


class OpenRouterClient:
    def __init__(self):
        self.model = os.environ.get("COURSEMATE_MODEL", DEFAULT_MODEL)

    def complete(self, messages: list[dict], max_tokens: int) -> LLMResult:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise DeadlineError("model_error", "OPENROUTER_API_KEY is not set")
        try:
            r = httpx.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": self.model, "messages": messages, "max_tokens": max_tokens,
                      "response_format": {"type": "json_object"},
                      "reasoning": {"effort": "low"}},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise DeadlineError("model_error", f"model call failed: {type(e).__name__}") from None
        choice = data["choices"][0]
        if choice.get("finish_reason") == "length":
            raise DeadlineError("model_bad_output",
                                f"answer cut off at max_tokens={max_tokens} (finish_reason=length)")
        usage = data.get("usage") or {}
        return LLMResult(choice["message"]["content"] or "",
                         int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)))


def call_and_log(client, messages, max_tokens: int, course_id: str, log_path: Path) -> LLMResult:
    """One model call, one usage line (AC4). Never logs the prompt or the key."""
    start = time.perf_counter()
    result = client.complete(messages, max_tokens)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "course_id": course_id,
        "model": client.model,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "cost_usd": cost_usd(client.model, result.prompt_tokens, result.completion_tokens),
        "latency_ms": round((time.perf_counter() - start) * 1000, 1),
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return result
