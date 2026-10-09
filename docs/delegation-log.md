# Delegation log · KIU CourseMate

One entry per delegation that mattered. Two minutes each. HW1 asks for half a page of these.

Format:

### Entry N · [task in five words]
- **Task:** [which acceptance criteria]
- **Delegated to:** [tool, model, what context it had]
- **Plan check:** [what you changed before approving, or "approved as proposed"]
- **Came back wrong:** [be specific; "nothing" is allowed only if you say what you checked]
- **Caught by:** [which gate: plan, tests-first reading, running tests, CI, a teammate]
- **Decision:** [merged, fixed, rejected and re-delegated]
- **AGENTS.md change:** [the line you added, or why none was needed]
- **Cost:** [minutes, extra runs]

---

### Entry 1 · First slice: /ask endpoint
- **Task:** AC1 (grounded answer), AC2 (refusal with no model call), AC4 (usage log). Branch `slice-1-ask-endpoint`.
- **Delegated to:** Claude (Opus 5.5) in a Claude cloud session, asked to "do everything for Lab 1 and Lab 2". Context: `docs/spec.md` v1, `AGENTS.md` v2, `data/courses/cs6920.md`.
- **Plan check:** Gate 1 was NOT done by a human: the agent planned and built in one run. The plan it followed: `courses.py` (split at `## `), `retrieve.py` (keyword overlap), `llm.py` (one `call_and_log` so no route can call the model without logging), `app.py`, tests with a fake model via dependency override. [Reviewer: check this plan against AC1, AC2, AC4 before approving the PR.]
- **Came back wrong:** while writing `test_ac1_model_sees_only_retrieved_sections`, the agent saw that plain keyword overlap would send Watch-checks and Demo Day for "When is HW1 due?" (they contain "due"), breaking the Context list. Fixed before the first run with a relative threshold (keep sections scoring at least 0.6 of the best).
- **Caught by:** tests-first: that test asserts Watch-checks text is not in the prompt. Then three deliberate breakages (always call the model, skip the log write, remove the threshold): each made at least one test fail. 17 tests pass with no `OPENROUTER_API_KEY` and no network. [Reviewer: run `pytest` yourself and read the output.]
- **CI caught:** first CI run failed: `ModuleNotFoundError: No module named 'src'`. The agent had run tests with `python -m pytest`, which puts the repo root on the import path; CI runs plain `pytest`, which does not. Fixed with `pythonpath = .` in `pytest.ini`; reproduced the failure locally with `python -P -m pytest` (2 errors) and confirmed the fix (17 passed) before pushing.
- **Decision:** merged. Gaaa-3 (Guram Tsiklauri) approved PR #2 and squash-merged it on 2026-10-09, after CI went green on the fix.
- **AGENTS.md change:** "Always" line now says to run plain `pytest`, not `python -m pytest`, because that difference hid the CI failure. Gotcha: a stale `__pycache__` made one restored run look red; clear it if results look impossible.
- **Cost:** one session, 5 test runs, 0 model calls.
