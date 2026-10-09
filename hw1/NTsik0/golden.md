# HW1 Golden questions · Deadline Finder · NTsik0

Three golden questions, run against the real model by `python hw1/NTsik0/src/run_golden.py` (needs `OPENROUTER_API_KEY`). The script writes the table below; results are never typed by hand.

What each one checks:
- **G1 (factual):** the most important deadline in the document comes back word for word.
- **G2 (grounding):** a second deadline in the same section is found, and the model invented nothing (`dropped` = 0).
- **G3 (edge case):** an unknown course fails cleanly with `course_not_found`, before any model call.

## Results

<!-- results:start -->
NOT RUN YET. Run `python hw1/NTsik0/src/run_golden.py` with your key exported; it replaces this block.
<!-- results:end -->

## If something fails
[Write it here: what failed, why you think it failed, and whether you fixed it (link the commit) or why not. The brief says hiding a failure costs more than the failure.]
