"""First slice: AC1 (grounded answer), AC2 (refusal, no model call), AC4 (usage log).

No test here calls OpenRouter: the model is replaced by FakeLLM through a FastAPI
dependency override, so CI runs without a key or network.
"""
import json

import pytest
from fastapi.testclient import TestClient

from src.app import REFUSAL, app, get_llm, get_log_path
from src.llm import LLMResult


class FakeLLM:
    model = "fake/model"

    def __init__(self, text="HW1 is due Thursday of Week 4 at 23:59 Tbilisi time. [Homework]"):
        self.text = text
        self.calls = []

    def complete(self, messages, max_tokens):
        self.calls.append({"messages": messages, "max_tokens": max_tokens})
        return LLMResult(text=self.text, prompt_tokens=812, completion_tokens=24)


@pytest.fixture
def fake():
    return FakeLLM()


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "usage.jsonl"


@pytest.fixture
def client(fake, log_path):
    app.dependency_overrides[get_llm] = lambda: fake
    app.dependency_overrides[get_log_path] = lambda: log_path
    yield TestClient(app)
    app.dependency_overrides.clear()


def ask(client, question, course_id="cs6920"):
    return client.post("/ask", json={"course_id": course_id, "question": question})


# --- AC1 · Grounded answer -------------------------------------------------

def test_ac1_matching_question_returns_model_answer_with_sources(client, fake):
    r = ask(client, "When is HW1 due?")
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["course_id"] == "cs6920"
    assert body["answer"] == fake.text
    assert "Homework" in body["sources"]
    assert 1 <= len(body["sources"]) <= 3


def test_ac1_model_sees_only_retrieved_sections(client, fake):
    ask(client, "When is HW1 due?")
    assert len(fake.calls) == 1
    prompt = "\n".join(m["content"] for m in fake.calls[0]["messages"])
    # The HW1 deadline text is in the prompt ...
    assert "Thursday of Week 4 at 23:59" in prompt
    # ... but an unrelated section is not.
    assert "watch-check on the lecture recording" not in prompt


def test_ac1_model_called_with_max_tokens_cap(client, fake):
    ask(client, "How many points is the midterm exam worth?")
    assert fake.calls[0]["max_tokens"] == 300


# --- AC2 · Refusal, no model call ------------------------------------------

def test_ac2_unmatched_question_refuses_without_calling_model(client, fake):
    r = ask(client, "What is the weather in Batumi tomorrow?")
    assert r.status_code == 200
    assert r.json() == {
        "course_id": "cs6920",
        "answer": "I can't find that in the course documents.",
        "found": False,
        "sources": [],
    }
    assert fake.calls == []


def test_ac2_model_refusal_is_reported_as_not_found(client, log_path):
    refusing = FakeLLM(text=REFUSAL)
    app.dependency_overrides[get_llm] = lambda: refusing
    body = ask(client, "When is HW1 due?").json()
    assert body["found"] is False
    assert body["sources"] == []
    assert body["answer"] == REFUSAL


# --- AC4 · Usage log -------------------------------------------------------

def test_ac4_each_model_call_writes_one_usage_line(client, log_path):
    ask(client, "When is HW1 due?")
    ask(client, "How many points is the midterm exam worth?")
    lines = log_path.read_text().splitlines()
    assert len(lines) == 2
    entry = json.loads(lines[0])
    assert set(entry) == {"ts", "course_id", "model", "prompt_tokens", "completion_tokens", "latency_ms"}
    assert entry["course_id"] == "cs6920"
    assert entry["model"] == "fake/model"
    assert entry["prompt_tokens"] == 812
    assert entry["completion_tokens"] == 24
    assert entry["latency_ms"] >= 0


def test_ac4_log_never_contains_question_text(client, log_path):
    ask(client, "When is HW1 due?")
    assert "HW1" not in log_path.read_text()


def test_ac4_refusal_without_model_call_writes_no_usage_line(client, log_path):
    ask(client, "What is the weather in Batumi tomorrow?")
    assert not log_path.exists() or log_path.read_text() == ""


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
