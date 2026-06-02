# ITER500 RANK #1 · DESIGN-INTENT AUDIT

**Date**: 2026-06-02T20:30 UTC
**Mode**: READ-ONLY · no code · no fixes · no deploy
**Authority**: OMEGA DIRECTIVE — Verify form-submit design intent before any further UX changes
**Scope**: The six "New X" forms touched (or verified) under ITER500 Rank #1

---

## Audit method

For each form, I read the actual source: (a) every `disabled={…}` expression on every Submit button (top-sticky-header, end-of-form, and any pre-existing or newly-added sticky bar), (b) the complete `validate()` / submit-handler gate list, (c) the post-submit toast + navigation, and (d) the surrounding completion-summary UI (e.g., serious-incident attention banner, safety-escalation stop-the-line, photo-count hint).

I then evaluated whether the Rank #1 sticky footer **bypassed, weakened, duplicated, or accurately mirrored** the pre-existing gate.

---

## 1 · NewIncident.jsx

| # | Question | Answer |
|---|---|---|
| 1 | Is Submit intentionally bottom-only? | **No.** A `submit-top-btn` already lived in the sticky page header (L391) **before** Rank #1, with the same `disabled={saving \|\| photos<4}` gate as the bottom button. The "bottom-only-to-force-completion" hypothesis was already not architecturally enforced. |
| 2 | Inaccessible until end? | **No.** Top-sticky-header Submit was already always-visible. |
| 3 | Visible-but-disabled-until-complete? | **Yes, partially.** Both pre-existing buttons disable when `photos<4`. Other required fields (severity, signature, serious-incident sections) are gated only inside `validate()` → toast.error. |
| 4 | What gates submission? | `validate()` L226-275: `project_name`, `location`, `incident_date`, `incident_time`, `reported_by`, `incident_type`, `severity`, `description`, `reporter_signature`, ≥4 photos. Serious-severity branch additionally requires `root_causes`, `corrective_actions`, `notifications` (L268-275). |
| 5 | Does sticky footer bypass / weaken the gate? | **No.** Sticky footer's `onClick={submit}` routes through the **same** validate()→toast.error pipeline as the top + bottom buttons. The data write only happens after every field-level toast.error has been cleared. |
| 6 | Correct disabled state? | **Yes.** Sticky footer L1355: `disabled={saving \|\| (data.photos \|\| []).length < 4}` — identical to L391 (top) and L1318 (bottom). |
| 7 | Clear "what is missing"? | **Yes.** Sticky footer hint copy: `Need N more photo(s)` while photos<4, otherwise `Ready to submit · Safety + PM will be notified`. Matches the inline photo-count hint at L1311-1314. |
| 8 | Allow premature submission? | **No.** Click while invalid → `validate()` returns false → toast.error → no POST. |
| 9 | Confusing duplication? | **Low.** Three Submit buttons now exist (top sticky-header, sticky-footer, bottom-end). All three carry identical disabled state and call the same `submit()`. Acceptable redundancy; not contradictory. |
| 10 | Preserve completion discipline? | **Yes.** Completion-summary banner at L1290-1310 (operational status pill, "Attention" vs "Status" tone) is **still rendered** above the bottom-end Submit. Users hitting the sticky footer get the same validate()-driven toasts. Discipline is preserved at the handler boundary, not the button. |

**Classification**: 🟢 **SAFE** — sticky submit preserves intended behaviour.

---

## 2 · NewDailyReport.jsx

