# RANK #1 CORRECTION RECOMMENDATION

**Date**: 2026-06-02T20:36 UTC
**Mode**: READ-ONLY · recommendation only · no code applied
**Scope**: One scoped UI-contract adjustment surfaced by the design-intent audit

---

## Final verdict

# 🟡 **B · Rank #1 changes need targeted adjustment**

* Not (A) — one form has a UI-contract drift worth fixing.
* Not (C) — no rollback warranted; 5 of 6 forms are clean, the 6th has no data-integrity issue, and the audit-finding is cosmetic / disabled-state alignment only.

---

## Recommended adjustment (single, scoped)

### File: `frontend/src/pages/NewDailyReport.jsx`

### Surface: the Rank #1 sticky footer Submit button (L2246)

### Change: align the sticky footer's `disabled` expression with the bottom-end button's stricter policy so the visible-but-disabled affordance matches the hint copy.

**Currently** (Rank #1 as-shipped, mirroring the pre-existing top button):

```jsx
<Button
  onClick={submit}
  disabled={saving}
  …
  data-testid="submit-sticky-btn"
>
```

**Recommended** (mirror the pre-existing bottom-end button's policy, L2203):

```jsx
<Button
  onClick={submit}
  disabled={saving || photosCount < photoMin}
  …
  data-testid="submit-sticky-btn"
>
```

### LOC: 1 (one expression on one line)

### Risk: minimal — the photo-count gap was already enforced by `validate()` on the same handler; this change only aligns the **button's clickable state** with the hint string the same surface already displays.

### Downstream UX effect: when the user has fewer than `photo_min` photos (default 6), the sticky-footer button visibly disables. The hint string `NEED N MORE PHOTO(S)` then matches a disabled affordance instead of a clickable one. Once the photo gate clears, the button becomes interactive and the hint flips to `Ready to submit · PM distribution will send`. All other gates (project name, signature, safety-escalation chain) remain handler-enforced on click — that policy is consistent across the entire daily-report page and is not in scope for this adjustment.

### Optional secondary thought (NOT required)

Pre-existing top button on NewDailyReport (L941) is also `disabled={saving}` only. The same alignment argument could be applied to the top button — but doing so is **out of scope** for this corrective. The audit was bounded to Rank #1's introductions; the top button predates Rank #1 and was not in the OMEGA Rank #1 change set.

---

## What does NOT need correction

| Form | Status | Reason |
|---|:-:|---|
| NewIncident | 🟢 | Sticky footer disabled-state already mirrors top + bottom buttons; hint copy matches; completion-summary banner preserved |
| NewInspection | 🟢 | Sticky footer disabled-state already mirrors top + bottom buttons; hint copy matches; live GradeBanner preserved |
| NewQaqcInspection | 🟢 | Pre-existing; unchanged by Rank #1; coherent single Submit |
| NewSafetyEquipmentIssuance | 🟢 | Pre-existing; unchanged by Rank #1; coherent single Submit |
| NewSafetyEquipmentTraining | 🟢 | Pre-existing; unchanged by Rank #1; coherent single Submit; no photo gate by design |

---

## Out-of-scope (do not perform under this directive)

* **Do not** unify the top-button's disabled state on NewDailyReport (predates Rank #1).
* **Do not** add a sticky footer to any additional page.
* **Do not** remove the pre-existing top-sticky-header Submits on the three Group-A pages — they predate Rank #1 and are not the audit's concern.
* **Do not** redesign the NewDailyReport safety-escalation block, completion summary, or photo-count UI — they are functioning per pre-Rank #1 intent.
* **Do not** revert the Rank #1 sticky footers on NewIncident or NewInspection — both are 🟢.

---

## Authorization required

Per OMEGA discipline, this corrective is **not** auto-applied. It is a recommendation only. The operator may:

* **Approve** — issue a one-line OMEGA directive: *"Apply the FORM_SUBMIT_GATING_MATRIX NewDailyReport corrective. Single line. Preview only. STOP."*
* **Defer** — leave as-is; the data-integrity contract is intact and the only consequence is a mild affordance contradiction on one page.
* **Reject** — leave as-is; document that this drift was reviewed and accepted.

---

## Stop conditions honored in this audit cycle

* ✅ No code changes
* ✅ No fixes
* ✅ No deployment
* ✅ No additional UX changes
* ✅ No Rank #2 / #3 work
* ✅ No drift to OC-005, Accountability Chain, White Label, ForgedOps
* ✅ All four deliverables written: `ITER500_RANK1_DESIGN_INTENT_AUDIT.md`, `FORM_SUBMIT_GATING_MATRIX.md`, `RANK1_CHANGE_IMPACT_ASSESSMENT.md`, `RANK1_CORRECTION_RECOMMENDATION.md` (this file)

STOP.
