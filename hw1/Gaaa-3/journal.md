# Pattern Journal · Guram Tsiklauri (Gaaa-3)

**W1 · Context as Budget** · Where I applied it: Designing prompt context. · What I noticed: Keeping prompt instructions tightly scoped strictly to JSON output formats drastically reduced token overhead. · Do differently: Enforce schema bounds directly in system instructions.

**W2 · Spec Before Code** · Where I applied it: Committing spec.md prior to writing code. · What I noticed: Defining the API interface early prevented structural refactoring. · Do differently: Detail boundary conditions directly inside acceptance criteria.

**W3 · Uncertainty-Aware UX** · Where I applied it: Handling invalid model output format gracefully. · What I noticed: Parsing errors can occur if LLMs add wrappers around JSON. · Do differently: Add explicit fallback handling for unrecognized tone labels.

**W4 · Grounded Generation** · Where I applied it: Constraining tone classification strictly to allowed Enum values. · What I noticed: Rejecting invalid strings guarantees system predictability. · Do differently: Add explicit validation error messages that guide the model during re-prompts.
