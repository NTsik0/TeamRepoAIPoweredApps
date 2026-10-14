# 0002 · Retrieve k = 5 chunks (tested against k = 8)

**Date:** Week 4 (2026-10-14) · **Decided by:** Nikoloz Tsikaridze

**Context.** The HW1 deadline appears in six of our twelve documents, and two of them (`homework/lab-1`, `homework/lab-2`) still give the old date. With the offline stand-in embeddings, the typo question g4 ("wen is hw1 due") did not retrieve the updated page, `milestones/hw1`, at k = 5, so we moved to k = 8 before running live. The live run decides.

**Decision.** k = 5 (`DEFAULT_K` in `src/answer.py`).

**Evidence.** All four runs are committed in `evals/results/`:

| Run | k | Right sources retrieved | Passed | Failed |
|---|---|---|---|---|
| offline | 5 | 4 / 5 | 2 / 5 | offline only: stand-in model cannot judge meaning |
| offline | 8 | 5 / 5 | 2 / 5 | same |
| **live** | **8** | 5 / 5 | 3 / 5 (0.60) | g2 (model: "sources do not answer"), g3 (citation list and `[n]` markers disagree) |
| **live** | **5** | 5 / 5 | **4 / 5 (0.80)** | g2 |

Live, real embeddings find `milestones/hw1` for g4 at k = 5, and g4 passes with the newer date. k = 8 gave the model three more chunks and one more failure (g3's reply cited sources inconsistently, so the citation check refused it). Fewer, better chunks won.

**Alternatives.** k = 8 (offline-only evidence, worse live, about 55% more prompt tokens). k = 3 (not measured; next candidate if cost matters).

**Consequences.** About $0.0016 per answer (average over 10 live calls, `evals/results/usage-2026-10-14-1942.json`). g2 still fails at both settings: tracked in the Design Review evaluation section. Offline tests still check retrieval at k = 8, because the offline stand-in embeddings are weaker than the real ones.
