# HW1 Delegation log · Deadline Finder · NTsik0

**What I delegated.** Spec, code, tests and the golden runner were drafted by Claude (Opus 5.5) in a Claude cloud session, from my request to "do HW1". It had the HW1 brief, the team `AGENTS.md` and spec, and the CS6920 course document. Order of work: spec committed first (commit "HW1: add spec…"), then tests, then code.

**What came back wrong, and how it was caught.**
1. *Carried over from the team slice the same night:* CI failed with `No module named 'src'` because the agent had tested with `python -m pytest`, which adds the repo root to the import path; CI runs plain `pytest`. Caught by CI. For HW1 this shaped the setup: a `conftest.py` puts `hw1/NTsik0/src` on the path, and tests were run with `python -P -m pytest`, which behaves like plain `pytest`.
2. *Design choice made at spec time, not a failure:* the prompt asks the model to copy deadlines word for word, but the spec does not trust that. AC2 puts the check in code: any `due` not found in the cited section is dropped and counted. A model can ignore a prompt; it can't get past a substring check.
3. *Nothing else failed during the build.* What was checked: 18 unit tests pass with no key and no network; three deliberate breakages (remove the grounding check, remove the section filter, raise the token cap) each made at least one test fail; the golden runner was dry-run with a fake model in a scratch copy to confirm it writes the table.

**What was NOT verified by the agent.** The golden questions against the real model: no API key in that session. Results in `golden.md` come only from my run of `run_golden.py`.

**My own checks.** [Fill in honestly before submitting: e.g. "read tests before code", "ran `pytest hw1/NTsik0`: N passed", "ran the golden script: N/3", "ran the CLI on cs6920 and compared each deadline with the document", plus anything you changed and why.]
