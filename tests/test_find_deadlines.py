"""HW2 (NTsik0): find_deadlines, a read-only lookup behind a contract. The golden cases are in
evals/tools/NTsik0.yaml; these tests cover what the cases do not."""
import asyncio
import json
from pathlib import Path

from mcp import Client

from src.act import call_tool
from src.mcp_server import mcp
from src.tools import tools_for

DOC = " ".join((Path(__file__).resolve().parents[1] / "data" / "courses" / "cs6920.md").read_text(encoding="utf-8").split())


def call(**args):
    return {"id": "c1", "name": "find_deadlines", "arguments": json.dumps(args)}


def test_every_quote_is_copied_from_the_document():
    out = call_tool(call(course="cs6920"), tools_for(None), None)
    assert out["ok"] and out["result"]["total"] == 4
    assert all(d["quote"] in DOC for d in out["result"]["deadlines"])


def test_it_is_offered_to_visitors_because_it_only_reads():
    assert "find_deadlines" in tools_for(None) and not tools_for(None)["find_deadlines"].writes


def test_limit_cuts_the_list_but_total_counts_all():
    out = call_tool(call(course="cs6920", limit=2), tools_for(None), None)
    assert len(out["result"]["deadlines"]) == 2 and out["result"]["total"] == 4


def test_filter_matches_the_section_name_too():
    out = call_tool(call(course="cs6920", about="Demo Day"), tools_for(None), None)
    assert out["ok"] and out["result"]["deadlines"][0]["section"] == "Demo Day"


def test_the_refusal_names_no_path_or_file():
    out = call_tool(call(course="cs6920", about="midterm"), tools_for(None), None)
    assert not out["ok"] and "data/" not in out["error"] and ".md" not in out["error"]


def test_mcp_marks_it_read_only_and_serves_it():
    async def go():
        async with Client(mcp) as c:
            listed = {t.name: t for t in (await c.list_tools()).tools}
            return listed["find_deadlines"], await c.call_tool("find_deadlines", {"course": "cs6920", "about": "HW1"})
    tool, r = asyncio.run(go())
    assert tool.annotations.read_only_hint is True
    assert not r.is_error and r.structured_content["total"] == 1
