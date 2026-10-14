# 0003 · Grounded answers on a new endpoint; keep the Week 2 /ask for now

**Date:** Week 4 (2026-10-14) · **Decided by:** Nikoloz Tsikaridze

**Context.** Lab 4 adds retrieval with citations and refusal (`src/answer.py`). Our Week 2 slice already answers on `POST /ask` with keyword retrieval (decision 0001) and its own response shape and tests.

**Decision.** Serve grounded answers on `POST /ask/grounded`. Keep `POST /ask` unchanged until the live golden run passes at 0.70, then make `/ask` call the grounded pipeline in its own pull request.

**Alternatives.** Replace `/ask` now: changes a public response shape (an "ask first" item in AGENTS.md) and deletes the Week 2 tests before the new path has a live result.

**Consequences.** Two answering paths for a short time. Both log every model call to `logs/usage.jsonl` with cost.
