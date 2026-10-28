"""The only place that talks to a model. Every call is timed and logged with tokens, cost and latency.

Week 2: OpenRouterClient + call_and_log() for the keyword /ask slice.
Week 4: complete_json() (image optional, so the Lab 3 image feature uses it too) and embed(),
        both logged by log_usage(). COURSEMATE_OFFLINE=1 routes both through src/offline.py:
        no key, no network, no cost. Tests and CI use it; real answers need the real model.
"""
import base64
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import httpx
import numpy as np

from src import offline

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
DEFAULT_MODEL = "google/gemini-3.8-flash"
CHAT_MODEL = os.environ.get("COURSEMATE_MODEL", DEFAULT_MODEL)
EMBED_MODEL = os.environ.get("COURSEMATE_EMBED_MODEL", "openai/text-embedding-3-small")
USAGE_LOG = Path(os.environ.get("COURSEMATE_LOG_PATH", "logs/usage.jsonl"))
OFFLINE = os.environ.get("COURSEMATE_OFFLINE") == "1"

# USD per million tokens (input, output). Same prices as the course reference (13 October 2026);
# gemini-3.8-flash is on a promotional price. Re-check on openrouter.ai before trusting a cost.
PRICES = {
    "google/gemini-3.8-flash": (0.75, 3.75),
    "openai/text-embedding-3-small": (0.02, 0.0),
    offline.MODEL: (0.0, 0.0),
}


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    """Unknown models log a cost of 0.0 rather than crashing the call."""
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 6)


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
        "cost_usd": cost_usd(client.model, result.prompt_tokens, result.completion_tokens),
        "latency_ms": latency_ms,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return result


# --- Week 4 ------------------------------------------------------------------

def _key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set; export it in your shell")
    return key


def data_url(image: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii")


def log_usage(model: str, tokens_in: int, tokens_out: int, latency_ms: int, kind: str = "chat") -> dict:
    """One line per model call: the log-entry half of the Evidence Rule."""
    line = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        "model": model,
        "prompt_tokens": tokens_in,          # includes image tokens when there is an image
        "completion_tokens": tokens_out,
        "cost_usd": cost_usd(model, tokens_in, tokens_out),
        "latency_ms": latency_ms,
    }
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with USAGE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    if os.environ.get("COURSEMATE_VERBOSE") == "1":
        print(json.dumps(line), file=sys.stderr)
    return line


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def complete_json(prompt: str, image: bytes | None = None, schema: dict | None = None,
                  max_tokens: int = 1500) -> dict:
    """Ask for JSON in a fixed shape. `image` is optional: Lab 3 sends one, Lab 4 does not."""
    if OFFLINE:
        t0 = time.perf_counter()
        out, tokens_in, tokens_out = offline.complete_json(prompt)
        log_usage(offline.MODEL, tokens_in, tokens_out, _ms(t0))
        return out
    content = [{"type": "text", "text": prompt}]
    if image is not None:
        content.append({"type": "image_url", "image_url": {"url": data_url(image)}})
    body = {"model": CHAT_MODEL, "messages": [{"role": "user", "content": content}],
            "temperature": 0, "max_tokens": max_tokens, "reasoning": {"effort": "low"},
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "reply", "schema": schema or {}, "strict": True}}}
    t0 = time.perf_counter()
    r = httpx.post(OPENROUTER_URL, headers={"Authorization": f"Bearer {_key()}"}, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    usage = data.get("usage") or {}
    log_usage(data.get("model") or CHAT_MODEL, int(usage.get("prompt_tokens", 0)),
              int(usage.get("completion_tokens", 0)), _ms(t0))
    choice = data["choices"][0]
    if choice.get("finish_reason") == "length":
        raise RuntimeError(f"answer cut off at max_tokens={max_tokens}")
    return json.loads(choice["message"]["content"])


def embed(texts: list[str]) -> np.ndarray:
    """Texts in, unit-length vectors out, so a dot product is the cosine similarity."""
    if OFFLINE:
        t0 = time.perf_counter()
        v, tokens = offline.embed(texts)
        log_usage(offline.MODEL, tokens, 0, _ms(t0), kind="embed")
        return v
    t0 = time.perf_counter()
    r = httpx.post(OPENROUTER_EMBED_URL, headers={"Authorization": f"Bearer {_key()}"},
                   json={"model": EMBED_MODEL, "input": texts}, timeout=60)
    r.raise_for_status()
    data = r.json()
    usage = data.get("usage") or {}
    log_usage(data.get("model") or EMBED_MODEL, int(usage.get("prompt_tokens", 0)), 0, _ms(t0), kind="embed")
    v = np.array([d["embedding"] for d in data["data"]], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def embed_model_name() -> str:
    """The model the index was (or will be) built with. Index and queries must match."""
    return offline.MODEL if OFFLINE else EMBED_MODEL


# --- Week 5 · function calling -----------------------------------------------

def complete_tools(messages: list[dict], tools: list[dict], max_tokens: int = 1500) -> dict:
    """One model turn that may ask for tools. Returns {content, tool_calls, reasoning_details};
    each tool call is {id, name, arguments (a JSON string)}. Logged like every other call.
    The model only ASKS for a tool: src/act.py decides whether it runs."""
    if OFFLINE:
        t0 = time.perf_counter()
        msg, tokens_in, tokens_out = offline.complete_tools(messages, tools)
        log_usage(offline.MODEL, tokens_in, tokens_out, _ms(t0), kind="tools")
        return msg
    body = {"model": CHAT_MODEL, "messages": messages, "tools": tools, "tool_choice": "auto",
            "temperature": 0, "max_tokens": max_tokens, "reasoning": {"effort": "low"}}
    t0 = time.perf_counter()
    r = httpx.post(OPENROUTER_URL, headers={"Authorization": f"Bearer {_key()}"}, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    usage = data.get("usage") or {}
    log_usage(data.get("model") or CHAT_MODEL, int(usage.get("prompt_tokens", 0)),
              int(usage.get("completion_tokens", 0)), _ms(t0), kind="tools")
    m = data["choices"][0]["message"]
    calls = [{"id": c["id"], "name": c["function"]["name"], "arguments": c["function"].get("arguments") or "{}"}
             for c in (m.get("tool_calls") or [])]
    return {"content": m.get("content"), "tool_calls": calls, "reasoning_details": m.get("reasoning_details")}
