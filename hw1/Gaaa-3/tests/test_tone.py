import pytest
from src.tone_checker import parse_response, check_email

def test_parse_valid_json():
    raw = '{"tone": "polite", "reason": "Good", "suggested_fix": "None"}'
    res = parse_response(raw)
    assert res["tone"] == "polite"


def test_parse_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_response("Not json")


def test_parse_invalid_tone():
    raw = '{"tone": "angry", "reason": "Bad", "suggested_fix": "Relax"}'
    with pytest.raises(ValueError, match="Tone must be polite, neutral, or rude"):
        parse_response(raw)


def test_check_email_empty():
    with pytest.raises(ValueError, match="Email is empty"):
        check_email("   ")


def test_check_email_too_long():
    with pytest.raises(ValueError, match="Email too long"):
        check_email("a" * 2001)


def test_check_email_e2e():
    def fake_llm(prompt):
        return '{"tone": "rude", "reason": "Short", "suggested_fix": "Add please"}'
    res = check_email("Do it now", llm=fake_llm)
    assert res["tone"] == "rude"
