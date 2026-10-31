"""Session State: everything CourseMate remembers across turns, in one place (Week 6).

docs/state-contract.md is the human-readable version of this table; the two must agree.

  kind        scope                 lifetime                          written when                 deleted by
  turn        one session           24 hours                          every chat turn, automatically   expiry, DELETE /me/memory
  reminder    one student (hash)    until the day after the due date  only when the student asks       expiry, DELETE /me/memory
                                    (at most 181 days)                (the save_reminder tool)

Rules that hold everywhere in this file:
  * the key holds the student HASH (tools.student_key), never the id
  * nothing is stored unless a function here is called with a session or a student:
    a visitor with neither leaves nothing behind
  * every read filters by key AND by expiry; there is no "all rows" read in the product
  * deletion is one call and it is total: forget() removes the rows, it does not flag them

Storage: SQLite from the standard library, $COURSEMATE_STATE_DIR/memory.db (default state/).
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TBILISI = ZoneInfo("Asia/Tbilisi")
TURN_LIFETIME = timedelta(hours=24)        # a conversation is a day, then it is gone
MAX_TURNS = 6                              # the context budget for history: 3 exchanges
MAX_TURN_CHARS = 2000
MAX_REMINDERS = 50                         # per student


def db_path() -> Path:
    return Path(os.environ.get("COURSEMATE_STATE_DIR", "state")) / "memory.db"


def now() -> datetime:
    """UTC now. COURSEMATE_NOW pins it for the lifetime tests."""
    pinned = os.environ.get("COURSEMATE_NOW")
    return datetime.fromisoformat(pinned) if pinned else datetime.now(timezone.utc)


@contextmanager
def _conn():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY, key TEXT NOT NULL, kind TEXT NOT NULL, role TEXT,
            value TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL)""")
        conn.execute("CREATE INDEX IF NOT EXISTS memory_key ON memory(key, kind, expires_at)")
        yield conn
        conn.commit()
    finally:
        conn.close()


def _student(student_hash: str) -> str:
    return f"student:{student_hash}"


def _session(session: str) -> str:
    return f"session:{session}"


# ---------------------------------------------------------------- turns (scope: one session)

def add_turn(session: str, role: str, text: str) -> None:
    t = now()
    with _conn() as c:
        c.execute("INSERT INTO memory (key, kind, role, value, created_at, expires_at) VALUES (?,?,?,?,?,?)",
                  (_session(session), "turn", role, text[:MAX_TURN_CHARS], t.isoformat(),
                   (t + TURN_LIFETIME).isoformat()))


def recent_turns(session: str, limit: int = MAX_TURNS) -> list[dict]:
    """The last few turns of THIS session, oldest first, ready to drop into a messages list."""
    with _conn() as c:
        rows = c.execute("SELECT role, value FROM memory WHERE key=? AND kind='turn' AND expires_at>? "
                         "ORDER BY id DESC LIMIT ?", (_session(session), now().isoformat(), limit)).fetchall()
    return [{"role": r["role"], "content": r["value"]} for r in reversed(rows)]


# ---------------------------------------------------------------- reminders (scope: one student)

def reminder_expiry(due: date) -> datetime:
    """A reminder dies at the end of the day after its due date, Tbilisi time."""
    return datetime.combine(due + timedelta(days=2), time(0, 0), TBILISI).astimezone(timezone.utc)


@dataclass
class Reminder:
    course: str
    title: str
    due: str
    remind_on: str


def reminders(student_hash: str) -> list[Reminder]:
    with _conn() as c:
        rows = c.execute("SELECT value FROM memory WHERE key=? AND kind='reminder' AND expires_at>? ORDER BY id",
                         (_student(student_hash), now().isoformat())).fetchall()
    return [Reminder(**json.loads(r["value"])) for r in rows]


def add_reminder(student_hash: str, r: Reminder) -> tuple[str, int]:
    """Store one reminder. Returns (status, how many the student now has). Idempotent on
    course + title (case-insensitive) + due. Raises OverflowError past MAX_REMINDERS."""
    mine = reminders(student_hash)
    if any(x.course == r.course and x.due == r.due and x.title.casefold() == r.title.casefold() for x in mine):
        return "already saved", len(mine)
    if len(mine) >= MAX_REMINDERS:
        raise OverflowError(MAX_REMINDERS)
    with _conn() as c:
        c.execute("INSERT INTO memory (key, kind, role, value, created_at, expires_at) VALUES (?,?,?,?,?,?)",
                  (_student(student_hash), "reminder", None, json.dumps(asdict(r)), now().isoformat(),
                   reminder_expiry(date.fromisoformat(r.due)).isoformat()))
    return "saved", len(mine) + 1


# ---------------------------------------------------------------- deletion and expiry

@dataclass
class Forgotten:
    reminders: int
    turns: int

    def to_dict(self) -> dict:
        return {"reminders": self.reminders, "turns": self.turns}


def forget(student_hash: str | None, session: str | None) -> Forgotten:
    """Everything, now. Rows are deleted, not flagged. Called by DELETE /me/memory; never by the model."""
    n_r = n_t = 0
    with _conn() as c:
        if student_hash:
            n_r = c.execute("DELETE FROM memory WHERE key=? AND kind='reminder'", (_student(student_hash),)).rowcount
        if session:
            n_t = c.execute("DELETE FROM memory WHERE key=? AND kind='turn'", (_session(session),)).rowcount
    return Forgotten(reminders=n_r, turns=n_t)


def expire() -> int:
    """Delete every row past its lifetime. Run at app startup; reads already ignore expired rows."""
    with _conn() as c:
        return c.execute("DELETE FROM memory WHERE expires_at<=?", (now().isoformat(),)).rowcount
