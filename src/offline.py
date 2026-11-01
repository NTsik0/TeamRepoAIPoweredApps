"""Offline stand-ins for the two model calls, used when COURSEMATE_OFFLINE=1.

They let tests and CI run with no key, no network and no cost. They are deliberately simple
and they are NOT a model:

  embed()          hashes character trigrams into 512 numbers. It catches typos and shared
                   words ("wen is hw1 due" still lands near "HW1 ... Due"). It does not
                   understand meaning: "penalty" and "minus" are unrelated to it.
  complete_json()  reads the SOURCES block of a grounded-answer prompt and copies the
                   sentences of the sources that share most of the question's words. If none
                   do, it answers grounded=false. It never writes anything new.

Golden-set numbers from offline mode measure retrieval and the citation checks, not answer
quality. Run the golden set live before trusting a number.
"""
from __future__ import annotations

import hashlib
import json
import re

import numpy as np

MODEL = "offline/trigram-hash"
DIMS = 512

STOP = set("""a an and are as at be by can do does for from has have how i if in is it me my
of on or the there this to was what when where which who will with you your our we any about
after before into than that then them they these those up""".split())


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def _vector(text: str) -> np.ndarray:
    v = np.zeros(DIMS, dtype=np.float32)
    for w in words(text):
        padded = f" {w} "
        for i in range(len(padded) - 2):
            h = int(hashlib.md5(padded[i:i + 3].encode()).hexdigest(), 16)
            v[h % DIMS] += 1.0
    n = np.linalg.norm(v)
    return v / n if n else v


def embed(texts: list[str]) -> tuple[np.ndarray, int]:
    """Vectors, plus a rough token count for the usage log."""
    return np.stack([_vector(t) for t in texts]), sum(len(t.split()) for t in texts)


_SOURCE = re.compile(r"^\[(\d+)\] (.*?)\n(.*?)(?=^\[\d+\] |\Z)", re.S | re.M)


def stems(text: str) -> set[str]:
    """Crude stemming: the first four letters. 'submit', 'submission' and 'submitted' meet."""
    return {w[:4] for w in words(text)}


def complete_json(prompt: str) -> tuple[dict, int, int]:
    """An extractive stand-in for the answering model: (reply, tokens_in, tokens_out)."""
    head, question = prompt.split("QUESTION:", 1)
    q = stems(question)
    cited, parts = [], []
    for n, header, body in _SOURCE.findall(head):
        overlap = len(q & stems(header + " " + body)) / max(1, len(q))
        if overlap >= 0.6 and len(cited) < 2:
            sentences = [s for s in re.split(r"(?<=[.!?])\s+", " ".join(body.split())) if s]
            ranked = sorted(sentences, key=lambda s: -len(q & stems(s)))[:2]
            cited.append(int(n))
            parts += [f"{s.rstrip('.')} [{n}]." for s in sentences if s in ranked]
    out = ({"answer": " ".join(parts), "citations": cited, "grounded": True} if cited else
           {"answer": "The sources do not say.", "citations": [], "grounded": False})
    return out, len(prompt.split()), len(out["answer"].split())


# --- Week 5 · a stand-in for function calling ---------------------------------

_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_REMIND = re.compile(r"remind me (?:about|of|for) (.+?)(?:,| due| on| by)\s", re.I)
_DAYS = re.compile(r"\b([1-9]) days? before\b", re.I)


def _say(result: dict) -> str:
    if "error" in result:
        return f"I couldn't do that: {result['error']}"
    if result.get("status") == "already saved":
        return f"You already have a reminder for {result['title']} on {result['remind_on']}."
    return f"Saved: I'll remind you about {result['title']} (due {result['due']}) on {result['remind_on']}."


def complete_tools(messages: list[dict], tools: list[dict]) -> tuple[dict, int, int]:
    """A rule-based stand-in for a tool-calling model: (message, tokens_in, tokens_out).
    It asks for save_reminder when the question says 'remind me about X due YYYY-MM-DD',
    and turns tool results into a sentence. It is NOT a model; it never decides anything new."""
    names = {t["function"]["name"] for t in tools}
    last_user = max(i for i, m in enumerate(messages) if m["role"] == "user")
    q = messages[last_user]["content"]
    results = [json.loads(m["content"]) for m in messages[last_user + 1:] if m["role"] == "tool"]
    call = None
    if results:
        content = " ".join(_say(r) for r in results)
    else:
        content = None
        title, due = _REMIND.search(q + " "), _DATE.search(q)
        if title and due:
            if "save_reminder" in names:
                args = {"course": "cs6920", "title": title.group(1).strip(), "due": due.group(1)}
                if _DAYS.search(q):
                    args["days_before"] = int(_DAYS.search(q).group(1))
                call = ("save_reminder", args)
            else:
                content = "Please sign in first: I can only save reminders for a signed-in student."
        else:
            content = "I can save a reminder for a course deadline. Tell me what is due and the date."
    calls = [] if call is None else [{"id": f"call_{len(messages)}", "name": call[0],
                                      "arguments": json.dumps(call[1])}]
    out = {"content": content, "tool_calls": calls, "reasoning_details": None}
    tokens_in = sum(len(str(m.get("content") or "").split()) for m in messages) + 40 * len(tools)
    return out, tokens_in, len((content or json.dumps(calls)).split())


# --- Week 6 · a stand-in for streaming ------------------------------------------

def stream(messages: list[dict], tools: list[dict]):
    """Yields (delta, usage) pairs shaped like OpenRouter's stream chunks: text word by word,
    a tool call in fragments (id and name first, then the arguments in pieces), usage last."""
    msg, tokens_in, tokens_out = complete_tools(messages, tools)
    for call in msg["tool_calls"]:
        yield {"tool_calls": [{"index": 0, "id": call["id"], "function": {"name": call["name"], "arguments": ""}}]}, None
        args = call["arguments"]
        for i in range(0, len(args), 8):
            yield {"tool_calls": [{"index": 0, "function": {"arguments": args[i:i + 8]}}]}, None
    if msg["content"]:
        words = msg["content"].split(" ")
        for i, w in enumerate(words):
            yield {"content": w + (" " if i < len(words) - 1 else "")}, None
    yield None, {"prompt_tokens": tokens_in, "completion_tokens": tokens_out}
