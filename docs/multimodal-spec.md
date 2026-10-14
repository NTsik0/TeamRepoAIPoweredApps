# Multimodal spec · Deadline from a photo

*Lab 3 · KIU CourseMate. A student photographs or screenshots a deadline and CourseMate turns it into a structured deadline, or asks when it is not sure.*

## 1 · The input

- **What the user has in their hand:** a deadline they saw somewhere other than the course pages: a screenshot of a Teams post or a course page, a photo of a slide or a screen, a handwritten note.
- **How it reaches us:** image upload (`POST /deadline/photo`), JPEG or PNG.
- **Typical quality:** screenshots are sharp; phone photos of a screen are often tilted, blurred or glared; handwritten notes are often vague ("next Tuesday").
- **What we will never accept:** faces, ID documents, screenshots that show other people's names or messages. Test images contain none (`tests/images/`), and photos are re-saved without EXIF data (no location).

## 2 · The fields

| Field | Type after normalisation | Required | Normalisation rule | Example value | Example evidence (exact text on the image) |
|---|---|---|---|---|---|
| `item` | string | yes | what is due, as written | `Milestone 1 = HW1 "Spec to Ship"` | `Milestone 1 = HW1 · "Spec to Ship"` |
| `due_date` | ISO date `YYYY-MM-DD` | yes | only an explicit calendar date; a relative date ("next Tuesday") gives value `null` and the relative words as evidence | `2026-10-20` | `Tuesday 20 October 2026` |
| `due_time` | `HH:MM`, 24-hour | no | as written; `null` if absent | `23:59` | `23:59 (Tbilisi time)` |
| `course` | string | no | course code if shown | `CS6920` | `CS6920` |

Every field returns `value`, `evidence`, `confidence`. `value` and `evidence` are `null` when the model cannot read the field. A guess is never a value.

## 3 · The schema

```python
class Field(BaseModel):
    value: str | None
    evidence: str | None
    confidence: float = PField(ge=0.0, le=1.0)

class DeadlineExtraction(BaseModel):
    item: Field
    due_date: Field
    due_time: Field
    course: Field
```

Sent as a strict JSON schema with the request (`src/deadline_extract.py`) and validated with pydantic on the way back.

## 4 · Acceptance criteria

1. Given `tests/images/clean.jpg`, `item` and `due_date` have non-null values with non-null evidence, `due_date` is `2026-10-20`, and the route is `accepted`.
2. Given `tests/images/degraded.jpg`, nothing unreadable is accepted: any required field without evidence goes to `review`, and in `review` that field is returned empty, never prefilled.
3. Given `tests/images/ambiguous.jpg` ("HW2 due next tuesday"), `due_date` has no value but has evidence, and the route is `confirm` with the question "Which date is 'next tuesday'?".
4. Given `tests/images/not-applicable.jpg`, the route is `rejected` and nothing is created.
5. The image is downscaled to at most 1024 px on its longest side before sending; one call costs under $0.005 and logs tokens, cost and latency in `logs/usage.jsonl`.

## 5 · Test images (in `tests/images/`)

| File | What it is | What we expect |
|---|---|---|
| `clean.jpg` | screenshot of the Lab 4 homework section: HW1 and the Design Review, both "Tuesday 20 October 2026, 23:59" | accepted |
| `degraded.jpg` | phone photo of the same screen, dark, blurred, tilted | review (predicted `due_date` hard; live, the model read the date but not the item, so `item` is hard) |
| `ambiguous.jpg` | handwritten, photographed sideways: "HW2 due next tuesday" | confirm, `due_date` flagged `relative_date` |
| `not-applicable.jpg` | a computer mouse | rejected |

Expected routes are in `evals/images_expected.json`; `python -m evals.run_images` runs all four live.

## 6 · Model and budget

- Model: `google/gemini-3.8-flash` via OpenRouter, the same model as grounded answers; it accepts image input and a JSON schema in `response_format`. Verified live on 2026-10-14: all four photos routed as expected (`evals/results/2026-10-14-2009-images.json`).
- Approximate cost per image at 1024 px: about 1,300 tokens in, 200 out ≈ $0.0017 (to be replaced by the logged number).
- Expected volume: 50 photos a day → about $2.60 a month.

## 7 · Out of scope for this slice

- More than one deadline per image: the most prominent one is read (the clean screenshot has two with the same date).
- Saving deadlines anywhere: this slice returns the decision; a calendar comes with the Week 5 tools.
- Georgian text.

## 8 · Stretch

- Run twice and flag fields whose value differs (`disagreements()`).
