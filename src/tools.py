"""CourseMate's tools: the code that acts, behind the contracts in src/contracts.py (Week 5).

Three tools: save_reminder (Lab 5) only adds; find_deadlines (HW2, NTsik0) and search_course_docs (HW2, Gaaa-3)
only read. Nothing here deletes, edits another student's data, or sends a message: that is the least-privilege
decision, made by what we chose NOT to build.

Every tool takes a validated contract object (never raw model output) and returns a pydantic
result. A failure we expected raises ToolFailure with a message written for the model to read
and act on. Anything else is a bug and is allowed to crash.

Reminders live in the Week 6 memory store (src/memory.py, docs/state-contract.md), keyed by a
hash of the student id, never the id itself, and expire the day after their due date.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Callable, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from src import answer as grounded
from src import index as course_index
from src import memory
from src.chunk import load_corpus
from src.contracts import Contract, FindDeadlines, SaveReminder, SearchCourseDocs
from src.courses import load_course
from src.search import hybrid

TBILISI = ZoneInfo("Asia/Tbilisi")
MAX_REMINDERS = memory.MAX_REMINDERS   # per student, enforced in src/memory.py
MAX_DAYS_AHEAD = 180        # about one semester
CORPUS = Path("data/corpus")
MAX_SECTION_CHARS = 600     # about 150 tokens: enough to answer from, small enough for three of them


class ToolFailure(Exception):
    """An expected failure. The message goes back to the model, so make it say what to do next."""


def today() -> date:
    """Today in Tbilisi. COURSEMATE_TODAY pins it for tests."""
    pinned = os.environ.get("COURSEMATE_TODAY")
    return date.fromisoformat(pinned) if pinned else datetime.now(TBILISI).date()


def student_key(student: str) -> str:
    """We store and log a hash of the student id, not the id itself."""
    return hashlib.sha256(student.encode()).hexdigest()[:12]


# ---------------------------------------------------------------- results

class ReminderResult(BaseModel):
    course: str
    title: str
    due: date
    remind_on: date
    status: Literal["saved", "already saved"]
    reminders: int             # how many reminders this student now has


# ---------------------------------------------------------------- save_reminder

def save_reminder(args: SaveReminder, *, student: str) -> ReminderResult:
    now = today()
    if args.due < now:
        raise ToolFailure(f"That deadline ({args.due.isoformat()}) has already passed. "
                          "Ask the student for the right date from the course document.")
    if args.due > now + timedelta(days=MAX_DAYS_AHEAD):
        raise ToolFailure(f"{args.due.isoformat()} is more than {MAX_DAYS_AHEAD} days away, outside this "
                          "semester. Check the date in the course document.")

    remind_on = max(now, args.due - timedelta(days=args.days_before))
    key = student_key(student)
    try:
        status, count = memory.add_reminder(key, memory.Reminder(
            course=args.course, title=args.title, due=args.due.isoformat(), remind_on=remind_on.isoformat()))
    except OverflowError:
        raise ToolFailure(f"You already have {MAX_REMINDERS} saved reminders, the most allowed. Nothing was saved.")
    if status == "already saved":
        stored = next(r for r in memory.reminders(key) if r.course == args.course and r.due == args.due.isoformat()
                      and r.title.casefold() == args.title.casefold())
        return ReminderResult(course=stored.course, title=stored.title, due=args.due,
                              remind_on=date.fromisoformat(stored.remind_on), status=status, reminders=count)
    return ReminderResult(course=args.course, title=args.title, due=args.due, remind_on=remind_on,
                          status=status, reminders=count)


# ---------------------------------------------------------------- find_deadlines

_DEADLINE = re.compile(r"\bdue\b|\bdeadline\b|23:59", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class Deadline(BaseModel):
    section: str               # the '## ' heading the sentence is under
    quote: str                 # the sentence, word for word (line breaks become spaces)


class DeadlineList(BaseModel):
    course: str
    deadlines: list[Deadline]
    total: int                 # how many matched, before the limit


def find_deadlines(args: FindDeadlines) -> DeadlineList:
    """Every sentence in data/courses/<course>.md that states a deadline. No model: the quotes
    are copied from the document, so a date cannot be invented."""
    sections = load_course(args.course)
    if not sections:
        raise ToolFailure(f"There is no course document for {args.course}. Nothing was looked up.")
    found = []
    for s in sections:
        for sentence in _SENTENCE_END.split(" ".join(s.text.split())):
            if not _DEADLINE.search(sentence):
                continue
            if args.about and args.about.casefold() not in f"{s.title} {sentence}".casefold():
                continue
            found.append(Deadline(section=s.title, quote=sentence))
    if not found:
        raise ToolFailure(f"No deadline in the {args.course} document mentions '{args.about}'. "
                          "Try a shorter word, like HW2, or leave 'about' out to list every deadline.")
    return DeadlineList(course=args.course, deadlines=found[:args.limit], total=len(found))


# ---------------------------------------------------------------- search_course_docs


class Section(BaseModel):
    source: str               # the document id, e.g. 'milestones/hw1'. Never a file path
    heading: str              # the '## ' heading this section is under
    text: str                 # the section as written, line breaks collapsed, cut at MAX_SECTION_CHARS


class SectionList(BaseModel):
    course: str
    sources: list[str]        # the distinct documents behind the sections, in rank order: a citation line
    sections: list[Section]


@lru_cache(maxsize=1)
def corpus_index() -> course_index.Index:
    """The index, built once per process. data/index/ is in .gitignore, so CI (and a fresh clone) has
    none: the first call builds it from data/corpus/. Offline that is the trigram hash in src/offline.py,
    so it needs no key, no network and costs nothing."""
    try:
        return course_index.load()
    except (FileNotFoundError, course_index.IndexMismatch):
        return course_index.build(load_corpus(CORPUS))


def clip(text: str) -> str:
    """One line, cut at a word boundary. The words are the document's own."""
    line = " ".join(text.split())
    return line if len(line) <= MAX_SECTION_CHARS else line[:MAX_SECTION_CHARS].rsplit(" ", 1)[0] + " ..."


