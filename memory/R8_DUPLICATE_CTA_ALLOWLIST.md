# R8 Duplicate CTA — Allow-list

**Track 18.11.** Every entry in this allow-list documents a pattern that *looks* like a duplicate CTA to a naive scanner but is **intentionally** correct.

## Allow-list entries

| # | File | Component / Pattern | Reason | Allowed action types | Why it is not CTA confusion | Future review |
|---|---|---|---|---|---|---|
| 1 | `frontend/src/pages/FieldLeadershipFormPage.jsx` | Form Card containing a conditional inline "Add new employee" sub-panel | The form Card hosts a `{!showInlineNewEmp ? toggle-link : <inline panel with Add / Cancel>}` block. When the inline panel is open, the operator is choosing **inside that sub-panel** (Add / Cancel) — not between the inline Add and the main form Submit. The two visible primary buttons (inline `Add` at L841 + main `Submit & Email PDF` at L1054) are contextually independent: the inline panel takes focus while it is open, and the form Submit returns once the inline action resolves. | PAIRED_DECISION (Add / Cancel inside the sub-panel) + WIZARD_STEP (main form Submit) | Inline sub-panel CTAs are conditionally rendered; they do not visually compete with the form CTA at runtime. The Cancel button on L842 is already `variant="outline"`, satisfying the paired-decision pattern within the sub-panel. | 2026-Q2 — re-evaluate if the inline panel pattern is moved into a Dialog or Sheet (would naturally remove the false positive). |

## How to add an entry

If a future R8 lint failure flags an intentionally-paired workflow, add a row here with:
1. The **file** path (e.g., `frontend/src/components/disposition/DispositionCard.jsx`).
2. The **component / pattern** (e.g., "DispositionCard footer").
3. The **reason** (e.g., "Approve / Needs Correction is the documented operator decision pair for this workflow").
4. The **allowed action types** (`PAIRED_DECISION`, `WIZARD_STEP`, etc.).
5. **Why it is not CTA confusion** — one-sentence justification.
6. A **future review** note (date + owner who approved the exception).

No mystery exceptions. Every entry must justify itself in plain English.

## Forbidden allow-list rationales
* "Looks fine to me" — rejected.
* "Always been like that" — rejected.
* "It's a card grid" — rejected (each card is its own Card; R8 already exempts multi-card grids by construction).
* "Two `aria-label`s are different" — irrelevant; R8 ignores `aria-label`. Only the visible button text + variant matter.

## Six-Pillar self-check
Powerful ✅ · Simple ✅ · Beautiful ✅ · Trusted ✅ · Proven ✅ · Operational ✅
