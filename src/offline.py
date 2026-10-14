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