def search_course_docs(args: SearchCourseDocs) -> SectionList:
    """The sections of data/corpus most likely to answer the question, each with its document and heading.
    This is the Week 4 retriever (hybrid()) behind a contract: no model call, so the text cannot be
    invented, only copied. Below the relevance floor it refuses instead of returning the least bad match."""
    hits = hybrid(corpus_index(), args.question, k=args.k)
    best = max((h.score for h in hits), default=0.0)
    if best < grounded.min_score():
        raise ToolFailure(f"Nothing in the {args.course} course documents matched that question. Ask a shorter "
                          "question in the words the course uses, like 'Design Review points' or 'HW2 deadline'.")
    return SectionList(
        course=args.course,
        sources=list(dict.fromkeys(h.chunk.doc_id for h in hits)),   # distinct, first mention wins
        sections=[Section(source=h.chunk.doc_id, heading=h.chunk.section, text=clip(h.chunk.text)) for h in hits])


# ---------------------------------------------------------------- the registry

@dataclass(frozen=True)
class Tool:
    name: str
    args: type[Contract]
    run: Callable[..., BaseModel]
    writes: bool = False                  # True: changes the world, needs a signed-in student

    def schema(self) -> dict:
        """What the model sees: name, description and JSON Schema, all from the contract."""
        return {"type": "function", "function": {
            "name": self.name, "description": self.args.__doc__.strip(),
            "parameters": self.args.model_json_schema()}}


TOOLS = {t.name: t for t in [
    Tool("save_reminder", SaveReminder, save_reminder, writes=True),
    Tool("find_deadlines", FindDeadlines, find_deadlines),
    Tool("search_course_docs", SearchCourseDocs, search_course_docs),
]}


def tools_for(student: str | None) -> dict[str, Tool]:
    """Least privilege by construction: a visitor who is not signed in is never offered a write tool."""
    return {n: t for n, t in TOOLS.items() if student or not t.writes}
