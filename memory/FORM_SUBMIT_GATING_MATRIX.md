# FORM SUBMIT GATING MATRIX

**Date**: 2026-06-02T20:32 UTC
**Mode**: READ-ONLY
**Scope**: All Submit affordances on the 6 ITER500 Rank #1 forms, before and after the Rank #1 sticky-footer roll-out

---

## Legend

* **Surface** — which Submit button it is (top sticky header / sticky footer / bottom end-of-form / single form-level sticky)
* **Pre-existing?** — was the surface there before Rank #1?
* **Disabled-when** — the literal `disabled={…}` expression in source
* **Hint copy** — what the user reads next to / on the button explaining the gate
* **Validation gate on click** — the fields the submit handler enforces via `validate()` → `toast.error` (button-disabled does NOT cover these)
* **Premature-submission risk** — can a click while invalid actually write to the API?

---

## 1 · NewIncident.jsx

| Surface | Pre-existing? | Disabled-when | Hint copy | Validation gate on click | Premature submit? |
|---|:-:|---|---|---|:-:|
| Top sticky header `submit-top-btn` (L391) | ✅ | `saving \|\| photos<4` | none (just `Submit` label) | project name · location · date · time · reporter · type · severity · description · signature · 4 photos · serious-severity branch (root causes · corrective · notifications) | No (`validate()`) |
| Sticky footer `submit-sticky-btn` (L1355) **+Rank #1** | ❌ new | `saving \|\| photos<4` | `Need N more photo(s)` / `Ready to submit · Safety + PM will be notified` | same as above | No (`validate()`) |
| Bottom end `submit-bottom-btn` (L1318) | ✅ | `saving \|\| photos<4` | inline `Need N more photo(s) before you can submit` (L1311) + completion-summary banner (L1290) | same as above | No (`validate()`) |

**Gating coherence**: ✅ All three surfaces carry identical disabled policy and route to the same `submit()` handler.

---

## 2 · NewDailyReport.jsx

| Surface | Pre-existing? | Disabled-when | Hint copy | Validation gate on click | Premature submit? |
|---|:-:|---|---|---|:-:|
| Top sticky header `submit-top-btn` (L941) | ✅ | `saving` only | none | project name · location · prepared_by · Delays-Yes⇒row · Weather-Yes⇒weather row · safety-escalation chain (5 fields) · photos ≥ `photo_min` (6) · signature | No (`validate()`) |
| Sticky footer `submit-sticky-btn` (L2246) **+Rank #1** | ❌ new | `saving` only | `Need N more photo(s)` / `Ready to submit · PM distribution will send` | same as above | No (`validate()`) |
| Bottom end `submit-bottom-btn` (L2203) | ✅ | **`saving \|\| photosCount<photoMin`** | inline `Need N more photo(s) before submit` | same as above | No (`validate()`) |

**Gating coherence**: ⚠️ **Mismatch.** Top + Rank #1 sticky footer are permissive (`saving` only). Bottom-end is restrictive (also photo-gated). The Rank #1 sticky footer's hint copy (`Need N more photo(s)`) is at odds with its own clickable state. Discipline is preserved at the submit handler — but the visible affordance contradicts itself.

---

## 3 · NewInspection.jsx

| Surface | Pre-existing? | Disabled-when | Hint copy | Validation gate on click | Premature submit? |
|---|:-:|---|---|---|:-:|
| Top sticky header `submit-top-btn` (L293) | ✅ | `saving \|\| photos<4` | none | required-field labels · inspector + foreman signatures · 4 photos | No (`validate()`) |
| Sticky footer `submit-sticky-btn` (L813) **+Rank #1** | ❌ new | `saving \|\| photos<4` | `Need N more photo(s)` / `Ready to submit · graded on file` | same as above | No (`validate()`) |
| Bottom end `submit-bottom-btn` (L766) | ✅ | `saving \|\| photos<4` | (live `GradeBanner` above) | same as above | No (`validate()`) |

**Gating coherence**: ✅ All three surfaces identical.

---

## 4 · NewQaqcInspection.jsx

| Surface | Pre-existing? | Disabled-when | Hint copy | Validation gate on click | Premature submit? |
|---|:-:|---|---|---|:-:|
| Form-level sticky bottom `qaqc-submit` (L563) | ✅ | `saving \|\| photos<4` | inline `qaqc-submit-photos-hint` (L549) + button label rotation `Need 4 photos to submit` / `Submit Inspection` | checklist-all-answered · every-fail-has-note · 4 photos · signatures · concrete-form extras | No (`toast.error(fails[0])`) |

**Gating coherence**: ✅ Single coherent Submit. Untouched by Rank #1.

---

## 5 · NewSafetyEquipmentIssuance.jsx

| Surface | Pre-existing? | Disabled-when | Hint copy | Validation gate on click | Premature submit? |
|---|:-:|---|---|---|:-:|
| Form-level sticky bottom `iss-submit` (L608) | ✅ | `saving \|\| photos<1` | inline `iss-submit-photos-hint` + label rotation `Photo required` / `Submit & Email PDF` | required-field labels · ≥1 photo · signatures | No (`toast.error(fails[0])`) |

**Gating coherence**: ✅ Single coherent Submit. Untouched by Rank #1.

---

## 6 · NewSafetyEquipmentTraining.jsx

| Surface | Pre-existing? | Disabled-when | Hint copy | Validation gate on click | Premature submit? |
|---|:-:|---|---|---|:-:|
| Form-level sticky bottom `trn-submit` (L460) | ✅ | `saving` only | "Auto-emails Safety dept on submit" microcopy + button label `Submit & Email PDF` | required-field labels · instructor signature (no photo gate on this form) | No (`toast.error(fails[0])`) |

**Gating coherence**: ✅ Single coherent Submit; no photo gate by design. Untouched by Rank #1.

---

## Gating-coherence summary

| Form | Pre-Rank #1 button policy | Rank #1 sticky policy | Coherent? |
|---|---|---|:-:|
| NewIncident | top + bottom both `saving \|\| photos<4` | `saving \|\| photos<4` | ✅ |
| NewDailyReport | **top `saving`** vs **bottom `saving \|\| photos<min`** | `saving` | ⚠️ inherits top's permissive policy; bottom remains stricter |
| NewInspection | top + bottom both `saving \|\| photos<4` | `saving \|\| photos<4` | ✅ |
| NewQaqcInspection | single `saving \|\| photos<4` | n/a | ✅ |
| NewSafetyEquipmentIssuance | single `saving \|\| photos<1` | n/a | ✅ |
| NewSafetyEquipmentTraining | single `saving` (no photo gate) | n/a | ✅ |

Only **NewDailyReport** has a policy split. That split predates Rank #1; Rank #1 inherited it.

---

## Submit-handler gate (architectural · cross-form)

For every form, the **canonical** gate is the submit handler, which runs `validate()` and returns false (toast.error) for every missing required field before any network write. Button `disabled={…}` is a UI affordance, not the gate. This is consistent across all six forms and was not changed by Rank #1.

A premature data write to the API was **impossible before Rank #1** and **remains impossible after Rank #1** on all six forms.
