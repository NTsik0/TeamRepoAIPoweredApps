"""Every test runs offline: no key, no network, no cost. Logs go to a temp folder."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="coursemate-tests-")
os.environ["COURSEMATE_OFFLINE"] = "1"
os.environ["COURSEMATE_LOG_PATH"] = os.path.join(_tmp, "usage.jsonl")
os.environ["COURSEMATE_ANSWER_LOG"] = os.path.join(_tmp, "answers.jsonl")
os.environ.pop("COURSEMATE_MIN_SCORE", None)
os.environ.pop("OPENROUTER_API_KEY", None)

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

from src.chunk import load_corpus  # noqa: E402
from src.index import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def index():
    return build(load_corpus(ROOT / "data" / "corpus"))
