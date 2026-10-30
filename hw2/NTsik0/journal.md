# Pattern Journal · Nikoloz Tsikaridze (NTsik0) · Weeks 5 to 7

*Copied from `docs/journal/NTsik0.md`. One entry per week: the pattern, one place I saw or used it, one thing I would do differently.*

## Week 5 · Tool Contract
*Written 2026-10-28*

**Where I used it:** our team tool `save_reminder` lets the model save a deadline reminder for the signed-in student. The model only asks; `call_tool()` decides: is the tool offered to this caller, do the arguments pass the contract, and the student comes from the `X-Student-Id` header, never from the model. A test sends `student: "s999"` in the arguments and checks that nothing is saved. **What I noticed:** that test only works because of one setting. When we changed `extra="forbid"` to `extra="ignore"` as an experiment, the extra `student` field was silently dropped and the test went red; one line of the contract is the whole defence. **Do differently:** do the lab in its own week. I built this on 28 October, six days after the lab, so I could not ask questions during the live demo.


## Week 6 · Session State
*Written 2026-10-30*

**Where I saw it:** in the Week 6 lecture. Weeks 1 to 5 were about what the model says and does; Week 6 was about how the app feels to use, and what it has to remember so that it feels like one conversation. The "four-second silence" example stuck with me: if nothing happens for four seconds, the person thinks it is broken, even when the answer is correct. I also liked the "One row per thing you remember" slide: every piece of memory gets one row with scope, lifetime, when it is written and how it is deleted, and if it is not in the table, the product does not store it. The rule I wrote in my notes was "the code and the table must agree." **What I noticed:** our own `save_reminder` tool from Lab 5 already stores something per student (`state/reminders.json`, keyed by a hash). It has a scope (the student) and a write rule (only when the student asks), but no lifetime and no way to delete it. So by the lecture's rule, our code stores a row that our docs never described. **Do differently:** before adding any memory, write its row first: scope, lifetime, when it is written, how it is deleted, plus a test for each. For reminders that means a lifetime (for example, delete after the due date) and a "forget me" path.

## Week 7 · Supervised Autonomy Loop
*To be written after the Week 7 lecture (5 November 2026).*
