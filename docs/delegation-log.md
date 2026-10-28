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

### Entry 2 · Lab 4: grounded answers
- **Task:** `docs/retrieval-spec.md` AC1 to AC5: corpus, chunking, hybrid retrieval, citation check, refusal, golden set. Branch `slice-lab4-grounded`.
- **Delegated to:** Claude (Opus 5.5), pointed at `docs/retrieval-spec.md`, `AGENTS.md` and the course reference `Lab-4/examples/campuspulse-rag/`. Rung 3 in name; the plan was not approved before files were written, so the reviewer reads every line of the diff.
- **Came back wrong:** (1) the refusal threshold copied from the reference (0.25) refused a real question offline ("When is HW1 due?" scored 0.23, gibberish 0.11); set to 0.15 for the offline model only. (2) Offline, at k = 5 the updated HW1 page was not retrieved for "wen is hw1 due", so the agent moved to k = 8; the live run reversed it (k = 5: 4/5, k = 8: 3/5), decision 0002. (3) Moving to k = 8 made the invented-citation test meaningless, because `[7]` became a valid source; the test now uses `[12]`, which stays invalid at either k. (4) The course pages contained the instructor's name and email; replaced, because the corpus must hold no personal data.
- **Caught by:** running the golden set offline and reading which sources were retrieved; a failing test after the k change; reading the corpus before committing it.
- **Verified:** 54 offline tests pass with no key. Removing each refusal route (threshold, model-says-no, citation check) makes at least one test fail. Live golden run by Nikoloz on 2026-10-14: k = 5 passed 4/5 (0.80), k = 8 passed 3/5; g2 fails at both (the model says the sources do not answer although `course/overview` was retrieved). Cost about $0.0016 per answer, latency p50 4.7 s, p95 14.1 s (`evals/results/usage-2026-10-14-1942.json`).
- **Decision:** [fill in after review]
- **AGENTS.md change:** grounding rules added (see AGENTS.md "Never" and conventions).
- **Cost:** one session; live runs cost $0.016 in total (22 model calls).

### Entry 3 · Lab 3: deadline from a photo
- **Task:** `docs/multimodal-spec.md` AC1 to AC5 and `docs/confidence-policy.md`. Branch `slice-lab3-deadline-photo`.
- **Delegated to:** Claude (Opus 5.5), pointed at both docs, `AGENTS.md` and the course reference `Lab-3/examples/poster-extraction/`. Spec and policy were written and committed before the code. The four photos were taken by Nikoloz.
- **Came back wrong:** (1) the first test for "a guessed date without evidence" used confidence 0.95, so swapping the order of the checks (confidence before evidence) broke nothing: no test protected the policy's "evidence before confidence" rule. Found by deliberately breaking `decide()` four ways; three were caught, this one was not. Added `test_evidence_is_checked_before_confidence` (no evidence and confidence 0.2 must be hard); the mutation now fails. (2) The first clean screenshot candidate showed browser tabs with a teammate's real name; the cropped screenshot was used instead.
- **Caught by:** mutation check; reading the images before committing them.
- **Verified:** 77 offline tests pass with no key. Live run by Nikoloz on 2026-10-14 (`evals/results/2026-10-14-2009-images.json`): 4/4 routed as expected. clean → accepted (`2026-10-20`, `23:59`); degraded → review; ambiguous → confirm ("Which date is 'next tuesday'?"); mouse → rejected. One surprise: on the blurred photo the model read the date with evidence but not the item, so `item` (not `due_date`, as the spec predicted) was the hard field. The spec now records what happened.
- **Decision:** [fill in after review]
- **AGENTS.md change:** downscale and nullable evidence convention; "Never prefill a low-confidence or unevidenced value".

### Entry 4 · Lab 5: the tool contract
- **Task:** Lab 5 Parts 1 to 3 and the studio: `docs/tool-contracts.md` for `save_reminder`, the contract class, the tool, `call_tool()` with the three gates, the loop, `complete_tools()` in `llm.py`, `POST /act`, the MCP server, tests, `tests/test_tool_golden.py` and `evals/tools/`. Branch `slice-lab5-tools-mcp`.
- **Delegated to:** Claude (Opus 5.5), pointed at `docs/tool-contracts.md`, `AGENTS.md` and `Lab-5/examples/campuspulse-tools/`. Rung 3: the plan (tool choice, files, the `mcp>=2.3` dependency, HW2 owners) was proposed first and approved by Nikoloz on 2026-10-28 before any file was written. The two lines the agent had to follow: arguments are validated against the contract before the tool runs, a failure goes back to the model as an error and nothing runs; the caller's identity is never a tool argument.
- **Came back wrong:** (1) the agent first added a line to the module docstring of `llm.py`, although the lab says nothing else in that file changes; reverted, so the `llm.py` diff only adds `complete_tools()`. (2) The installed MCP SDK was 2.2.0, below the `mcp>=2.3` the lab requires; upgraded before running the tests, so the tests ran on the version in `requirements.txt`.
- **Caught by:** reading the `llm.py` diff for removed lines; checking `importlib.metadata.version("mcp")`. Two mutations of the contract: with `extra="ignore"` instead of `"forbid"`, `test_model_cannot_choose_the_student` fails; without the `title` pattern, `test_invalid_arguments_never_reach_the_tool` fails. Both restored.
- **Verified:** 103 offline tests pass with no key (1 skipped: `tests/test_tool_golden.py` has no cases until HW2 adds `evals/tools/<username>.yaml`). Live check by Nikoloz on 2026-10-28 (`POST /act`, `X-Student-Id: nikoloz`, google/gemini-3.8-flash): "Remind me about HW2 Tool Contract due 2026-11-08, 3 days before". The model's first call sent `course: "CS6920"`; the contract refused it before the tool ran (`invalid arguments: course: Input should be 'cs6920'`). The model read the error, called again with `cs6920`, and the reminder was saved (`remind_on` 2026-11-05). The same question a second time returned `already saved` with 1 reminder: idempotent. Both lines from `logs/tools.jsonl` (14:54 UTC run):
  ```
  {"ts": "2026-10-28T14:54:22+00:00", "tool": "save_reminder", "ok": false, "error": "invalid arguments: course: Input should be 'cs6920'", "student": "02f053fefa08", "latency_ms": 0}
  {"ts": "2026-10-28T14:54:25+00:00", "tool": "save_reminder", "ok": true, "error": null, "student": "02f053fefa08", "latency_ms": 7}
  ```
  (arguments left out here for length; the full lines are in the log.) The student is stored and logged only as a hash.
- **Decision:** [fill in after review]
- **AGENTS.md change:** two "Never" lines (no identity in tool arguments; no tool that deletes or sends without asking) and a tools convention.
- **Cost:** one session, 0 live model calls by the agent.

