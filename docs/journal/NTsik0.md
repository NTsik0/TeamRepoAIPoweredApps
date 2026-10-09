# Pattern Journal · Nika Tsikaridze (NTsik0)

*One entry per week, 2 to 3 sentences: pattern · where I applied it · what I delegated to AI · how I verified it. Graded only inside HW1 (Weeks 1 to 4), HW2 (Weeks 5 to 7) and one Repository Review line (Weeks 10 to 14). Honest beats polished.*

> DRAFT written with Claude from what happened in the repo. Rewrite every entry in your own words before HW1: the journal is graded as yours, and you must be able to explain each line.

## Week 1 · Context as Budget
Applied it in the spec's napkin math: I first estimated 2,500 prompt tokens per question, then capped context at 3 sections and 4,000 characters (spec AC5), which cut the estimate from about $24 to about $16 a month. Delegated the arithmetic to Claude; verified it by redoing it by hand: 1,300 × $0.75 + 200 × $3.75 per million tokens, × 300 requests × 30 days.

## Week 2 · Spec Before Code
Applied it by upgrading spec v0 to v1 before any code existed, so each acceptance criterion names the exact status code, field or log line a test checks. Delegated the critique of spec v0 and the build of the first slice (AC1, AC2, AC4) to Claude (Opus 5.5) with a plan-first prompt. Verified by reading `tests/test_ask.py` before `src/`, running `pytest` myself. [Lab 1 drill: name one suggestion from the agent's spec critique that you rejected, and why. Use one you actually rejected; `docs/spec-critique.md` lists what came back.]

## Week 3 · Uncertainty-Aware UX

## Week 4 · Grounded Generation
