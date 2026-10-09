"""HW1 Deadline Finder: AC1 to AC5 from hw1/NTsik0/spec.md. No test calls a real model."""
import json

import pytest

import deadlines
from deadlines import (MAX_CHARS, MAX_TOKENS, DeadlineError, LLMResult, deadline_sections,
                       find_deadlines, load_sections, main)


class FakeLLM:
    model = "fake/model"

    def __init__(self, payload):
        self.text = payload if isinstance(payload, str) else json.dumps(payload)
        self.calls = []

    def complete(self, messages, max_tokens):
        self.calls.append({"messages": messages, "max_tokens": max_tokens})
        return LLMResult(text=self.text, prompt_tokens=900, completion_tokens=120)


GOOD = {"deadlines": [
    {"item": "HW1 Spec to Ship", "due": "Thursday of Week 4 at 23:59 Tbilisi time", "section": "Homework"},
    {"item": "HW2 Tool Contract", "due": "at the end of Week 7", "section": "Homework"},
]}


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "usage.jsonl"


# --- AC1 · Grounded list ---------------------------------------------------

def test_ac1_returns_grounded_deadlines(log_path):
    out = find_deadlines("cs6920", FakeLLM(GOOD), log_path)
    assert out["course_id"] == "cs6920"
    assert out["dropped"] == 0
    assert [d["item"] for d in out["deadlines"]] == ["HW1 Spec to Ship", "HW2 Tool Contract"]
    assert set(out["deadlines"][0]) == {"item", "due", "section"}


def test_ac1_match_ignores_case_and_spacing(log_path):
    payload = {"deadlines": [{"item": "HW1", "due": "thursday of  week 4 at 23:59", "section": "Homework"}]}
    out = find_deadlines("cs6920", FakeLLM(payload), log_path)
    assert len(out["deadlines"]) == 1 and out["dropped"] == 0


def test_ac1_model_sees_only_deadline_sections(log_path):
    fake = FakeLLM(GOOD)
    find_deadlines("cs6920", fake, log_path)
    prompt = "\n".join(m["content"] for m in fake.calls[0]["messages"])
    assert "### Homework" in prompt
    assert "### AI use policy" not in prompt  # no deadline words in that section


# --- AC2 · Invented dates are dropped ----------------------------------------

def test_ac2_invented_due_is_dropped(log_path):
    payload = {"deadlines": [
        GOOD["deadlines"][0],
        {"item": "HW1", "due": "Friday of Week 4 at 18:00", "section": "Homework"},
    ]}
    out = find_deadlines("cs6920", FakeLLM(payload), log_path)
    assert len(out["deadlines"]) == 1
    assert out["dropped"] == 1


def test_ac2_section_not_sent_is_dropped(log_path):
    payload = {"deadlines": [{"item": "AI policy", "due": "Week 4", "section": "AI use policy"}]}
    out = find_deadlines("cs6920", FakeLLM(payload), log_path)
    assert out["deadlines"] == [] and out["dropped"] == 1


# --- AC3 · Errors --------------------------------------------------------------

@pytest.mark.parametrize("course_id", ["cs9999", "../AGENTS", ""])
def test_ac3_unknown_course_no_model_call(course_id, log_path):
    fake = FakeLLM(GOOD)
    with pytest.raises(DeadlineError) as e:
        find_deadlines(course_id, fake, log_path)
    assert e.value.code == "course_not_found"
    assert fake.calls == []


@pytest.mark.parametrize("bad", ["not json", '{"items": []}', '{"deadlines": [{"item": "x"}]}', "[]"])
def test_ac3_bad_model_output(bad, log_path):
    with pytest.raises(DeadlineError) as e:
        find_deadlines("cs6920", FakeLLM(bad), log_path)
    assert e.value.code == "model_bad_output"


def test_ac3_fenced_json_is_accepted(log_path):
    fenced = "```json\n" + json.dumps(GOOD) + "\n```"
    assert len(find_deadlines("cs6920", FakeLLM(fenced), log_path)["deadlines"]) == 2


def test_ac3_cli_error_shape_and_exit_code(capsys, monkeypatch):
    monkeypatch.setattr(deadlines, "OpenRouterClient", lambda: FakeLLM(GOOD))
    assert main(["cs9999"]) == 2
    err = json.loads(capsys.readouterr().out)
    assert err["error"]["code"] == "course_not_found" and err["error"]["message"]


def test_cli_success(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(deadlines, "OpenRouterClient", lambda: FakeLLM(GOOD))
    monkeypatch.setenv("HW1_LOG_PATH", str(tmp_path / "u.jsonl"))
    assert main(["cs6920"]) == 0
    assert json.loads(capsys.readouterr().out)["dropped"] == 0


# --- AC4 · Usage log -----------------------------------------------------------

def test_ac4_one_usage_line_per_call(log_path):
    find_deadlines("cs6920", FakeLLM(GOOD), log_path)
    find_deadlines("cs6920", FakeLLM(GOOD), log_path)
    lines = log_path.read_text().splitlines()
    assert len(lines) == 2
    entry = json.loads(lines[0])
    assert set(entry) == {"ts", "course_id", "model", "prompt_tokens", "completion_tokens", "latency_ms"}
    assert entry["prompt_tokens"] == 900 and entry["completion_tokens"] == 120


# --- AC5 · Cost cap --------------------------------------------------------------

def test_ac5_context_and_token_caps(log_path):
    fake = FakeLLM(GOOD)
    find_deadlines("cs6920", fake, log_path)
    assert fake.calls[0]["max_tokens"] == MAX_TOKENS == 1500
    secs = deadline_sections(load_sections("cs6920"))
    assert sum(len(s.text) for s in secs) <= MAX_CHARS


def test_ac5_cap_truncates_large_documents():
    from deadlines import Section
    big = [Section(f"S{i}", "due " * 2000) for i in range(5)]
    assert sum(len(s.text) for s in deadline_sections(big)) <= MAX_CHARS


# --- AC5 · Cut-off answers are reported, not misread ----------------------------

class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _fake_post(finish_reason, content):
    def post(url, headers, json, timeout):
        post.sent = json
        return _Resp({"choices": [{"finish_reason": finish_reason, "message": {"content": content}}],
                      "usage": {"prompt_tokens": 10, "completion_tokens": 393}})
    return post


def test_ac5_cut_off_answer_says_so(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(deadlines.httpx, "post", _fake_post("length", '{"deadlines": [{'))
    with pytest.raises(DeadlineError) as e:
        deadlines.OpenRouterClient().complete([], MAX_TOKENS)
    assert e.value.code == "model_bad_output"
    assert "cut off" in e.value.message


def test_ac5_client_sends_cap_and_low_reasoning(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    post = _fake_post("stop", json.dumps(GOOD))
    monkeypatch.setattr(deadlines.httpx, "post", post)
    result = deadlines.OpenRouterClient().complete([], MAX_TOKENS)
    assert post.sent["max_tokens"] == 1500
    assert post.sent["reasoning"] == {"effort": "low"}
    assert json.loads(result.text) == GOOD
