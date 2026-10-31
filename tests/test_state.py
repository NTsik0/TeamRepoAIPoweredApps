"""Week 6: streaming and session state. Offline: no key, no network.

The first four follow Lab-6/templates/test_state.py: they prove the streaming log line and the
scope, lifetime and deletion columns of docs/state-contract.md. The rest cover the endpoints."""
import json
import os
import sqlite3

from fastapi.testclient import TestClient

from src import memory
from src.app import app
from src.chat import build_messages, chat_turn
from src.llm import stream
from src.tools import student_key

SESSION_A, SESSION_B = "sess-aaaa-1111", "sess-bbbb-2222"
A, B = student_key("student-a"), student_key("student-b")
HW2 = memory.Reminder(course="cs6920", title="HW2 Tool Contract", due="2026-11-08", remind_on="2026-11-06")


def rows() -> list[tuple]:
    if not memory.db_path().exists():
        return []
    with sqlite3.connect(memory.db_path()) as c:
        return c.execute("SELECT key, kind, value FROM memory").fetchall()


def sse_events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


# ---------------------------------------------------------------- the four from the template

def test_stream_yields_pieces_and_logs_time_to_first_token():
    log = os.environ["COURSEMATE_LOG_PATH"]
    before = open(log).read().count("\n") if os.path.exists(log) else 0
    s = stream([{"role": "user", "content": "When is HW2 due?"}])
    pieces = list(s)
    assert len(pieces) > 1 and "".join(pieces) == s.text
    lines = open(log).read().splitlines()
    assert len(lines) == before + 1
    last = json.loads(lines[-1])
    assert last["kind"] == "stream" and "ttft_ms" in last and last["ttft_ms"] is not None


def test_scope_one_students_memory_never_reaches_another():
    memory.add_reminder(A, HW2)
    memory.add_turn(SESSION_A, "user", "my secret question about HW2")
    assert memory.reminders(B) == [] and memory.recent_turns(SESSION_B) == []
    prompt = build_messages(SESSION_B, "student-b", "hello")
    assert all("HW2 Tool Contract" not in m["content"] and "secret" not in m["content"] for m in prompt)
    assert "HW2 Tool Contract" in build_messages(SESSION_A, "student-a", "hello")[0]["content"]


def test_lifetime_is_enforced(monkeypatch):
    monkeypatch.setenv("COURSEMATE_NOW", "2026-10-28T09:00:00+00:00")
    memory.add_reminder(A, HW2)
    memory.add_turn(SESSION_A, "user", "hello")
    monkeypatch.setenv("COURSEMATE_NOW", "2026-10-29T09:00:01+00:00")       # 24 hours and a second later
    assert memory.recent_turns(SESSION_A) == [] and len(memory.reminders(A)) == 1
    monkeypatch.setenv("COURSEMATE_NOW", "2026-11-09T19:59:00+00:00")       # 23:59 on 9 Nov, Tbilisi
    assert len(memory.reminders(A)) == 1
    monkeypatch.setenv("COURSEMATE_NOW", "2026-11-09T20:00:00+00:00")       # 00:00 on 10 Nov, Tbilisi
    assert memory.reminders(A) == []
    assert memory.expire() == 2 and rows() == []


def test_deletion_is_total_and_immediate():
    memory.add_reminder(A, HW2)
    memory.add_turn(SESSION_A, "user", "hello")
    memory.add_reminder(B, HW2)
    gone = memory.forget(A, SESSION_A)
    assert gone.to_dict() == {"reminders": 1, "turns": 1}
    assert memory.reminders(A) == [] and memory.recent_turns(SESSION_A) == []
    left = rows()
    assert len(left) == 1 and left[0][0] == f"student:{B}"           # A's rows are gone, not flagged


# ---------------------------------------------------------------- the turn

def test_the_turn_remembers_this_session_and_nothing_for_a_visitor():
    list(chat_turn("When is HW2 due?", session=SESSION_A))
    assert [t["role"] for t in memory.recent_turns(SESSION_A)] == ["user", "assistant"]
    list(chat_turn("When is HW2 due?"))                               # no session, no student
    assert len(rows()) == 2


def test_a_reminder_streams_through_the_week5_gates_and_names_the_delete_path():
    events = list(chat_turn("Remind me about HW2 Tool Contract due 2026-11-08", session=SESSION_A, student="student-a"))
    tool = [p for k, p in events if k == "tool"][0]
    assert tool["ok"] and tool["stored"]["status"] == "saved" and tool["delete_with"] == "DELETE /me/memory"
    assert events[-1][0] == "done" and events[-1][1]["calls"] == 1
    assert len(memory.reminders(A)) == 1
    stored = " ".join(f"{k} {v}" for k, _, v in rows())
    assert "student-a" not in stored and A in stored                 # a hash, never the id


def test_a_visitor_is_never_offered_the_write_tool_in_chat():
    events = list(chat_turn("Remind me about HW2 Tool Contract due 2026-11-08", session=SESSION_A))
    assert not [k for k, _ in events if k == "tool"] and memory.reminders(A) == []


# ---------------------------------------------------------------- the endpoints

def test_chat_endpoint_streams_server_sent_events():
    r = TestClient(app).post("/chat", json={"question": "When is HW2 due?"}, headers={"X-Session-Id": SESSION_A})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    kinds = [k for k, _ in sse_events(r.text)]
    assert kinds.count("token") > 1 and kinds[-1] == "done"


def test_me_memory_shows_and_forgets(monkeypatch):
    c = TestClient(app)
    h = {"X-Session-Id": SESSION_A, "X-Student-Id": "student-a"}
    c.post("/chat", json={"question": "Remind me about HW2 Tool Contract due 2026-11-08"}, headers=h)
    seen = c.get("/me/memory", headers=h).json()
    assert len(seen["reminders"]) == 1 and seen["recent_turns"] == 2 and seen["delete_with"] == "DELETE /me/memory"
    assert c.delete("/me/memory", headers=h).json() == {"reminders": 1, "turns": 2}
    assert c.get("/me/memory", headers=h).json()["reminders"] == [] and rows() == []


def test_bad_headers_are_refused_with_the_error_shape():
    c = TestClient(app)
    r = c.delete("/me/memory", headers={"X-Session-Id": "x"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "bad_session_id"
    r = c.post("/chat", json={"question": "hello there"}, headers={"X-Student-Id": "a b"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "bad_student_id"
