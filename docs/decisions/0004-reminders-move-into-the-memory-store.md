# 0004 · Reminders move into the memory store, with a lifetime and a delete path

**Date:** Week 6 (2026-10-31) · **Decided by:** Nikoloz Tsikaridze

**Context.** Lab 5's `save_reminder` wrote to `state/reminders.json` with a scope (the student's hash) and a write rule (only when asked), but no lifetime and no way to delete. The Week 6 rule is "if it is not in the table, the product does not store it", and the table needs a lifetime and a deletion path for every row. Nikoloz's Week 6 journal names exactly this gap.

**Decision.** Reminders become the second row of `docs/state-contract.md` and live in `state/memory.db` next to the conversation turns: they expire at the end of the day after their due date, and `DELETE /me/memory` deletes them with the turns.

**Alternatives.** (1) Keep `reminders.json` and add a lifetime there: two stores, two expiry paths, and "Forget me" would have to remember both. (2) A new row for a preference (for example, a default `days_before`): it would add a second write path about the student when the one we already have was ungoverned.

**Consequences.** One store and one `forget()` for everything about a student. The old `state/reminders.json` is no longer read; it is local and gitignored, so nothing is migrated (there is no production data yet). The `save_reminder` contract and its results did not change, so the Lab 5 and HW2 golden cases still apply unchanged.
