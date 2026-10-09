"""Smoke test: the test command is real and the repo layout is in place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_repo_layout():
    for required in ["AGENTS.md", "docs/spec.md", "docs/TEAM-REPO.md", ".env.example"]:
        assert (ROOT / required).exists(), f"missing {required}"


def test_no_env_file_committed():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()
