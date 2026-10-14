"""decide() for deadline photos (docs/confidence-policy.md). Hand-written extractions, no model."""
from datetime import date

import pytest

from src.deadline_checks import decide, for_display, parse_date
from src.deadline_extract import DeadlineExtraction, Field

TODAY = date(2026, 10, 14)


def f(value, evidence="same", confidence=0.95):
    return Field(value=value, evidence=value if evidence == "same" else evidence, confidence=confidence)


def none():
    return Field(value=None, evidence=None, confidence=0.0)


@pytest.fixture
def clean():
    """What we expect for tests/images/clean.jpg (the Lab 4 homework screenshot)."""
    return DeadlineExtraction(
        item=f('Milestone 1 = HW1 "Spec to Ship"', 'Milestone 1 = HW1 · "Spec to Ship"'),
        due_date=f("2026-10-20", "Tuesday 20 October 2026"),
        due_time=f("23:59", "23:59 (Tbilisi time)"),
        course=none(),
    )


def test_clean_is_accepted(clean):
    d = decide(clean, TODAY)
    assert d.route == "accepted" and d.flags == [] and d.hard == set()


def test_degraded_with_unreadable_date_goes_to_review_and_is_blanked(clean):
    """tests/images/degraded.jpg: the item is half readable, the date is not."""
    clean.item = f("HW1", "HW1", 0.5)
    clean.due_date = none()
    d = decide(clean, TODAY)
    assert d.route == "review"
    assert ("missing", "due_date") in d.flags and d.hard == {"due_date"}
    shown = for_display(clean, d)
    assert shown["due_date"]["value"] is None and shown["due_date"]["hard"]
    assert shown["item"]["value"] == "HW1" and shown["item"]["flagged"]     # soft: prefilled, highlighted


def test_a_guessed_date_without_evidence_is_hard_even_at_high_confidence(clean):
    clean.due_date = Field(value="2026-10-20", evidence=None, confidence=0.95)
    d = decide(clean, TODAY)
    assert d.route == "review" and d.hard == {"due_date"}
    assert ("low_confidence", "due_date") not in d.flags            # evidence is checked first
    assert for_display(clean, d)["due_date"]["value"] is None       # the guess is never shown


def test_next_tuesday_asks_which_date():
    """tests/images/ambiguous.jpg: 'HW2 due next tuesday'."""
    x = DeadlineExtraction(item=f("HW2"), due_date=f(None, "next tuesday", 0.4), due_time=none(), course=none())
    d = decide(x, TODAY)
    assert d.route == "confirm"
    assert d.flags == [("relative_date", "due_date")]
    assert d.reasons(x) == ["Which date is 'next tuesday'?"]


def test_not_a_deadline_is_rejected():
    """tests/images/not-applicable.jpg: a computer mouse."""
    x = DeadlineExtraction(item=none(), due_date=none(), due_time=none(), course=f("Havit", "Havit", 0.3))
    assert decide(x, TODAY).route == "rejected"


def test_past_date_is_confirm(clean):
    d = decide(clean, date(2026, 11, 1))
    assert d.route == "confirm" and d.flags == [("in_the_past", "due_date")]


def test_unparseable_date_is_flagged_not_raised(clean):
    clean.due_date = f("Oct 20th", "Oct 20th")
    d = decide(clean, TODAY)
    assert d.flags == [("unparseable_date", "due_date")] and d.route == "confirm"


def test_bad_time_is_soft(clean):
    clean.due_time = f("11:59 pm", "11:59 pm")
    assert decide(clean, TODAY).flags == [("bad_time", "due_time")]


def test_low_confidence_alone_is_confirm(clean):
    clean.item = f("HW1", "HW1", 0.4)
    d = decide(clean, TODAY)
    assert d.route == "confirm" and d.flags == [("low_confidence", "item")]


def test_missing_item_is_hard(clean):
    clean.item = none()
    d = decide(clean, TODAY)
    assert d.route == "review" and d.hard == {"item"}


def test_parse_date():
    assert parse_date("2026-10-20") == date(2026, 10, 20)
    assert parse_date("20/10/2026") is None and parse_date(None) is None


def test_decide_is_pure(clean):
    before = clean.model_dump()
    decide(clean, TODAY)
    assert clean.model_dump() == before


def test_evidence_is_checked_before_confidence(clean):
    """No evidence and low confidence at once: unsupported beats unsure, so the field is hard."""
    clean.due_date = Field(value="2026-10-20", evidence=None, confidence=0.2)
    d = decide(clean, TODAY)
    assert ("no_evidence", "due_date") in d.flags
    assert ("low_confidence", "due_date") not in d.flags
    assert d.route == "review" and d.hard == {"due_date"}
