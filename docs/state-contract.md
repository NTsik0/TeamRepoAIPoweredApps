# KIU CourseMate · State Contract

One row per thing CourseMate remembers across turns. If it is not in this table, CourseMate does not store it. `src/memory.py` is the code version of this table; the two must agree, and `tests/test_state.py` proves the scope, lifetime and deletion columns.

| What we remember | Why the product needs it | Scope: who can read it | Lifetime | Written when | Deleted by | Where it lives |
|---|---|---|---|---|---|---|
| Conversation turns: the last 6 (3 questions, 3 answers), at most 2,000 characters each | so a follow-up like "and when is the next one?" makes sense | this session only (`X-Session-Id`; a new tab is a new session) | 24 hours after each turn | every `/chat` turn, automatically; nothing without a session | expiry; `DELETE /me/memory` (the "Forget me" button) | `state/memory.db` · key `session:<id>` |
| Deadline reminders (course, title, due date, remind-on date), at most 50 | the student asked CourseMate to remind them | this signed-in student only (`X-Student-Id`, stored as a 12-character hash) | until the end of the day after the due date, Tbilisi time (at most 181 days, because a due date may be at most 180 days ahead) | only when the student asks, through the `save_reminder` tool (Lab 5 contract, identity from the session) | expiry; `DELETE /me/memory` (the "Forget me" button) | `state/memory.db` · key `student:<hash>` |

## What we never store

- The student id itself: every key and log line carries a 12-character hash.
- Anything the model inferred about the student that they did not state. The only write about a person is `save_reminder`, which the student has to ask for.
- Other students' rows in anyone's prompt: `build_messages()` reads only the caller's reminders and only this session's turns.
- The question text in `logs/usage.jsonl` (numbers only) or audio of any kind (there is no voice path).

## How a student sees and controls it

- `GET /me/memory`: the reminders we hold, how many turns of this session, and both lifetimes.
- After a reminder is saved, the stream's `tool` event carries what was stored and `"delete_with": "DELETE /me/memory"`; the page shows "Saved … Delete any time: Forget me."
- `DELETE /me/memory` (the "Forget me" button): deletes this student's reminders and this session's turns, now, and returns the counts, e.g. `{"reminders": 1, "turns": 2}`. Rows are deleted, not flagged. No model is involved.
- Expired rows are invisible to every read and are deleted by `memory.expire()` at app startup.

## What changes the contract

Any new row needs a decision record in `docs/decisions/` and tests for its scope, lifetime and deletion. Backups: there are none yet; when there are, the same deletion must reach them, or this promise is false.
