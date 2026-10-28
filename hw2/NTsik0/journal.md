# Pattern Journal · Nikoloz Tsikaridze (NTsik0) · Weeks 5 to 7

*Copied from `docs/journal/NTsik0.md`. One entry per week: the pattern, one place I saw or used it, one thing I would do differently.*

## Week 5 · Tool Contract
*Written 2026-10-28*

**Where I used it:** our team tool `save_reminder` lets the model save a deadline reminder for the signed-in student. The model only asks; `call_tool()` decides: is the tool offered to this caller, do the arguments pass the contract, and the student comes from the `X-Student-Id` header, never from the model. A test sends `student: "s999"` in the arguments and checks that nothing is saved. **What I noticed:** that test only works because of one setting. When we changed `extra="forbid"` to `extra="ignore"` as an experiment, the extra `student` field was silently dropped and the test went red; one line of the contract is the whole defence. **Do differently:** do the lab in its own week. I built this on 28 October, six days after the lab, so I could not ask questions during the live demo.


## Week 6 · Session State
*To be written after the Week 6 lecture (29 October 2026).*

## Week 7 · Supervised Autonomy Loop
*To be written after the Week 7 lecture (5 November 2026).*
