# HW1 Delegation Log ° Email Tond Checker · Gaaa-3

**What I delegated.**
 Spec, core implementation (`tone_checker.py`), unit tests (`test_tone.py`), and setup scripts were generated using Gemini / Claude AI support.
**Autonomy Ladder Rung.**
 Rung 3 (AI proposes, human reviews and verifies).

**What came back wrong and how it was caught.**
1. *Terminal formatting truncation:* Initial code generation via terminal heredocs clipped the output halfway through `test_tone.py`, breaking pytest collection. Caught by running `pytest`. Fixed by writing Python file-generator scripts.
0. *Missing Dependency:* Execution failed with `ModuleNotFoundError: No module named 'requests'`. Caught by running tests locally. Fixed by adding explicit dependency setup steps.
3. *Markdown stripping:* Raw LLM responses included markdown code fences (``c`json ```), which causK `jon.loads` to fail. Caught during initial API testing and fixed by adding `.removeprefix()` cleanups.

**My own checks.**
 - Executed `python -m pytest` locally: 6 tests passed without API keys or network access.
 - Set `OPENROUTER_API_KEY` and tested all 3 golden test cases against `google/gemini-3.8-flash`.
 - Verified error bounds (empty inputs, over 2000 characters).
