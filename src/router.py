"""The fallback chain (Week 8, Lab 8). From Lab-8/templates/router_starter.py; the decisions behind
every setting are in docs/fallback-plan.md. The Lab 7 loop (POST /plan) runs through complete().

Three ideas, and nothing else:
  the chain   for each kind of job, an ordered list of models. Ask the first; if it cannot
              answer, ask the next. The last link is a sentence you wrote, not a model.
  the limit   one model gets TIMEOUT_S seconds. Slow counts as down.
  the cache   the same question inside CACHE_TTL_S seconds is answered from memory, for free.

Every call writes one line to logs/router.jsonl. `python -m src.router` prints the summary
you paste into docs/measurements.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ADAPT 0: our one model call. complete_tools() takes (messages, tools, timeout=..., model=...)
# since Week 8 and returns {"content", "tool_calls", "reasoning_details", "usage"}.
from src.llm import complete_tools

CHAINS = {                                      # ADAPT 1: per job, who answers, in order. Two companies.
    "chat": ["google/gemini-3.8-flash", "anthropic/claude-haiku-5.5"],   # plan line 2
}
TIMEOUT_S = 15                                  # ADAPT 2: plan line 3, just above our measured p95 of 14.1 s
CACHE_TTL_S = 600                               # ADAPT 3: plan line 4, a corrected course document must show within 10 min
SORRY = "CourseMate cannot reach its models right now. No reminder was saved. Please try again in a minute."   # plan line 5

CACHE: dict[str, tuple[float, dict]] = {}       # key -> (when, answer). A dict is enough for today.
LOG = Path(os.environ.get("COURSEMATE_ROUTER_LOG", "logs/router.jsonl"))


def temporary(error: Exception) -> bool:
    """Is the next model worth a try? A timeout, a dropped connection, a 429 or a 5xx: yes.
    A 400, 401 or 403 is our own bug. Another model will not fix it, so it is raised.
    ADAPT (ours): complete_tools() uses httpx, not the OpenAI SDK. httpx puts the status on
    error.response and calls a refused connection ConnectError, so the starter's check missed both."""
    name = type(error).__name__
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
    else:
        status = getattr(error, "status_code", None)
    return ("Timeout" in name or "Connection" in name
            or isinstance(error, (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError))
            or status in (408, 429, 500, 502, 503, 504))


def complete(messages: list[dict], tools: list[dict] | None = None, job: str = "chat", call=complete_tools) -> dict:
    key = hashlib.sha256(json.dumps([job, messages], sort_keys=True).encode()).hexdigest()
    saved = CACHE.get(key)
    if saved and not tools and time.time() - saved[0] < CACHE_TTL_S:      # THE CACHE: seen it, still fresh
        return note(job, "cache", saved[1], saved_usd=cost(saved[1]))
    for place, model in enumerate(CHAINS[job], start=1):                  # THE CHAIN: first, then next
        started = time.perf_counter()
        try:
            answer = call(messages, tools or [], timeout=TIMEOUT_S, model=model)      # THE LIMIT
        except Exception as error:
            if not temporary(error):
                raise                                                     # our bug: fail loudly
            note(job, "failed", model=model, place=place, why=type(error).__name__)
            continue                                                      # their outage: next model
        if not tools:
            CACHE[key] = (time.time(), answer)                            # only plain answers are reused
        return note(job, "ok", answer, model=model, place=place, cost_usd=cost(answer),
                    ms=int((time.perf_counter() - started) * 1000))
    return note(job, "exhausted", {"content": SORRY, "tool_calls": [], "degraded": True})


def cost(answer: dict) -> float:
    return (answer.get("usage") or {}).get("cost_usd", 0.0)


def note(job: str, outcome: str, answer: dict | None = None, **fields) -> dict | None:
    """One line per attempt. This file is the evidence for the before/after table."""
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),     # AGENTS.md: UTC ISO 8601
                            "job": job, "outcome": outcome, **fields}) + "\n")
    return answer


def summary(path: Path | None = None) -> dict:
    """Read the log, count what happened. `python -m src.router` prints it."""
    path = path or LOG
    lines = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    count = lambda outcome: sum(1 for x in lines if x["outcome"] == outcome)      # noqa: E731
    ok = sorted(x["ms"] for x in lines if x["outcome"] == "ok")
    return {"requests": count("ok") + count("cache") + count("exhausted"),
            "answered_by_first_model": sum(1 for x in lines if x["outcome"] == "ok" and x["place"] == 1),
            "answered_by_a_fallback": sum(1 for x in lines if x["outcome"] == "ok" and x["place"] > 1),
            "answered_from_cache": count("cache"),
            "sorry_message": count("exhausted"),
            "failed_attempts": count("failed"),
            "median_ms": ok[len(ok) // 2] if ok else None,
            "spent_usd": round(sum(x.get("cost_usd", 0) for x in lines), 6),
            "saved_by_cache_usd": round(sum(x.get("saved_usd", 0) for x in lines), 6)}


if __name__ == "__main__":
    for name, value in summary().items():
        print(f"{name:<26} {value}")
