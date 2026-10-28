"""The MCP door: same contract, annotations, identity from the server, in-memory client (Week 5).
The both-doors tests are copied from Lab-5/examples/campuspulse-tools/tests/test_mcp.py."""
import asyncio

import pytest
from mcp import Client

from src import tools
from src.mcp_server import mcp


def run(coro):
    return asyncio.run(coro)


async def listed():
    async with Client(mcp) as c:
        return {t.name: t for t in (await c.list_tools()).tools}


async def call(name, args):
    async with Client(mcp) as c:
        return await c.call_tool(name, args)


def strip(schema):
    return {k: {kk: vv for kk, vv in v.items() if kk != "title"} for k, v in schema["properties"].items()}


GOOD = {"course": "cs6920", "title": "HW2 Tool Contract", "due": "2026-11-08"}


def test_same_tools_through_both_doors():
    assert set(run(listed())) == set(tools.TOOLS)


@pytest.mark.parametrize("name", sorted(tools.TOOLS))
def test_both_doors_describe_the_arguments_identically(name):
    mcp_schema = run(listed())[name].input_schema
    fc_schema = tools.TOOLS[name].schema()["function"]["parameters"]
    assert strip(mcp_schema) == strip(fc_schema)
    assert set(mcp_schema.get("required", [])) == set(fc_schema.get("required", []))


def test_annotations_mark_the_one_additive_write():
    t = run(listed())["save_reminder"]
    assert t.annotations.read_only_hint is False and t.annotations.destructive_hint is False


def test_bad_arguments_are_rejected_by_the_sdk(monkeypatch):
    monkeypatch.setenv("COURSEMATE_STUDENT", "s123")
    r = run(call("save_reminder", {**GOOD, "due": "2026-02-30"}))
    assert r.is_error


def test_expected_failure_reaches_the_model_as_text(monkeypatch):
    monkeypatch.setenv("COURSEMATE_STUDENT", "s123")
    r = run(call("save_reminder", {**GOOD, "due": "2026-10-20"}))
    assert r.is_error and "already passed" in r.content[0].text


def test_save_reminder_needs_a_signed_in_student():
    r = run(call("save_reminder", GOOD))
    assert r.is_error and "Not signed in" in r.content[0].text


def test_student_comes_from_the_server_not_the_model(monkeypatch):
    monkeypatch.setenv("COURSEMATE_STUDENT", "s123")
    assert "student" not in run(listed())["save_reminder"].input_schema["properties"]
    r = run(call("save_reminder", {**GOOD, "student": "s999"}))
    assert not r.is_error and r.structured_content["status"] == "saved"
    stored = tools._state_file().read_text()
    assert tools.student_key("s123") in stored and tools.student_key("s999") not in stored


def test_one_call_through_the_client(monkeypatch):
    monkeypatch.setenv("COURSEMATE_STUDENT", "s123")
    r = run(call("save_reminder", {**GOOD, "days_before": 3}))
    assert not r.is_error and r.structured_content["remind_on"] == "2026-11-05"