| # | Question | Answer |
|---|---|---|
| 1 | Is Submit intentionally bottom-only? | **No.** A `submit-top-btn` existed in the sticky page header (L941) before Rank #1. |
| 2 | Inaccessible until end? | **No.** Top-sticky-header Submit was always-visible. |
| 3 | Visible-but-disabled-until-complete? | **Inconsistent (PRE-EXISTING).** Pre-Rank #1, the top button was `disabled={saving}` only; the bottom-end button was `disabled={saving \|\| photosCount<photoMin}`. The same form already shipped with **two different gating policies** on Submit. |
| 4 | What gates submission? | `validate()` L635-725: `project_name`, `location`, `prepared_by`, Delays-Yes ⇒ ≥1 constraint row, Weather-Yes ⇒ ≥1 weather-type constraint row, safety-escalation chain (`safety_notified=Yes`, `safety_contact_person`, `safety_contact_time`, `incident_report_filled=Yes`, `incident_report_time`), photos ≥ `photo_min` (default 6), `prepared_by_signature`. |
| 5 | Does sticky footer bypass / weaken the gate? | **No premature write** — `submit()`→`validate()` will still reject. **But** the sticky footer mirrors the **permissive** top-button policy (`disabled={saving}`) rather than the **restrictive** bottom-end policy (`disabled={saving \|\| photosCount<photoMin}`). It is therefore a more prominent realization of the permissive policy than existed pre-Rank #1. |
| 6 | Correct disabled state? | **No — mismatch.** Sticky footer L2246: `disabled={saving}`. Bottom-end L2203: `disabled={saving \|\| photosCount<photoMin}`. Sticky footer hint copy says `Need N more photo(s)` while the button itself stays clickable. A click in that state routes through `validate()` → toast.error, but the button-state contradicts the hint copy. |
| 7 | Clear "what is missing"? | Partially. The hint enumerates only photo gaps; the larger required-fields list (project name, signature, safety chain) is surfaced as toast.error on click, not in the footer copy. |
| 8 | Allow premature submission? | **No data write.** `validate()` blocks every missing required field with toast.error. No POST is issued. |
| 9 | Confusing duplication? | **Medium.** Three Submit buttons, **two different disabled policies**. The sticky footer (most prominent) sides with the more permissive top button. A foreman who reads `NEED 6 MORE PHOTO(S)` and sees the SUBMIT button looking clickable may be momentarily confused before clicking → toast.error → realizing photos are still required. |
| 10 | Preserve completion discipline? | **Mostly.** Stop-the-line safety-escalation block (red banner, Section 03, L1301-1442) still renders and is unaffected by the sticky footer. Validation handler still rejects. Discipline preserved at the submit-handler boundary, **but the sticky footer's disabled-state copy/contract is inconsistent with the bottom-end button's intent**. |

**Classification**: 🟡 **NEEDS ADJUSTMENT** — sticky submit is useful but disabled-state should mirror the **bottom-end button's stricter policy** (`disabled={saving \|\| photosCount<photoMin}`) so the visible-but-disabled affordance lines up with the hint copy.

---

## 3 · NewInspection.jsx

| # | Question | Answer |
|---|---|---|
| 1 | Is Submit intentionally bottom-only? | **No.** Top-sticky-header Submit existed pre-Rank #1 (L293). |
| 2 | Inaccessible until end? | **No.** Top-sticky-header Submit was always-visible. |
| 3 | Visible-but-disabled-until-complete? | **Yes.** Both pre-existing buttons disable when `photos<4`. Other required fields gated in `validate()` → toast.error. |
| 4 | What gates submission? | `validate()` L160-180: required-field labels, `inspector_signature`, `foreman_signature`, ≥4 photos. |
| 5 | Does sticky footer bypass / weaken the gate? | **No.** `onClick={submit}` routes through identical pipeline. |
| 6 | Correct disabled state? | **Yes.** Sticky footer L813: `disabled={saving \|\| photos<4}` — identical to L293 (top) and L766 (bottom). |
| 7 | Clear "what is missing"? | **Yes.** Hint: `Need N more photo(s)` while photos<4, `Ready to submit · graded on file` otherwise. |
| 8 | Allow premature submission? | **No.** `validate()` enforces. |
| 9 | Confusing duplication? | **Low.** Three Submit buttons, all carrying identical disabled state. |
| 10 | Preserve completion discipline? | **Yes.** Live `GradeBanner` at L319 still renders and updates in real time; foreman still sees the live grade summary. Validation pipeline unchanged. |

**Classification**: 🟢 **SAFE**.

---

## 4 · NewQaqcInspection.jsx (no Rank #1 change)

| # | Question | Answer |
|---|---|---|
| 1 | Bottom-only? | **Partially.** The single Submit is at the bottom of `<form>` inside a `sticky bottom-0` bar. There is no top-header Submit. The bar pins to viewport-bottom as the form scrolls. |
| 2 | Inaccessible until end? | **Effectively no.** `sticky bottom-0` keeps the Submit visible from very early in the scroll. |
| 3 | Visible-but-disabled-until-complete? | **Yes.** L563: `disabled={saving \|\| data.photos.length < 4}`. |
| 4 | What gates submission? | `validate()` runs checklist-completion, every-fail-has-note, ≥4 photos, signatures, concrete-form additional fields (Mix Design + Yards Ordered + Vendor) — L185 `toast.error(fails[0])`. |
| 5 | Sticky footer bypass? | **N/A — pre-existing, not changed.** |
| 6 | Correct disabled state? | **Yes.** Photos gate visible on button + hint copy. |
| 7 | Clear "what is missing"? | **Yes.** Pre-existing `qaqc-submit-photos-hint` line + button label cycles `Need 4 photos to submit` / `Submit Inspection`. |
| 8 | Premature submission? | **No.** Single validation pipeline. |
| 9 | Confusing duplication? | **No.** One Submit. |
| 10 | Preserve discipline? | **Yes.** Untouched. |

