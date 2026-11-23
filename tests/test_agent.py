"""Lab 7 tests: copied from Lab-7/templates/test_agent.py, three ADAPT lines changed, plus endpoint tests.
All offline: the "model" is a small function written here, so the test decides exactly what it asks for.
Today is pinned to 2026-10-28 (tests/conftest.py), so a reminder due 2026-11-08 is in range."""
import json

from fastapi.testclient import TestClient

from src import memory
from src.agent import LOOP_TOOLS, PENDING, confirm, run
from src.app import app, get_planner
from src.tools import student_key

USER = "s123"                                                   # ADAPT 1: a signed-in test student
NEEDS_A_YES = ("save_reminder", {"course": "cs6920", "title": "HW2 Tool Contract", "due": "2026-11-08"})  # ADAPT 2


def what_changed():
    """ADAPT 3: what save_reminder changes: this student's reminders in the memory store."""
    return memory.reminders(student_key(USER))


def scripted(*turns):
    """A fake model: each turn is either a list of (tool, arguments) calls, or the final text."""
    left = list(turns)

    def model(messages, schemas):
        turn = left.pop(0)
        if isinstance(turn, str):
            return {"content": turn, "tool_calls": []}
        return {"content": None, "tool_calls": [
            {"id": f"c{len(messages)}-{i}", "name": name, "arguments": json.dumps(args)} for i, (name, args) in enumerate(turn)]}
    return model


def test_the_gate_blocks_until_a_person_says_yes():
    PENDING.clear()
    before = what_changed()
    plan = run("do it for me", USER, llm=scripted([NEEDS_A_YES], "I proposed one action."))
    assert plan["status"] == "needs_confirmation" and len(plan["proposed"]) == 1
    assert what_changed() == before                         # proposed is not done
    done = confirm(USER, [plan["proposed"][0]["id"]])
    assert done[0]["ok"] and what_changed() != before       # the yes is what did it
    assert confirm(USER, [plan["proposed"][0]["id"]]) == [] # and a plan works once


def test_the_loop_stops_after_max_steps():
    PENDING.clear()
    before = what_changed()
    forever = scripted(*[[NEEDS_A_YES]] * 10)               # a model that never says "done"
    plan = run("do it for me", USER, llm=forever, max_steps=4)
    assert plan["status"] == "stopped" and "4 steps" in plan["text"]
    assert what_changed() == before                         # stopping early does nothing, either


def test_a_read_runs_inside_the_loop_and_the_plan_is_keyed_by_hash():
    PENDING.clear()
    lookup = ("find_deadlines", {"course": "cs6920", "about": "HW2"})
    plan = run("remind me about HW2, due 2026-11-08", USER,
               llm=scripted([lookup], [NEEDS_A_YES], "I proposed a reminder for HW2."))
    assert [t["parked"] for t in plan["trace"]] == [False, True]          # the read ran, the write waited
    assert plan["proposed"][0]["summary"] == "Save reminder: HW2 Tool Contract · cs6920 · due 2026-11-08 · remind 2 days before"
    assert list(PENDING) == [student_key(USER)]                           # never the raw id


def test_the_loop_only_gets_the_tools_on_its_list():
    seen = {}

    def model(messages, schemas):
        seen["tools"] = sorted(s["function"]["name"] for s in schemas)
        return {"content": "Nothing to do.", "tool_calls": []}
    assert run("hello", USER, llm=model)["status"] == "answered"
    assert seen["tools"] == sorted(LOOP_TOOLS)              # search_course_docs is not offered to the planner
    run("hello", None, llm=model)
    assert seen["tools"] == ["find_deadlines"]              # a visitor's loop has no write tool at all


def test_the_endpoints_park_then_confirm_by_id_only():
    PENDING.clear()
    app.dependency_overrides[get_planner] = lambda: scripted([NEEDS_A_YES], "I proposed one reminder.")
    try:
        c, h = TestClient(app), {"X-Student-Id": USER}
        assert c.post("/plan", json={"goal": "remind me about HW2"}).status_code == 401    # a plan needs a student
        plan = c.post("/plan", json={"goal": "remind me about HW2, due 2026-11-08"}, headers=h).json()
        assert plan["status"] == "needs_confirmation" and what_changed() == []
        sneaky = c.post("/plan/confirm", json={"approve": ["a1"], "arguments": {"due": "2026-12-01"}}, headers=h)
        assert sneaky.status_code == 422 and what_changed() == []                          # ids only, never arguments
        assert c.post("/plan/confirm", json={"approve": ["a1"]}).status_code == 401
        done = c.post("/plan/confirm", json={"approve": ["a1"]}, headers=h).json()["done"]
        assert done[0]["ok"] and len(what_changed()) == 1
        assert c.post("/plan/confirm", json={"approve": ["a1"]}, headers=h).json()["done"] == []
    finally:
        app.dependency_overrides.clear()
