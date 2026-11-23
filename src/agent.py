"""Lab 7: a supervised loop. Copied from Lab-7/templates/agent_starter.py, three ADAPT lines changed.
Contract: docs/agent-contract.md.

Three ideas, and nothing else:
  the loop    ask the model "what next?", run the tool it asks for, show it the result, repeat
  the stop    at most MAX_STEPS model turns, then the loop ends and says so
  the yes     a tool in NEEDS_YES is never run by the loop. It is parked. confirm() runs it
              when a person says yes, and no model is involved in that.
"""
from __future__ import annotations

import json

from src.act import as_assistant, call_tool     # echo the model's turn; run one tool safely
from src.llm import complete_tools              # one model call that may ask for tools
from src.tools import student_key, today, tools_for

# ADAPT 1: what is this loop for, and how to finish.
GOAL_PROMPT = """You help a KIU student set reminders for course deadlines. The course id is cs6920 (lowercase).
Work in steps: first look the deadline up with find_deadlines, then propose save_reminder for it.
Use only a due date the student wrote in their message, as YYYY-MM-DD. The course document often names a week,
not a date: never work a date out yourself. If the student gave no date, propose nothing and ask for the date.
A proposed reminder is NOT saved: the student must confirm it. Never say it is saved.
Finish with two or three sentences: what you proposed, and the course document's sentence it matches."""

LOOP_TOOLS = ("find_deadlines", "save_reminder")    # ADAPT 2: not search_course_docs, the goal does not need it
NEEDS_YES = {"save_reminder"}                       # ADAPT 3: the only tool that writes, in the student's name
MAX_STEPS = 6                                       # the stop

PENDING: dict[str, list[dict]] = {}     # student hash -> parked actions. Never the raw id (AGENTS.md).


def facts(user: str) -> str:
    """Facts our code already knows go into the prompt. The model is not asked to guess them."""
    return f"Today is {today():%A %Y-%m-%d}, Tbilisi time."


def describe(call: dict) -> str:
    """One line the student reads before saying yes."""
    try:
        a = json.loads(call["arguments"])
        return (f"Save reminder: {a['title']} · {a['course']} · due {a['due']} · "
                f"remind {a.get('days_before', 2)} days before")
    except (ValueError, KeyError, TypeError):
        return f"{call['name']} {call['arguments']}"


def run(goal: str, user: str | None, llm=complete_tools, max_steps: int = MAX_STEPS) -> dict:
    allowed = {name: tool for name, tool in tools_for(user).items() if name in LOOP_TOOLS}
    schemas = [tool.schema() for tool in allowed.values()]
    messages = [{"role": "system", "content": GOAL_PROMPT + "\n" + facts(user)}, {"role": "user", "content": goal}]
    proposed, trace = [], []
    for step in range(1, max_steps + 1):
        msg = llm(messages, schemas)                                  # REASON: what next?
        if not msg["tool_calls"]:                                     # the model says it is done
            return finish("needs_confirmation" if proposed else "answered", msg["content"], user, proposed, trace)
        messages.append(as_assistant(msg))
        for call in msg["tool_calls"]:
            if call["name"] in NEEDS_YES:                             # ACT, needs a yes: park it
                action = {"id": f"a{len(proposed) + 1}", "tool": call["name"],
                          "arguments": call["arguments"], "summary": describe(call)}
                proposed.append(action)
                observation = {"status": "added to the plan; NOT saved. The student will confirm.",
                               "summary": action["summary"]}
            else:                                                     # ACT, a read: run it
                outcome = call_tool(call, allowed, user)
                observation = outcome.get("result") or {"error": outcome["error"]}
            trace.append({"step": step, "tool": call["name"], "parked": call["name"] in NEEDS_YES})
            messages.append({"role": "tool", "tool_call_id": call["id"],              # OBSERVE
                             "content": json.dumps(observation)})
    return finish("stopped", f"I stopped after {max_steps} steps. Nothing was saved.", user, proposed, trace)


def finish(status: str, text: str, user: str | None, proposed: list[dict], trace: list[dict]) -> dict:
    if user:                                                          # a visitor has no write tool, so nothing to park
        PENDING[student_key(user)] = proposed                         # parked until the student answers
    print(json.dumps({"status": status, "steps": len({t["step"] for t in trace}), "proposed": len(proposed)}))
    return {"status": status, "text": text, "proposed": proposed, "trace": trace}


def confirm(user: str, approved_ids: list[str]) -> list[dict]:
    """The student said yes. Run exactly what was parked, once. No model here.
    The contract is checked again inside call_tool(), so a parked call cannot skip the gates."""
    actions = PENDING.pop(student_key(user), [])                      # pop: a plan works once
    allowed = tools_for(user)
    return [call_tool({"id": a["id"], "name": a["tool"], "arguments": a["arguments"]}, allowed, user)
            for a in actions if a["id"] in approved_ids]
