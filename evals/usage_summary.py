"""Summarise logs/usage.jsonl and logs/answers.jsonl into numbers for the Design Review.

    python -m evals.usage_summary            prints the table and writes evals/results/usage-<timestamp>.json

Cost and latency come from the usage log (one line per model call); requests come from the
answer log (one line per answer or refusal). Only live lines count: offline lines cost nothing.
"""
from __future__ import annotations

import json
import os
import statistics
from datetime import datetime
from pathlib import Path

USAGE = Path(os.environ.get("COURSEMATE_LOG_PATH", "logs/usage.jsonl"))
ANSWERS = Path(os.environ.get("COURSEMATE_ANSWER_LOG", "logs/answers.jsonl"))
RESULTS = Path("evals/results")


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))]


def summarise() -> dict:
    usage = [u for u in read(USAGE) if not u.get("model", "").startswith("offline/")]
    chats = [u for u in usage if u.get("kind", "chat") == "chat"]
    embeds = [u for u in usage if u.get("kind") == "embed"]
    answers = read(ANSWERS)
    answered = [a for a in answers if a["status"] == "answered"]
    out = {
        "model_calls": len(usage),
        "chat_calls": len(chats),
        "embed_calls": len(embeds),
        "requests_logged": len(answers),
        "answered": len(answered),
        "refused": len(answers) - len(answered),
        "total_cost_usd": round(sum(u.get("cost_usd", 0) for u in usage), 6),
        "avg_chat_cost_usd": round(statistics.mean([u.get("cost_usd", 0) for u in chats]), 6) if chats else 0.0,
        "avg_prompt_tokens": round(statistics.mean([u["prompt_tokens"] for u in chats])) if chats else 0,
        "avg_completion_tokens": round(statistics.mean([u["completion_tokens"] for u in chats])) if chats else 0,
        "chat_latency_ms_p50": statistics.median([u["latency_ms"] for u in chats]) if chats else 0,
        "chat_latency_ms_p95": p95([u["latency_ms"] for u in chats]),
    }
    return out


if __name__ == "__main__":
    s = summarise()
    for k, v in s.items():
        print(f"{k:<24} {v}")
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"usage-{datetime.now().strftime('%Y-%m-%d-%H%M')}.json"
    path.write_text(json.dumps(s, indent=1), encoding="utf-8")
    print(f"\nwritten to {path}")
