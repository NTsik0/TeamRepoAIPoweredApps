"""The only place that talks to a model. Every call is timed and logged (AC4)."""
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3.8-flash"


@dataclass(frozen=True)
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int


class LLMClient(Protocol):
    model: str

    def complete(self, messages: list[dict], max_tokens: int) -> LLMResult: ...


class OpenRouterClient:
    def __init__(self, model: str | None = None, timeout: float = 20.0):
        self.model = model or os.environ.get("COURSEMATE_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def complete(self, messages: list[dict], max_tokens: int) -> LLMResult:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        r = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {key}"},
            json={"model": self.model, "messages": messages, "max_tokens": max_tokens},
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") or {}
        return LLMResult(
            text=data["choices"][0]["message"]["content"].strip(),
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )


def call_and_log(client: LLMClient, messages: list[dict], max_tokens: int,
                 course_id: str, log_path: Path) -> LLMResult:
    """Call the model and append one usage line. Never logs the question or the key."""
    start = time.perf_counter()
    result = client.complete(messages, max_tokens)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "course_id": course_id,
        "model": client.model,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "latency_ms": latency_ms,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return result
