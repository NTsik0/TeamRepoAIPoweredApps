# Milestone 1 · HW1 "Spec to Ship" · what you hand in, where, and when

**Milestone 1 is HW1.** Same deliverables as announced in Lab 1, one week more time. This page is the single source of truth for it. If any other file in this repo, or your copy of `docs/TEAM-REPO.md`, says a different date, this page wins.

**Milestone 1 = HW1 · "Spec to Ship" · 5 points · individual**
**Due: before Week 5 · Tuesday 20 October 2026, 23:59 (Tbilisi time). Extended by one week from the original Week 4 date.**
**Submit: push to `hw1/<your-github-username>/` in your team repo (four files and one `src/` folder), then fill the submission form (link on Teams)**
**Deliver: a one-page spec, the working feature it describes, 3 golden questions with results, a half-page delegation log, and your Pattern Journal for Weeks 1 to 4**
**Full brief, folder layout and checklist: `Lab-3/MILESTONE-1.md`**

---

## 1 · What changed, and what did not

| | Before | Now |
|---|---|---|
| Deadline | Thursday of Week 4 | **Tuesday 20 October 2026, 23:59 Tbilisi time**, before the Week 5 lab |
| Deliverables | spec, feature, 3 golden questions, delegation log, journal Weeks 1 to 4 | unchanged |
| Points | 5, individual | unchanged |
| Where | `hw1/<your-github-username>/` + the form on Teams | unchanged |

Why the extension: the homework information was spread across several files and some of you could not tell what to upload where. That is on me. This page fixes it; the extra week makes sure nobody is penalised for it.

## 2 · The one feature

HW1 is the whole Week 2 method, done once, alone, end to end: write a spec, delegate the build, review it, prove it with golden questions, log what went wrong.

Pick **one small feature**. Small enough to spec on one page and build in a week; real enough to need three golden questions.

- Too big: "a full recommendation engine".
- Good: "given a club name, return its next three events with room and time".
- Too small: "a function that formats a date".

It can be CampusPulse-adjacent, or a piece of your own capstone. Either way **you build it alone, inside your own `hw1/` folder.** It is not the team slice that was merged in Lab 2 or Lab 3, and no teammate edits it.

## 3 · Exactly what is in your folder

```
hw1/<your-github-username>/
├── spec.md          one page: goal, users, acceptance criteria, context list, out of scope
├── golden.md        3 golden questions: question · expected · actual · pass or fail · how you ran it
├── delegation.md    half a page: what you delegated, what came back wrong, how you caught it
├── journal.md       your Pattern Journal entries for Weeks 1, 2, 3 and 4 (copied from docs/journal/<username>.md)
└── src/             the working feature, with at least one test that runs with `pytest hw1/<username>`
```

A filled example for a CampusPulse feature is in `Lab-3/examples/hw1-example/`. Copy its shape, not its content.

**`spec.md`, one page.** Use the Week 2 spec format (`Lab-2/templates/spec-v1-upgrade.md` is the checklist). Every acceptance criterion must be decidable by a script: "returns the next three events sorted by start time; returns an empty list and HTTP 200 when the club has none" passes; "works well" does not. At least one criterion covers an error case.

**`src/`, the feature.** Runs from a fresh clone with the commands written at the top of `spec.md`. If it calls a model, the call goes through an `llm.py` that logs tokens, cost and latency, and the key comes from the environment, never from a file in the repo. Tests never call a real model.

**`golden.md`, three golden questions.** For each: the input, the expected output, the actual output you got, pass or fail, and the command or steps you used. A failing golden question, documented as a failure, is fine. Three passes with no evidence of having been run is not.

**`delegation.md`, half a page.** What you asked the agent to do, at which rung of the Autonomy Ladder, what it got wrong (there is always something), and how you caught it: a test, a diff read, a golden question. Same format as the team log from Lab 2 (`Lab-2/templates/delegation-log.md`).

**`journal.md`, Weeks 1 to 4.** Four entries, one per week, copied from your `docs/journal/<username>.md`. Each entry: the pattern of the week, one place you saw it or used it, one thing you would do differently. The Week 4 entry is written after the Week 4 lecture, which is why the deadline is after it.

## 4 · How to submit, step by step

1. In your team repo: `git switch main && git pull && git switch -c hw1-<your-github-username>`
2. Create `hw1/<your-github-username>/` with the five items above. Commit from your own GitHub account.
3. Run your tests: `pytest hw1/<your-github-username>`. Green before you push.
4. Push and open a pull request into `main`. Title: `HW1 · <your-github-username>`.
5. A teammate approves and merges. They check one thing only: that every changed file is inside your own `hw1/<your-github-username>/` folder. They do not edit or improve your work.
6. Open the submission form (link pinned on Teams), paste the link to your merged folder on `main` (`https://github.com/<org-or-user>/<team-repo>/tree/main/hw1/<your-github-username>`), submit.

Both parts count. A folder on `main` without the form, or a form without the folder, is not a submission.

## 5 · Before you press submit

- [ ] `hw1/<your-github-username>/` is on `main`, merged through a pull request, not pushed directly
- [ ] `spec.md` fits on one page and every criterion is testable
- [ ] `src/` runs from a fresh clone using only the commands in `spec.md`
- [ ] `pytest hw1/<your-github-username>` is green and no test needs an API key
- [ ] `golden.md` shows actual outputs, not just expected ones
- [ ] `delegation.md` names at least one thing the agent got wrong and how you caught it
- [ ] `journal.md` has four dated entries, Weeks 1 to 4
- [ ] No key, no `.env`, no personal data anywhere in the folder
- [ ] The form is submitted with the link to your folder on `main`

## 6 · How it is graded (5 points)

| Part | Weight | What earns it |
|---|---|---|
| Correctness | 40% | the feature does what the spec says; golden questions were actually run |
| Code quality | 20% | readable, small, tests that could fail if the feature broke |
| Documentation and journal | 20% | a one-page spec a stranger could build from; four honest journal entries |
| Verification evidence | 20% | the delegation log shows what went wrong and how you caught it |

A working feature with an honest delegation log beats an impressive feature with vague evidence. Every time.

## 7 · Questions I expect

**Can I use the agent for all of it?** Yes. AI is permitted for everything in the repo. Log it. The only places AI is not allowed are the quizzes and the midterm.

**Can my HW1 feature become part of the team capstone later?** Yes, after the deadline, through the normal slice workflow. Until then it stays in your `hw1/` folder.

**My teammate has not merged my pull request.** Ask once on your team channel. If it is still open 24 hours before the deadline, email the instructor (email on Teams) with the pull request link; the open pull request counts as submitted on time.

**Does the team contract have the same deadline?** No. `TEAM-CONTRACT.md` is a team file, due at the end of Week 3, and it is part of the Design Review. See `SUBMISSIONS.md` at the repo root for every deadline in one table.

**Where do I ask?** Teams, in the course channel, so everyone sees the answer. Office hours over Google Meet, booked by email.
