# Confidence policy · Deadline from a photo

*`src/deadline_checks.py` implements exactly this table; `tests/test_deadline_checks.py` proves it.*

## 1 · Routes

| Route | What it means | What the student sees | What gets created |
|---|---|---|---|
| `accepted` | `item` and `due_date` present, evidenced, consistent | "HW1 is due Tuesday 20 October 2026, 23:59 (from your photo)" | a deadline |
| `confirm` | soft flags only | the deadline with the flagged value highlighted and one question | a draft until the student confirms |
| `review` | at least one hard flag | the flagged fields **empty**, the photo beside them: "Type what the photo says" | a draft, nothing saved |
| `rejected` | not a deadline at all | "This doesn't look like a deadline. Photograph the announcement itself?" | nothing |

## 2 · Signals, per required field (`item`, `due_date`)

| Signal | Condition | Flag | Hard or soft |
|---|---|---|---|
| value present | `value is None and evidence is None` | `missing` | hard |
| evidence present | `value is not None and evidence is None` | `no_evidence` | hard |
| relative date | `due_date.value is None and due_date.evidence is not None` ("next Tuesday") | `relative_date` | soft |
| self-rated confidence | `confidence < 0.6` | `low_confidence` | soft |
| date format | `due_date.value` is not `YYYY-MM-DD` | `unparseable_date` | soft |
| consistent with the world | `due_date < today` | `in_the_past` | soft |
| time format (optional field) | `due_time.value` is not `HH:MM` | `bad_time` | soft |
| deadline-like at all | `item`, `due_date` and `due_time` all without value and evidence | (no flag) | `rejected` |

Order: missing, then evidence, then confidence. Evidence is checked before the model's own number: a date with confidence 0.95 and nothing on the photo to quote is a guess.

"Soft" fields that join a `review` (because another field is hard) stay prefilled but highlighted; hard fields are always blank.

## 3 · From flags to a route

```
nothing deadline-like on the image              → rejected
any missing or no_evidence                      → review   hard = every field with missing or no_evidence
any other flag                                  → confirm
no flags                                        → accepted
```

## 4 · The reason text

| Flag | On screen |
|---|---|
| `missing` | "Due date: not found on the photo" |
| `no_evidence` | "Due date: we could not find the text this came from" |
| `relative_date` | "Which date is 'next tuesday'?" |
| `low_confidence` | "We think this is 2026-10-20. Check the photo?" |
| `unparseable_date` | "We could not read 'Oct 20th' as a date. Type it in?" |
| `in_the_past` | "This date has already passed. Is the year right?" |
| `bad_time` | "We could not read the time. Type it in?" |

## 5 · Tests (in `tests/test_deadline_checks.py`, no API calls)

1. Clean extraction → `accepted`, no flags.
2. Degraded photo, nothing readable for the date → `review`, `due_date` hard and returned empty.
3. Degraded photo where the model guessed a date with no evidence → `review`, even at confidence 0.95.
4. "next tuesday" → `confirm`, `relative_date`.
5. A mouse → `rejected`.
6. Past date → `confirm`, `in_the_past`.

## 6 · What we measure once it runs

- Route per test image, live, against `evals/images_expected.json` (`python -m evals.run_images`).
- Wrong accepts (the expensive mistake) and wrong reviews (the annoying one). Revisit the 0.6 threshold after twenty real photos and record the change in a decision record.
