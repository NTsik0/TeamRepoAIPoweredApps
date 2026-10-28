"""CourseMate's tools: the code that acts, behind the contracts in src/contracts.py (Week 5).

One tool today, save_reminder, and it only adds. Nothing here deletes, edits another student's
data, or sends a message: that is the least-privilege decision, made by what we chose NOT to build.

Every tool takes a validated contract object (never raw model output) and returns a pydantic
result. A failure we expected raises ToolFailure with a message written for the model to read
and act on. Anything else is a bug and is allowed to crash.

Reminders are written to $COURSEMATE_STATE_DIR/reminders.json (default state/), keyed by a
hash of the student id, never the id itself.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from src.contracts import Contract, SaveReminder

TBILISI = ZoneInfo("Asia/Tbilisi")
MAX_REMINDERS = 50          # per student
MAX_DAYS_AHEAD = 180        # about one semester


class ToolFailure(Exception):
    """An expected failure. The message goes back to the model, so make it say what to do next."""


def today() -> date:
    """Today in Tbilisi. COURSEMATE_TODAY pins it for tests."""
    pinned = os.environ.get("COURSEMATE_TODAY")
    return date.fromisoformat(pinned) if pinned else datetime.now(TBILISI).date()


def student_key(student: str) -> str:
    """We store and log a hash of the student id, not the id itself."""
    return hashlib.sha256(student.encode()).hexdigest()[:12]


def _state_file() -> Path:
    return Path(os.environ.get("COURSEMATE_STATE_DIR", "state")) / "reminders.json"


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

    path = _state_file()
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    mine = state.setdefault(student_key(student), [])
    remind_on = max(now, args.due - timedelta(days=args.days_before))

    same = [r for r in mine if r["course"] == args.course and r["due"] == args.due.isoformat()
            and r["title"].casefold() == args.title.casefold()]
    if same:
        r = same[0]
        return ReminderResult(course=r["course"], title=r["title"], due=date.fromisoformat(r["due"]),
                              remind_on=date.fromisoformat(r["remind_on"]), status="already saved",
                              reminders=len(mine))
    if len(mine) >= MAX_REMINDERS:
        raise ToolFailure(f"You already have {MAX_REMINDERS} saved reminders, the most allowed. Nothing was saved.")

    mine.append({"course": args.course, "title": args.title, "due": args.due.isoformat(),
                 "remind_on": remind_on.isoformat()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return ReminderResult(course=args.course, title=args.title, due=args.due, remind_on=remind_on,
                          status="saved", reminders=len(mine))


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
]}


def tools_for(student: str | None) -> dict[str, Tool]:
    """Least privilege by construction: a visitor who is not signed in is never offered a write tool."""
    return {n: t for n, t in TOOLS.items() if student or not t.writes}
