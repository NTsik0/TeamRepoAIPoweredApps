"""Run the four Lab 3 test photos through the real model and save the evidence.

    python -m evals.run_images          needs OPENROUTER_API_KEY; about $0.01 for four images

Compares each route with evals/images_expected.json and writes evals/results/<timestamp>-images.json.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from src.deadline_checks import decide
from src.deadline_extract import extract
from src.llm import CHAT_MODEL, OFFLINE

IMAGES = Path("tests/images")
EXPECTED = json.loads(Path("evals/images_expected.json").read_text(encoding="utf-8"))
RESULTS = Path("evals/results")


def check(expect: dict, route: str, flags: list, due_date: str | None) -> list[str]:
    why = []
    allowed = expect["route"] if isinstance(expect["route"], list) else [expect["route"]]
    if route not in allowed:
        why.append(f"expected {' or '.join(allowed)}, got {route}")
    if "due_date" in expect and route == "accepted" and due_date != expect["due_date"]:
        why.append(f"expected due_date {expect['due_date']}, got {due_date}")
    if "flag" in expect and not any(k == expect["flag"] for k, _ in flags):
        why.append(f"expected flag {expect['flag']}")
    return why


def main() -> int:
    if OFFLINE:
        print("Set COURSEMATE_OFFLINE=0: this run needs the real model.", file=sys.stderr)
        return 2
    today = date.today()
    rows = []
    for name, expect in EXPECTED.items():
        x = extract((IMAGES / name).read_bytes())
        d = decide(x, today)
        why = check(expect, d.route, d.flags, x.due_date.value)
        rows.append({"image": name, "pass": not why, "why": why, "route": d.route, "flags": d.flags,
                     "hard": sorted(d.hard), "reasons": d.reasons(x), "extraction": x.model_dump()})
        print(f"{'PASS' if not why else 'FAIL'}  {name:<20} {d.route:<9} {'; '.join(d.reasons(x))}")
        for w in why:
            print(f"        {w}")
    passed = sum(r["pass"] for r in rows)
    report = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": CHAT_MODEL,
              "today": today.isoformat(), "passed": passed, "total": len(rows), "items": rows}
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{datetime.now().strftime('%Y-%m-%d-%H%M')}-images.json"
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\n{passed}/{len(rows)} routed as expected · written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