**Classification**: 🟢 **SAFE** (pre-compliant; not modified).

---

## 5 · NewSafetyEquipmentIssuance.jsx (no Rank #1 change)

| # | Question | Answer |
|---|---|---|
| 1 | Bottom-only? | **Partially.** Single Submit at the bottom inside a `sticky bottom-0` bar; no top-header Submit. |
| 2 | Inaccessible until end? | **Effectively no.** Sticky bar visible throughout scroll. |
| 3 | Visible-but-disabled-until-complete? | **Yes.** L608: `disabled={saving \|\| data.photos.length < 1}`. |
| 4 | What gates submission? | `validate()` runs required-field list + ≥1 photo + signatures; failure surfaces via `toast.error(fails[0])` at L175. |
| 5 | Sticky footer bypass? | **N/A.** |
| 6 | Correct disabled state? | **Yes.** Mirrors photo gate. |
| 7 | Clear "what is missing"? | **Yes.** `iss-submit-photos-hint` + button label cycles `Photo required` / `Submit & Email PDF`. |
| 8 | Premature submission? | **No.** |
| 9 | Confusing duplication? | **No.** Single Submit. |
| 10 | Preserve discipline? | **Yes.** Untouched. |

**Classification**: 🟢 **SAFE** (pre-compliant; not modified).

---

## 6 · NewSafetyEquipmentTraining.jsx (no Rank #1 change)

| # | Question | Answer |
|---|---|---|
| 1 | Bottom-only? | **Partially.** Single Submit at the bottom inside `sticky bottom-0` bar; no top-header Submit. |
| 2 | Inaccessible until end? | **Effectively no.** Sticky bar visible throughout scroll. |
| 3 | Visible-but-disabled-until-complete? | **Permissive.** L460: `disabled={saving}` only. No photo requirement on this form. |
| 4 | What gates submission? | `validate()` runs required-field list + instructor signature; failure surfaces via `toast.error(fails[0])` at L116. |
| 5 | Sticky footer bypass? | **N/A.** |
| 6 | Correct disabled state? | **Yes** — no photo gate exists on this form, so `disabled={saving}` is correct. |
| 7 | Clear "what is missing"? | **Yes** — via toast.error on click. |
| 8 | Premature submission? | **No.** |
| 9 | Confusing duplication? | **No.** Single Submit. |
| 10 | Preserve discipline? | **Yes.** Untouched. |

**Classification**: 🟢 **SAFE** (pre-compliant; not modified).

---

## Cross-form principle observed

Across all six forms the **submit handler** — not the **button's disabled prop** — is the canonical gate. `validate()` → `toast.error` is the universal stop. Photo counts are the **only** field a button-disabled state is ever wired against; every other required field (signatures, severity branch sections, safety-escalation chain, checklist completeness, concrete-form extras) is gated only on click.

That architectural choice predates Rank #1. The Rank #1 sticky footer inherits it; it does not change it.

---

## Composite verdict

| Form | Classification |
|---|---|
| NewIncident | 🟢 SAFE |
| NewDailyReport | 🟡 NEEDS ADJUSTMENT |
| NewInspection | 🟢 SAFE |
| NewQaqcInspection | 🟢 SAFE (pre-compliant) |
| NewSafetyEquipmentIssuance | 🟢 SAFE (pre-compliant) |
| NewSafetyEquipmentTraining | 🟢 SAFE (pre-compliant) |

5 / 6 forms 🟢 · 1 / 6 forms 🟡 · 0 / 6 forms 🔴.

See `FORM_SUBMIT_GATING_MATRIX.md`, `RANK1_CHANGE_IMPACT_ASSESSMENT.md`, `RANK1_CORRECTION_RECOMMENDATION.md`.
