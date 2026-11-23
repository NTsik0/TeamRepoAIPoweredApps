# Pattern Journal · Guram Tsiklauri (Gaaa-3) · Weeks 5 to 7

*One entry per week: the pattern, one place I saw or used it, what I noticed, and one thing I would do differently.*

## Week 5 · Tool Contract
*Written 2026-10-31*

**Where I used it:** twice. First as a reviewer: I approved Nikoloz's `find_deadlines` pull request (#18), which was the first tool in our repo written by one of us rather than copied from the lab. Then as the author of my own, `search_course_docs`, for HW2.

**What I noticed:** reviewing a tool is not reading the function. `call_tool()` in `src/act.py` runs three gates before anyone's code executes — is this tool offered to this caller, do the arguments pass the contract, and the caller's identity comes from the session — so almost everything that can go wrong is decided in `src/contracts.py`, in lines that look like nothing. I checked that by breaking them on purpose: with `extra="forbid"` changed to `extra="ignore"`, a `student: s999` smuggled into the arguments is silently dropped instead of refused, and two golden cases fail at once, mine and Nikoloz's. One line, two tools.

The second thing I noticed is about my own tool. The function it wraps already existed and already worked — `hybrid()` from Week 4 — so the slice was almost entirely contract. And writing the contract made the function better, which I did not expect. `hybrid()` always returns `k` sections, however irrelevant, so an off-topic question used to come back with the least bad match and nothing to say it was bad. Having to describe the tool's failures forced me to pick a relevance floor and write a refusal. That refusal is the only part of the tool that is really mine.

**Do differently:** write the failure message first, before the happy path. I wrote mine last and it showed: the first version named `data/corpus/` in the text, which tells the model about our filesystem and tells the student nothing.

## Week 6 · Session State
*Written 2026-10-31*

**Where I saw it:** in my own code, an hour after I thought the pattern did not apply to me. The rule is that every piece of state the product keeps gets one row — scope, lifetime, when it is written, how it is deleted — and if it has no row, the product does not keep it. My tool saves nothing per student, so I assumed it kept no state.

**What I noticed:** it does. `corpus_index()` is wrapped in `lru_cache`, and a cache is state: its scope is the process, its lifetime is "until the process restarts", it is written on the first call, and there is no way to clear it. That has a consequence I had not thought about. Rebuilding `data/index/` or adding a document to `data/corpus/` changes nothing for a running server — it keeps answering from the index it built when the first question arrived. And I did not invent this: `get_index()` in `src/app.py` has been doing the same thing since Week 4, which is why I copied the pattern without thinking about it. Two caches, one rule, and neither of them had a row written anywhere.

**Do differently:** write the row before the cache, not after. I only found it because I went looking for state rather than for bugs, and the fix cost one line in `docs/tool-contracts.md` ("built once per process; a rebuilt index or a changed corpus needs a restart"), which is exactly the thing a reviewer needs and the code does not say.

## Week 7 · Supervised Autonomy Loop
*Written 2026-11-23*

**Where I used it:** twice, and the second time was as the person who broke it on purpose. As a reviewer I read the Lab 7 PR (#27) — `docs/agent-contract.md` and `tests/test_agent.py` — before it merged. Then, for this entry, I ran the gate myself: on a clean `main` I changed one line in `src/agent.py`, `NEEDS_YES = {"save_reminder"}` to `NEEDS_YES = set()`, ran `pytest tests/test_agent.py -q`, and restored the file. Four of the five tests failed. That run is my evidence.

**What I noticed:** the gate is not a prompt, it is a branch. `run()` checks `if call["name"] in NEEDS_YES:` and parks the call instead of running it; the model is told "NOT saved"; the call only executes when a person confirms by id, through `confirm()`, which pops the plan and re-runs `call_tool()` so nothing skips the contract checks. With the gate off, `test_the_gate_blocks_until_a_person_says_yes` came back `answered` instead of `needs_confirmation`, and in `test_the_loop_stops_after_max_steps` a real `Reminder(course='cs6920', ... due='2026-11-08')` was already in the store even though the loop had stopped — stopping early is not the same as not writing. The one test that still passed was `test_the_loop_only_gets_the_tools_on_its_list`: being offered a tool and being allowed to run it are two different mechanisms, and breaking one does not break the other. That is the lecture line, "an instruction is not a permission system", in our own repo. `GOAL_PROMPT` tells the model to use only a date the student wrote and "never work a date out yourself", and nothing enforces that — the only protection is the `describe()` line the student reads before saying yes. The coding agent that wiped a production database during a code freeze is the same shape: the instruction was there, the permission was not.

**The one action that waits:** `save_reminder`. Contract item 3 says a wrong date is worse than none, and the course document says "Week 7", not dates, so only the student can confirm it. `search_course_docs` is not even offered to the loop — least privilege, item 2 — which is why my tool never appears in `LOOP_TOOLS`.

**Do differently:** treat the gate as a test surface, not a feature. The gate lives in one line, and one line is exactly what a reviewer skims past; the run I did took two minutes and would have caught a regression that green CI would not, because CI only tests that the gate is on. Next time I would make the "gate off" run a scripted check, not a manual one — same shape as the `extra="forbid"` break in Week 5.