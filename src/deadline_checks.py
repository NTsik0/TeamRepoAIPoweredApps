"""Deterministic checks on the model's reading of a deadline photo (docs/confidence-policy.md).

Extract, then verify: the model reads, code decides. decide() is pure: no network, no clock
(today comes in as an argument), no files. That is why it is tested with hand-written
extractions and no model at all.

Routes, best to worst: accepted · confirm · review · rejected.
"""
import re
from dataclasses import dataclass, field
from datetime import date

from src.deadline_extract import FIELDS, DeadlineExtraction

REQUIRED = ("item", "due_date")
HARD_KINDS = ("missing", "no_evidence")
LABEL = {"item": "What is due", "due_date": "Due date", "due_time": "Time", "course": "Course"}


@dataclass
class Decision:
    route: str                                    # accepted, confirm, review, rejected
    flags: list[tuple[str, str]]                  # (kind, field name)
    hard: set[str] = field(default_factory=set)   # fields a human must fill in; never prefilled

    def reasons(self, x: DeadlineExtraction) -> list[str]:
        return [reason_text(kind, name, x) for kind, name in self.flags]


def reason_text(kind: str, name: str, x: DeadlineExtraction) -> str:
    f = getattr(x, name)
    return {
        "missing": f"{LABEL[name]}: not found on the photo",
        "no_evidence": f"{LABEL[name]}: we could not find the text this came from",
        "relative_date": f"Which date is '{f.evidence}'?",
        "low_confidence": f"We think this is {f.value}. Check the photo?",
        "unparseable_date": f"We could not read '{f.value}' as a date. Type it in?",
        "in_the_past": "This date has already passed. Is the year right?",
        "bad_time": "We could not read the time. Type it in?",
    }.get(kind, f"{LABEL[name]}: {kind}")


def parse_date(value: str | None) -> date | None:
    """ISO YYYY-MM-DD only; None instead of raising, so decide() flags instead of crashing."""
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def looks_like_deadline(x: DeadlineExtraction) -> bool:
    return any(getattr(x, n).value is not None or getattr(x, n).evidence is not None
               for n in ("item", "due_date", "due_time"))


def decide(x: DeadlineExtraction, today: date) -> Decision:
    if not looks_like_deadline(x):
        return Decision("rejected", [])
    flags: list[tuple[str, str]] = []
    for name in REQUIRED:
        f = getattr(x, name)
        if f.value is None and f.evidence is None:
            flags.append(("missing", name))
        elif f.value is None:                           # text was read, but it is not a date
            flags.append(("relative_date", name) if name == "due_date" else ("missing", name))
        elif f.evidence is None:                         # evidence before confidence
            flags.append(("no_evidence", name))
        elif f.confidence < 0.6:
            flags.append(("low_confidence", name))
    d = x.due_date
    if d.value is not None and d.evidence is not None:
        parsed = parse_date(d.value)
        if parsed is None:
            flags.append(("unparseable_date", "due_date"))
        elif parsed < today:
            flags.append(("in_the_past", "due_date"))
    t = x.due_time.value
    if t is not None and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t.strip()):
        flags.append(("bad_time", "due_time"))

    hard = {n for k, n in flags if k in HARD_KINDS}
    if hard:
        return Decision("review", flags, hard)
    if flags:
        return Decision("confirm", flags)
    return Decision("accepted", flags)


def for_display(x: DeadlineExtraction, d: Decision) -> dict:
    """What the student or reviewer sees: hard fields are blanked, never prefilled with a guess."""
    out = {}
    for n in FIELDS:
        f = getattr(x, n)
        out[n] = {"value": None if n in d.hard else f.value, "evidence": f.evidence,
                  "flagged": any(name == n for _, name in d.flags), "hard": n in d.hard}
    return out
