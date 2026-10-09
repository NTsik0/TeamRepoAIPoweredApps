# HW1 Golden questions · Deadline Finder · NTsik0

Three golden questions, run against the real model by `python hw1/NTsik0/src/run_golden.py` (needs `OPENROUTER_API_KEY`). The script writes the table below; results are never typed by hand.

What each one checks:
- **G1 (factual):** the most important deadline in the document comes back word for word.
- **G2 (grounding):** a second deadline in the same section is found, and the model invented nothing (`dropped` = 0).
- **G3 (edge case):** an unknown course fails cleanly with `course_not_found`, before any model call.

## Results

<!-- results:start -->
Run: 2026-10-09 20:33 UTC · model `google/gemini-3.8-flash` · **3/3 passed**

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| G1 | `cs6920`: is HW1 listed with its real deadline? | an item about HW1 whose `due` contains "Thursday of Week 4" and "23:59" | {"item": "HW1", "due": "Thursday of Week 4 at 23:59 Tbilisi time", "section": "Homework"} | PASS |
| G2 | `cs6920`: is HW2 listed, with nothing invented? | an item about HW2 whose `due` contains "end of Week 7", and `dropped` = 0 | {"item": "HW2 \"Tool Contract\"", "due": "at the end of Week 7", "section": "Homework"}; dropped=0 | PASS |
| G3 | `cs9999` (no such course) | error `course_not_found`, no model call | error course_not_found: no course document for 'cs9999' | PASS |
<!-- results:end -->

## If something fails
The first real run failed G1 and G2 (1/3 passed). Both returned `model_bad_output: model did not return JSON`. I printed the raw model answer: `TOKENS OUT: 393`, and the text stopped after `{"deadlines": [{`. The spec had set `max_tokens` to 400, but gemini-3.8-flash spends completion tokens on hidden reasoning, so the JSON was cut off before it finished.

Fix (commit "HW1: fix cut-off JSON from reasoning tokens"): the spec was updated first (AC5, success criterion 3, napkin math), then the code: `max_tokens` 1,500, reasoning effort `low`, and a cut-off answer now reports "answer cut off" instead of "did not return JSON". Two unit tests were added for it. Re-run after the fix: 3/3 passed (table above).

Note: G1 returned the item name as just "HW1" rather than "HW1 Spec to Ship". The check only needs "hw1" in the item and the exact deadline, so it passes, but item names are not consistent between runs.