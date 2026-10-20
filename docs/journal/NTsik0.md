# Pattern Journal · Nikoloz Tsikaridze (NTsik0)

*One entry per week: the pattern, one place I saw or used it, one thing I would do differently. Weeks 1 to 4 are copied into `hw1/NTsik0/journal.md`.*

## Week 1 · Context as Budget
*Written 2026-10-09, revised 2026-10-14*

**Where I used it:** the napkin math of our team spec. Capping the context at 3 sections and 4,000 characters (about 1,300 prompt tokens) brought the monthly estimate from about $24 down to about $16; I had Claude do the arithmetic and redid it by hand (1,300 × $0.75 + 200 × $3.75 per million tokens, × 300 requests × 30 days). **What I noticed:** in HW1 my first budget was wrong because the model spent 393 of 400 tokens on hidden reasoning, so reasoning tokens count against the budget too. **Do differently:** read the cost from the usage log after the first real call instead of trusting my estimate; my log now records `cost_usd` for every call.

## Week 2 · Spec Before Code
*Written 2026-10-09, revised 2026-10-14*

**Where I used it:** upgrading the team spec to v1 and writing the HW1 spec before any code, with acceptance criteria a test can decide on its own. Claude did the spec critique, the first team slice and the HW1 build; I read the tests before the code, ran `pytest` myself, and CI caught a real bug (`No module named 'src'`). From the critique we did not take the idea of storing every question in a database, because our spec says no personal data and a question can contain a student's name. **What I noticed:** twice the bug was in the spec, not the code: the token budget forgot reasoning tokens, and I never wrote down that the log needs cost. **Do differently:** approve the agent's plan before it writes any file. In the team slice the agent planned and built in one run, which skipped Gate 1.

## Week 3 · Uncertainty-Aware UX
*Written 2026-10-12, revised 2026-10-14 and 2026-10-20*

**Where I used it:** both features say clearly when they do not know instead of guessing. CourseMate answers "I can't find that in the course documents" without calling the model; HW1 reports how many deadlines it `dropped` and says "answer cut off" when the model's reply is incomplete. Tests check the exact refusal text and the cut-off error, and I saw the cut-off case happen for real in my first golden run. **What I noticed:** the first error message, "model did not return JSON", was true but misleading; a clear reason is part of the UX, not a detail. **Do differently:** do the lab in its own week. Our team did the Week 3 multimodal lab late, on 2026-10-14; it added the proper version of this pattern: a deadline read from a photo is accepted, sent to the user to confirm, or sent to review, depending on the evidence and confidence, instead of being guessed.

## Week 4 · Grounded Generation
*Written 2026-10-12, revised 2026-10-14, finished 2026-10-20*

**Where I used it:** in HW1 the model only sees the course sections that mention deadlines, and my code drops any deadline that does not appear word for word in the section it cites, so the model cannot invent a date. A unit test where a fake model invents a date checks that it gets dropped, and golden question G2 against the real model returned `dropped=0`, 3/3 passed. **What I noticed:** the check is in code, not in the prompt, so it holds even when the model ignores the instruction. **Do differently:** add a golden question for a deadline outside the Homework section (for example the team contract) to test that grounding works across sections, not only in one.

*Added 2026-10-20 · I missed the live Week 4 lecture and lab, so this comes from our own Lab 4 work.* Offline, our stand-in embeddings made us raise the number of retrieved chunks from k = 5 to k = 8. The live run with the real model reversed it: k = 5 passed 4 of 5 golden questions and k = 8 passed 3 of 5, because with three more chunks one answer cited its sources inconsistently and the citation check refused it (decision record 0002). **Lesson:** more context is not more grounding; fewer, better chunks won, and only a live golden run showed it.
