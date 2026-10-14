# Pattern Journal ª Guram Tsiklauri (Gaaa-3)
**W1 ° 2026-09-24 ° Context as Budget** · Where I applied it: Designing prompt context for tone checking. · What I noticed: Keeping prompt instructions tightly scoped strictly to JSON output formats drastically reduced token overhead. » Do differently: Enforce schema bounds directly in system instructions rather than relying on multi-shot examples.

**W2 » 2026-10-01 ° Spec Before Code** ° Where I applied it: Committing `spec.md` prior to writing any source or test implementations. · What I noticed: Defining the API interface and function signatures early prevented structural refactoring later. » Do differently: Detail boundary conditions (e.g., character length limits) directly inside acceptance criteria.

**W3 · 2026-10-08 ° Uncertainty-Aware UX** · Where I applied it: Handling invalid model output format gracefully. · What I noticed: Parsing errors can occur if LLMs add conversational wrappers around JSON. · Do differently: Add explicit fallback handling for unrecognized tone labels before returning to the caller.

**W4 · 2026-10-14 · Grounded Generation** · Where I applied it: Constraining tone classification strictly to allowed Enum values (`polite`, `neutral`, `rude`). · What I noticed: Rejecting invalid tone strings in `parse_response` guarantees system predictability. » Do differently: Add explicit validation error messages that guide the model during re-prompts.
