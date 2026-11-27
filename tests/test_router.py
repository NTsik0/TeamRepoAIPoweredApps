"""Lab 8 tests, from Lab-8/templates/test_router.py. All offline: the "provider" is a small function
written here, so each test decides exactly which model is down. No key, no cost.

Tests 1 to 3 are the template, unchanged. Tests 4 to 6 are ours: complete_tools() raises httpx's
errors, not the OpenAI SDK's, and the starter's temporary() did not recognise them. Test 7 is the
Lab 7 loop running through the chain (Step 4).
"""
import httpx
import pytest

from src import router
from src.router import CACHE, CHAINS, SORRY, complete, summary

JOB = "chat"                                            # ADAPT only if your CHAINS has other job names
QUESTION = [{"role": "user", "content": "When is HW2 due in cs6920?"}]
FIRST, SECOND = CHAINS[JOB][0], CHAINS[JOB][1]          # fails here? your chain needs two models


class Down(Exception):
    status_code = 503


class OurBug(Exception):
    status_code = 400


def models(down=(), error=Down):
    """A fake provider. Models named in `down` raise; the others answer with their own name."""
    def call(messages, tools, timeout=None, model=None):
        if model in down:
            raise error(f"{model} is down")
        return {"content": f"answered by {model}", "tool_calls": [], "usage": {"cost_usd": 0.001}}
    return call


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    CACHE.clear()
    monkeypatch.setattr(router, "LOG", tmp_path / "router.jsonl")     # tests never touch your real log


def test_the_second_model_answers_when_the_first_is_down():
    answer = complete(QUESTION, job=JOB, call=models(down=[FIRST]))
    assert answer["content"] == f"answered by {SECOND}"
    assert summary()["answered_by_a_fallback"] == 1               # and the log says so


def test_everything_down_gives_a_sentence_not_a_stack_trace():
    answer = complete(QUESTION, job=JOB, call=models(down=CHAINS[JOB]))
    assert answer["content"] == SORRY and answer["degraded"] and answer["tool_calls"] == []
    assert not CACHE                                              # an apology is never cached


def test_our_own_bug_is_raised_not_hidden_by_the_next_model():
    with pytest.raises(OurBug):
        complete(QUESTION, job=JOB, call=models(down=[FIRST], error=OurBug))


# --- ours: the errors complete_tools() really raises -----------------------------------------

def openrouter(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return httpx.HTTPStatusError(f"{status}", request=request, response=httpx.Response(status, request=request))


def raising(first_error: Exception):
    """FIRST raises the given httpx error, the others answer."""
    def call(messages, tools, timeout=None, model=None):
        if model == FIRST:
            raise first_error
        return {"content": f"answered by {model}", "tool_calls": [], "usage": {"cost_usd": 0.001}}
    return call


@pytest.mark.parametrize("error", [openrouter(503), openrouter(429), httpx.ConnectError("refused"),
                                   httpx.ReadTimeout("no reply in 15 s")])
def test_an_openrouter_outage_moves_to_the_second_model(error):
    answer = complete(QUESTION, job=JOB, call=raising(error))
    assert answer["content"] == f"answered by {SECOND}"
    assert summary()["failed_attempts"] == 1 and summary()["answered_by_a_fallback"] == 1


@pytest.mark.parametrize("status", [400, 401, 403])
def test_an_openrouter_error_that_is_ours_is_raised(status):
    with pytest.raises(httpx.HTTPStatusError):
        complete(QUESTION, job=JOB, call=raising(openrouter(status)))
    assert summary()["answered_by_a_fallback"] == 0


def test_the_same_question_is_paid_for_once():
    calls = []

    def counting(messages, tools, timeout=None, model=None):
        calls.append(model)
        return {"content": "the Homework sentence", "tool_calls": [], "usage": {"cost_usd": 0.001}}
    first = complete(QUESTION, job=JOB, call=counting)
    second = complete(QUESTION, job=JOB, call=counting)
    assert first == second and calls == [FIRST]
    assert summary()["answered_from_cache"] == 1 and summary()["saved_by_cache_usd"] == 0.001


def test_the_week_7_loop_runs_through_the_chain():
    """Step 4: POST /plan hands the loop complete(). The first model is down for the whole run;
    the loop still finishes, and save_reminder is still parked, not run."""
    from src import memory
    from src.agent import run, student_key
    from tests.test_agent import NEEDS_A_YES, USER, scripted

    second = scripted([("find_deadlines", {"course": "cs6920", "about": "HW2"})], [NEEDS_A_YES],
                      "I proposed a reminder for HW2.")        # the same fake model as the Lab 7 tests

    def first_is_down(messages, tools, timeout=None, model=None):
        if model == FIRST:
            raise httpx.ReadTimeout("no reply in 15 s")
        return second(messages, tools)

    plan = run("remind me about HW2, due 2026-11-08", USER, llm=lambda m, s: complete(m, s, call=first_is_down))
    assert plan["status"] == "needs_confirmation" and len(plan["proposed"]) == 1
    assert memory.reminders(student_key(USER)) == []              # parked, not saved: the Lab 7 gate still holds
    assert summary()["answered_by_a_fallback"] == 3 and summary()["failed_attempts"] == 3
    assert summary()["sorry_message"] == 0 and not CACHE          # tool turns are never cached


def test_the_loop_says_the_sentence_when_every_model_is_down():
    from src.agent import run
    from tests.test_agent import USER

    plan = run("remind me about HW2, due 2026-11-08", USER, llm=lambda m, s: complete(m, s, call=models(down=CHAINS[JOB])))
    assert plan["text"] == SORRY and plan["proposed"] == []


def test_post_plan_uses_the_router():
    from src import app
    assert app.get_planner() is complete
