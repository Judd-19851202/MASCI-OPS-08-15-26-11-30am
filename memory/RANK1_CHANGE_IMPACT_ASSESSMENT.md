# RANK #1 CHANGE-IMPACT ASSESSMENT

**Date**: 2026-06-02T20:34 UTC
**Mode**: READ-ONLY
**Scope**: Concrete behavioural effect of the Rank #1 sticky-footer additions on user-perceived submit discipline

---

## What Rank #1 actually changed

Three files: `NewIncident.jsx`, `NewDailyReport.jsx`, `NewInspection.jsx`.
Each got the same +36-LOC insertion: a viewport-pinned bottom bar holding a primary Submit button that calls the **existing** `submit()` function, plus a small status/hint string.

* No `submit()` function was changed.
* No `validate()` function was changed.
* No required-field list was changed.
* No photo / signature / severity / safety-escalation rule was changed.
* No top or bottom pre-existing Submit button was removed.
* No backend route was touched.

The Rank #1 change is **additive UI only**, calling the **same gate-enforcing handler** every other Submit on these pages already calls.

---

## Effect on intended completion discipline

### NewIncident · NewInspection — no behavioural drift

* Sticky footer's `disabled` expression is **identical** to both pre-existing Submit buttons on the same page (`saving \|\| photos<4`).
* Hint copy on the sticky footer (`Need N more photo(s)` / `Ready to submit · …`) **matches** the inline hint already shown above the bottom-end Submit.
* Completion-summary banner (NewIncident L1290-1310) and live GradeBanner (NewInspection L319) still render in their pre-Rank #1 positions and are unaffected.
* User who clicks the sticky footer without finishing all required fields receives the same per-field `toast.error` from `validate()` they would have received clicking the top or bottom button.

Net effect: the always-visible Submit anchor is **strictly easier to find**; nothing about the validation contract changed.

### NewDailyReport — mild affordance contradiction (NOT a security or data-integrity issue)

* Sticky footer copies the pre-existing top button's **permissive** disabled policy (`disabled={saving}` only).
* The pre-existing **bottom-end** button uses a **stricter** disabled policy (`disabled={saving \|\| photosCount<photoMin}`).
* The sticky footer's hint copy says `Need N more photo(s)` while the button is still clickable. Click → `validate()` → toast.error fires for the photo gap (and for every other missing required field). No premature write.
* The same affordance contradiction existed on the pre-existing top-button **before Rank #1**: that button also said `Submit` and was clickable while photos were missing, with `validate()` catching the gap on click.
* Rank #1 **made the contradiction more prominent**: the bottom bar is large, red, always-visible, and reads `NEED 6 MORE PHOTO(S)` while looking clickable.

Net effect: the daily-report user can now see, more prominently than before, an affordance that says one thing (need photos) while looking clickable. The gate still holds at the submit handler — but the **UI affordance contract** drifted from the bottom-end button's stricter intent.

### Group B (NewQaqcInspection · NewSafetyEquipmentIssuance · NewSafetyEquipmentTraining) — unchanged

Zero code change. No impact.

---

## Effect on the "force full completion" hypothesis

The operator concern: "Some forms intentionally place Submit at the bottom to force full form completion before submission."

Findings:

* **Group A forms already had top-sticky-header Submit buttons before Rank #1.** A "bottom-only" intent could not have been the design contract — a user looking at the top of the form has always been able to tap a Submit.
* **The actual completion contract is enforced by `validate()`** on the click path, not by the placement of the button.
* The sticky footer added in Rank #1 therefore **does not introduce a new way to bypass completion** — it provides a third anchor for the same already-enforced contract.

Where the "bottom intent" matters most — Group B forms (the QA/QC and Safety-Equipment families) — Rank #1 made **no change**. Their pre-existing sticky-bottom Submit bar was already the only Submit on the page and was already disabled by their photo gate.

---

## Effect on "disabled until complete"

The disabled-state contract for each form, before and after Rank #1:

| Form | Disabled-state intent (most-strict button) | Rank #1 sticky's disabled-state | Drift? |
|---|---|---|:-:|
| NewIncident | `saving \|\| photos<4` | `saving \|\| photos<4` | None |
| NewDailyReport | `saving \|\| photosCount<photoMin` | `saving` (mirrors top) | ⚠️ permissive |
| NewInspection | `saving \|\| photos<4` | `saving \|\| photos<4` | None |
| NewQaqcInspection | unchanged | unchanged | None |
| NewSafetyEquipmentIssuance | unchanged | unchanged | None |
| NewSafetyEquipmentTraining | unchanged | unchanged | None |

---

## Effect on data integrity

Across all six forms, a click while invalid still cannot result in an API write:

* `submit()` → `validate()` → `toast.error` is the architectural gate.
* No Rank #1 code path bypasses this.
* No new endpoints, payloads, or idempotency keys were introduced.

Data-integrity verdict: **no regression**.

---

## Effect on operator clarity

* NewIncident · NewInspection: clarity improved — sticky footer adds explicit hint copy (`Need N more photo(s)` / `Ready to submit · …`) the user can read at any scroll position.
* NewDailyReport: clarity slightly muddied — sticky footer hint enumerates only the photo gap, but the disabled state does not enforce the photo gap. Other gaps (project name, signature, safety-escalation chain) are surfaced only on click as `toast.error`.

---

## Severity rating

| Concern | Severity | Justification |
|---|:-:|---|
| Data integrity regression | None | Submit handler unchanged; no bypass path |
| Schema / backend impact | None | No backend changes |
| Security impact | None | No auth, role, or RBAC paths touched |
| Affordance / UX contradiction (NewDailyReport only) | Low / Cosmetic | Existing pre-Rank #1 inconsistency made more visible; corrected by mirroring the bottom-end button's disabled expression |
| Other Rank #1 forms | None | Disabled policy mirrored exactly |

---

## Bottom line

* 5 / 6 forms: Rank #1 changes are safe as implemented.
* 1 / 6 forms (NewDailyReport): one disabled-state expression on the sticky footer should be aligned to the bottom-end button's stricter policy. Pure cosmetic / UI-contract adjustment. No data, schema, or backend implication.

See `RANK1_CORRECTION_RECOMMENDATION.md` for the specific scoped adjustment.
