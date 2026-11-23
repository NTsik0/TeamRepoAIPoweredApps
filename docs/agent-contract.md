# KIU CourseMate · Agent Contract

Five lines, from `Lab-7/templates/agent-contract.md`, written before `src/agent.py` was adapted.

1. **The goal, in one sentence.** Given "remind me about HW2, it is due 2026-11-25", check the deadline in the course document and propose a reminder for it.
2. **The tools this loop may use.** `find_deadlines` and `save_reminder`. Not `search_course_docs`: finding a deadline does not need a search over the whole corpus.
3. **The one tool that must wait for a yes, and why.** `save_reminder`: it writes into the student's saved reminders, in their name, and a reminder with a wrong date is worse than none, because the student trusts it and stops checking. The date often comes from the student's own message, since the course document names weeks ("the end of Week 7"), not dates, so only the student can confirm it is right.
4. **The most steps it may take.** Six.
5. **What the person sees before they say yes.** One line per proposed action:
   "Save reminder: HW2 Tool Contract · cs6920 · due 2026-11-25 · remind 2 days before"

**Where it lives.** `src/agent.py` (`GOAL_PROMPT`, `LOOP_TOOLS`, `NEEDS_YES`, `MAX_STEPS`), `POST /plan` runs the loop, `POST /plan/confirm` takes action ids and calls `confirm()`, with no model. Proof: `tests/test_agent.py`.
