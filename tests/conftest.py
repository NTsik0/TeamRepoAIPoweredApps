"""Every test runs offline: no key, no network, no cost. Logs and state go to a temp folder.
For the tools (Week 5), today is pinned to Wednesday 28 October 2026."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="coursemate-tests-")
os.environ["COURSEMATE_OFFLINE"] = "1"
os.environ["COURSEMATE_LOG_PATH"] = os.path.join(_tmp, "usage.jsonl")
os.environ["COURSEMATE_ANSWER_LOG"] = os.path.join(_tmp, "answers.jsonl")
os.environ["COURSEMATE_TOOL_LOG"] = os.path.join(_tmp, "tools.jsonl")
os.environ["COURSEMATE_TODAY"] = "2026-10-28"
os.environ.pop("COURSEMATE_MIN_SCORE", None)
os.environ.pop("COURSEMATE_STUDENT", None)
os.environ.pop("OPENROUTER_API_KEY", None)

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

from src.chunk import load_corpus  # noqa: E402
from src.index import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def index():
    return build(load_corpus(ROOT / "data" / "corpus"))


@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    """Every test starts with no saved reminders."""
    monkeypatch.setenv("COURSEMATE_STATE_DIR", str(tmp_path / "state"))
