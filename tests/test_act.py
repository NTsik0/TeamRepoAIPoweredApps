"""The function-calling loop: offered? valid? then run, with identity from the server (Week 5).
Today is pinned to 2026-10-28 in conftest.py."""
import json
import os

from fastapi.testclient import TestClient

from src import tools
from src.act import MAX_ROUNDS, act, call_tool
from src.app import app
from src.tools import tools_for

GOOD = {"course": "cs6920", "title": "HW2 Tool Contract", "due": "2026-11-08"}


def call(name, **args):
    return {"id": "c1", "name": name, "arguments": json.dumps(args)}


# ---------------------------------------------------------------- the three gates

def test_valid_call_runs_and_saves():
    out = call_tool(call("save_reminder", **GOOD), tools_for("s123"), "s123")
    assert out["ok"] and out["error"] is None
    assert out["result"]["status"] == "saved" and out["result"]["remind_on"] == "2026-11-06"


def test_invalid_arguments_never_reach_the_tool(monkeypatch):
    ran = []
    monkeypatch.setitem(tools.TOOLS, "save_reminder", tools.Tool(
        "save_reminder", tools.SaveReminder, lambda *a, **k: ran.append(1), writes=True))
    out = call_tool(call("save_reminder", **{**GOOD, "title": "<script>alert(1)</script>"}),
                    tools_for("s123"), "s123")
    assert not out["ok"] and out["error"].startswith("invalid arguments: title")
    assert ran == []


def test_a_tool_not_offered_is_not_run():
    out = call_tool(call("save_reminder", **GOOD), tools_for(None), None)
    assert not out["ok"] and "no tool named 'save_reminder'" in out["error"]
    assert not tools._state_file().exists()


def test_a_tool_that_does_not_exist_is_not_run():
    out = call_tool(call("delete_all_reminders"), tools_for("s123"), "s123")
    assert not out["ok"] and "no tool named" in out["error"]


def test_model_cannot_choose_the_student():
    out = call_tool(call("save_reminder", **GOOD, student="s999"), tools_for("s123"), "s123")
    assert not out["ok"] and "student" in out["error"]
    assert not tools._state_file().exists()


def test_visitors_are_offered_no_write_tools():
    assert "save_reminder" not in tools_for(None)
    assert "save_reminder" in tools_for("s123")


# ---------------------------------------------------------------- the tool itself

def test_saving_twice_changes_nothing():
    first = call_tool(call("save_reminder", **GOOD), tools_for("s123"), "s123")
    again = call_tool(call("save_reminder", **{**GOOD, "title": "hw2 tool contract"}), tools_for("s123"), "s123")
    assert first["result"]["status"] == "saved" and again["result"]["status"] == "already saved"
    assert again["result"]["reminders"] == 1


def test_a_past_deadline_is_an_expected_failure_the_model_can_read():
    out = call_tool(call("save_reminder", **{**GOOD, "due": "2026-10-20"}), tools_for("s123"), "s123")
    assert not out["ok"] and "already passed" in out["error"] and "Traceback" not in out["error"]


def test_reminders_are_stored_under_a_hash_not_the_student_id():
    call_tool(call("save_reminder", **GOOD), tools_for("s123"), "s123")
    stored = tools._state_file().read_text()
    assert "s123" not in stored and tools.student_key("s123") in stored


def test_every_call_writes_one_log_line_without_the_student_id():
    log = os.environ["COURSEMATE_TOOL_LOG"]
    before = open(log).read().count("\n") if os.path.exists(log) else 0
    call_tool(call("save_reminder", **GOOD), tools_for("s123"), "s123")
    lines = open(log).read().splitlines()
    assert len(lines) == before + 1
    last = json.loads(lines[-1])
    assert last["tool"] == "save_reminder" and last["ok"] and last["student"] == tools.student_key("s123")


# ---------------------------------------------------------------- the loop

def test_end_to_end_offline_answer():
    reply = act("Remind me about HW2 Tool Contract due 2026-11-08, 3 days before", student="s123")
    assert reply.status == "answered" and reply.calls[0]["ok"]
    assert "2026-11-05" in reply.text


def test_visitor_asking_for_a_reminder_is_told_to_sign_in():
    reply = act("Remind me about HW2 Tool Contract due 2026-11-08")
    assert reply.calls == [] and "sign in" in reply.text


def test_the_model_reads_the_error_and_can_repair():
    turns = []

    def model(messages, schemas):
        turns.append(messages[-1]["role"])
        if len(turns) == 1:
            return {"content": None, "tool_calls": [call("save_reminder", **{**GOOD, "course": "CS6920"})]}
        if len(turns) == 2:
            assert "invalid arguments" in json.loads(messages[-1]["content"])["error"]
            return {"content": None, "tool_calls": [call("save_reminder", **GOOD)]}
        return {"content": "Saved.", "tool_calls": []}

    reply = act("Remind me about HW2", student="s123", llm=model)
    assert reply.text == "Saved." and [c["ok"] for c in reply.calls] == [False, True]


def test_loop_stops_after_the_budget():
    def stubborn(messages, schemas):
        return {"content": None, "tool_calls": [call("save_reminder", course="nope")]}

    reply = act("Remind me", student="s123", llm=stubborn)
    assert reply.status == "stopped" and len(reply.calls) == MAX_ROUNDS


def test_reasoning_details_are_echoed_back():
    seen = []

    def model(messages, schemas):
        seen.append(messages)
        if len(seen) == 1:
            return {"content": None, "reasoning_details": [{"type": "reasoning.encrypted", "data": "x"}],
                    "tool_calls": [call("save_reminder", **GOOD)]}
        return {"content": "ok", "tool_calls": []}

    act("Remind me about HW2", student="s123", llm=model)
    assistant = [m for m in seen[1] if m["role"] == "assistant"][0]
    assert assistant["reasoning_details"] == [{"type": "reasoning.encrypted", "data": "x"}]


# ---------------------------------------------------------------- POST /act

def test_act_endpoint_takes_the_student_from_the_header_only():
    c = TestClient(app)
    r = c.post("/act", json={"question": "Remind me about HW2 Tool Contract due 2026-11-08"},
               headers={"X-Student-Id": "s123"})
    assert r.status_code == 200 and r.json()["calls"][0]["ok"]
    stored = tools._state_file().read_text()
    assert tools.student_key("s123") in stored


def test_act_endpoint_rejects_a_malformed_student_header():
    r = TestClient(app).post("/act", json={"question": "Remind me about HW2"},
                             headers={"X-Student-Id": "s1; DROP TABLE"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "bad_student_id"
