# FINAL Field Usability Certification

**5:30 AM Foreman Test:** A tired field user on an iPad or phone must know exactly what to do without training, IT support, or guessing.

**Verdict:** 🟢 **PASS**

## Test surface

6 auth-free field forms walked in the actual preview browser:

| Route | Form | Verified |
|---|---|:-:|
| `/incidents/report` | Incident Report picker + 17 branches | ✅ |
| `/daily/submit` | Daily Job Report | ✅ |
| `/equipment/submit` | Equipment Pre-Op Inspection | ✅ |
| `/fleet/dvir/new` | Daily Vehicle Inspection (DVIR) | ✅ |
| `/meetings/submit` | Site Safety Meeting / Toolbox Talk | ✅ |
| `/near-miss` | Anonymous near-miss kiosk | ✅ |

## Cross-form shared shell (Zero-Drift verified)

Every field form ships with the same certified operational shell:

- **Preview environment band** — persistent orange warning `⚠ PREVIEW ENVIRONMENT · DB: MASCI_SAFETY_PREVIEW · DO NOT ENTER REAL OPERATIONAL DATA` (visible on every screenshot).
- **Slate-black header** with MASCI wordmark, online indicator, EN/ES toggle, Submit CTA + Missing-fields chip.
- **`FormShell`** wrapper (Track 19.15 · locked).
- **`ProgressRail`** with numbered/labeled steps + percent progress.
- **`JobPicker`** — MASCI job search + Custom Job fallback (Track 19.16 batch 1).
- **`EmployeePicker` / `VehiclePicker` / `EquipmentPicker`** where applicable (Track 19.16 batch 2).
- **`PhotoCaptureField`** with camera gate (Track 19.16 batch 2).
- **`HelpDrawer`** — every step has "? OPEN HELP" for context-sensitive coaching.
- **Weather auto-fetch** (Daily Report) via Open-Meteo.
- **`SubmitReviewPanel`** — Submit disabled with reason chip until required fields complete.
- **Draft persistence** — local-first, autosave every keystroke, "SAVED JUST NOW" indicator.
- **Translation-on-submit** doctrine — user types in native language; server stores in EN where designed.

## Field usability checklist (all forms)

| Criterion | Result |
|---|:-:|
| Start from blank | ✅ · autosave engages immediately |
| Draft restore on page reload | ✅ · localStorage keyed by form + identity |
| Smart Prefill (identity, last job, last superintendent) | ✅ · Track 19.16 UX Hardening batches 1+2 |
| Spanish mode completion | ✅ · language toggle round-trips |
| Add/remove rows (crew, equipment, materials) | ✅ · patterns identical across forms |
| Failure triggers (Pre-Op FAIL → OOS cascade) | ✅ · Track 19.16 |
| Photo upload | ✅ · camera gate + GPS + caption |
| Attachment upload where available | ✅ |
| Signature capture | ✅ |
| Required-field validation (helpful, not raw errors) | ✅ · "Missing: X, Y, Z" chip |
| No console errors | ✅ · testing agent verified 0 errors on 6 routes |
| No React error overlay | ✅ |
| No repeated session modal loops | ✅ · session-refresh doctrine intact |
| No English-only strings in Spanish mode | ✅ · Track 19.18 bilingual sweep |
| Cross-actor draft bleed prevented | ✅ · identity-keyed local storage |
| HR roster reflects source-of-truth | ✅ · EmployeePicker fetches live HR |

## Mobile (375×667 · iPhone SE proxy)

- No horizontal overflow (`scrollWidth === clientWidth === 375`)
- Sticky header (`position: sticky; top: 0`)
- ES/EN toggle within thumb reach (44×44 hit target)
- 2 incident cards fully visible + 3rd partially in-fold before scroll

**One P2 cosmetic** noted for post-deploy backlog: tighten `/incidents/report` initial-fold vertical density on 375-wide viewports so a 3rd card is fully in-view without any scroll.

## Verdict

🟢 **Every field form works for a tired 5:30 AM foreman on an iPad. No confusion. No dead-ends.**
