"""Run the 3 HW1 golden questions against the real model and write the results into golden.md.

Usage (from the repo root, with OPENROUTER_API_KEY exported):
    python hw1/NTsik0/src/run_golden.py
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deadlines import DeadlineError, OpenRouterClient, _norm, find_deadlines  # noqa: E402

GOLDEN_MD = Path(__file__).resolve().parent.parent / "golden.md"
LOG_PATH = Path(os.environ.get("HW1_LOG_PATH", "logs/hw1-usage.jsonl"))
START, END = "<!-- results:start -->", "<!-- results:end -->"


def has(out, item_word, *due_parts):
    for d in out["deadlines"]:
        if item_word in d["item"].lower() and all(p in _norm(d["due"]) for p in due_parts):
            return d
    return None


def g1(client):
    out = find_deadlines("cs6920", client, LOG_PATH)
    hit = has(out, "hw1", "thursday of week 4", "23:59")
    return bool(hit), (json.dumps(hit, ensure_ascii=False) if hit else
                       f"no HW1 item with that date; got {len(out['deadlines'])} items, dropped {out['dropped']}")


def g2(client):
    out = find_deadlines("cs6920", client, LOG_PATH)
    hit = has(out, "hw2", "end of week 7")
    return bool(hit and out["dropped"] == 0), (
        f"{json.dumps(hit, ensure_ascii=False) if hit else 'no HW2 item'}; dropped={out['dropped']}")


def g3(client):
    try:
        find_deadlines("cs9999", client, LOG_PATH)
    except DeadlineError as e:
        return e.code == "course_not_found", f"error {e.code}: {e.message}"
    return False, "returned a result instead of an error"


QUESTIONS = [
    ("G1", "`cs6920`: is HW1 listed with its real deadline?",
     "an item about HW1 whose `due` contains \"Thursday of Week 4\" and \"23:59\"", g1),
    ("G2", "`cs6920`: is HW2 listed, with nothing invented?",
     "an item about HW2 whose `due` contains \"end of Week 7\", and `dropped` = 0", g2),
    ("G3", "`cs9999` (no such course)",
     "error `course_not_found`, no model call", g3),
]


def main() -> int:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Export OPENROUTER_API_KEY first.", file=sys.stderr)
        return 2
    client = OpenRouterClient()
    rows, passed = [], 0
    for gid, question, expected, check in QUESTIONS:
        try:
            ok, actual = check(client)
        except DeadlineError as e:
            ok, actual = False, f"error {e.code}: {e.message}"
        passed += ok
        actual = actual.replace("|", "\\|")
        rows.append(f"| {gid} | {question} | {expected} | {actual} | {'PASS' if ok else 'FAIL'} |")
        print(f"{gid}: {'PASS' if ok else 'FAIL'} · {actual}")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    table = "\n".join([
        f"Run: {stamp} · model `{client.model}` · **{passed}/3 passed**",
        "",
        "| # | Input | Expected | Actual | Result |",
        "|---|---|---|---|---|",
        *rows,
    ])
    text = GOLDEN_MD.read_text(encoding="utf-8")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    GOLDEN_MD.write_text(f"{head}{START}\n{table}\n{END}{tail}", encoding="utf-8")
    print(f"\n{passed}/3 passed · results written to {GOLDEN_MD}")
    return 0 if passed == 3 else 1


if __name__ == "__main__":
    sys.exit(main())
