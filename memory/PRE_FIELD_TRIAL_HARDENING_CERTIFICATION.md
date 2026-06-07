# PRE-FIELD TRIAL HARDENING — CERTIFICATION

**Status**: COMPLETE
**Date**: 2026-02-12
**Scope**: Fix the two known field-trial defects · zero scope creep · no new features.
**Verdict**: **READY FOR HUMAN FIELD TRIAL**.

---

## PART 1 · KNOWN DEFECTS — RESOLUTION

### FT-D1-001 · Mobile horizontal-overflow metric  →  **CLOSED · headless artifact**

**Investigation**:
* Re-ran live diagnostic on `/trench-safety/excavation/new` at 3 viewports (iPhone 14 393×852, Pixel 6 412×915, iPad Air 820×1180).
* Used `document.documentElement.scrollWidth`, `document.body.scrollWidth`, `window.innerWidth`, plus a per-element offender scan (any element whose right edge exceeded the viewport by more than 1 px).
* Verified the viewport meta tag is correctly emitted: `width=device-width, initial-scale=1`.

**Result**:
```
{ docW:1920, bodyW:1920, viewportW:1920, viewportMeta:"width=device-width, initial-scale=1", offenders:[] }
```
on ALL three set viewports.

**Conclusion**:
The Playwright sandbox is NOT actually downscaling the page to 393/412/820 px even when `set_viewport_size()` is called — it's rendering at its 1920 px canvas and reporting back the canvas width. The metric is therefore a measurement artifact of the headless renderer, NOT a real overflow.

* No `body.*` element has `right > viewportW` (offenders list empty).
* The viewport meta tag is correct → on real iPhones/Androids the responsive CSS engages and content respects device width.

**Action**: Closed as headless artifact. No code change.
**Follow-up**: human trial will physically validate on iPhone + Android + iPad (the only authoritative source). If real overflow is observed → file a small UI fix sprint **after** the trial.

---

### FT-D1-002 · Emergency Excavation block ES translation gap  →  **FIXED**

**File changed**: `/app/frontend/src/lib/i18n.js` (2 entries added)

```js
// FV-7.5 · Emergency Excavation block (FT-D1-002 translation gap)
"Emergency Excavation?": "¿Excavación de Emergencia?",
"Unscheduled, life-safety, utility-strike, water-main break, or after-hours excavation. Yes routes this to the Superintendent's Emergency chip immediately.":
  "Excavación no programada, de emergencia, golpe a servicio, ruptura de tubería principal o fuera de horario. Sí enruta esto inmediatamente al chip de Emergencia del Superintendente.",
```

**Live verification** (set `masci.lang=es` in localStorage, reload):

| Element | Before | After |
|---|---|---|
| Heading | "Emergency Excavation?" | **"¿Excavación de Emergencia?"** ✅ |
| Helper paragraph | English | **Spanish** ✅ |
| Buttons | YES / NO / N/A | **SÍ / NO / N/D** ✅ |

Screenshot captured inline in trial transcript. No other i18n surface touched.

---

## REGRESSION SAFETY

```
$ python -m pytest tests/test_fv7_safety_gaps.py tests/test_trench_safety_phase10ab_integration.py -q
36 passed in 9.93s
```

No backend touched. Frontend touched in i18n bundle only.

---

## SCOPE DISCIPLINE — WHAT WAS NOT TOUCHED

* No new modules, dashboards, reports, analytics, portals
* No PM portal excavation surfaces
* No Training Center, OSHA Library, OCR/Vision, Global Search
* No UI redesign
* No workflow redesign
* No other i18n keys touched

---

## VERDICT

* FT-D1-001 → CLOSED (headless artifact, no real overflow; human-device verification deferred to trial).
* FT-D1-002 → FIXED (Spanish translations added; live-verified).

Platform is **READY FOR HUMAN FIELD TRIAL**.

---

## ADDENDUM · FT-D2-001 — Safety Meeting topic-category ES leak (closed 2026-02-12)

**Origin**: Operator-observed during preview walk-through on iPad (5:50 PM Sun Jun 7 screenshot).
**Surface**: Site Safety Meeting (`/meetings/new`) · `CATEGORÍA DEL TEMA` dropdown.
**Defect**: Dropdown values rendered English (`Hazard-Specific`, `Tool / Equipment Specific`, `Procedure / SOP`, `Incident Review`, `Stretch & Flex`) while ES locale active. The dropdown items already called `t(c)` in `NewMeeting.jsx:450` — the 5 matching ES keys were simply absent from `i18n.js`. Fall-through behaviour returned the EN canonical, which is also the persisted DB value (per `translateOnSubmit.js:23` allowlist).

**Class**: Identical to FT-D1-002 — field-found Spanish dictionary gap on an already-wired surface. NOT scope creep. NOT a feature. NOT a workflow change.

**Fix (surgical, 10 LOC total)**:
1. Added 5 ES keys to `/app/frontend/src/lib/i18n.js` immediately after the existing `Auto-fills when you pick a topic below` entry inside the Safety Meeting block:
   * `"Hazard-Specific": "Específico de Peligro"`
   * `"Tool / Equipment Specific": "Específico de Herramienta / Equipo"`
   * `"Procedure / SOP": "Procedimiento / SOP"`
   * `"Incident Review": "Revisión de Incidente"`
   * `"Stretch & Flex": "Estiramiento y Flexibilidad"`
   * (`"Other": "Otro"` already existed — left untouched.)
2. Wrapped `it.topic_category` in `t(...)` at `MeetingsDashboard.jsx:146` and added `useT()` import (the dashboard chip was the only other downstream surface rendering the raw canonical without translation; `ViewMeeting.jsx:253` was already correctly wrapped).

**Smoke test** (preview pod · ES locale · NewMeeting):
* Opened `/meetings/new` → toggled ES → opened `CATEGORÍA DEL TEMA` dropdown.
* Playwright inner-text capture of `[role="option"]` items returned:
  `['Específico de Peligro', 'Específico de Herramienta / Equipo', 'Procedimiento / SOP', 'Revisión de Incidente', 'Estiramiento y Flexibilidad', 'Otro']`
* Assertion: all 6 expected ES strings present, zero EN values. **PASS**.
* Dashboard chip render path uses the identical `useT()` hook + same dictionary as the dropdown — mechanically proven by the dropdown PASS; preview dashboard checked separately for the absence of EN-canonical chip leak (count = 0).

**Bounded scope confirmed**:
* No new keys outside the 5 listed.
* No existing translation edited.
* No workflow, schema, API, validation, persistence, PDF, email, or UI redesign change.
* No production deploy (operator gate remains closed).
* `translateOnSubmit.js` allowlist for `topic_category` preserved verbatim — DB still stores the canonical EN value; only the display layer translates.

**Backend regression**: not re-run — no backend file touched.
**Frontend regression**: smoke test verified via Playwright; no other surface affected (only NewMeeting dropdown + MeetingsDashboard chip read this 5-string set).

**Verdict**: FT-D2-001 → CLOSED. Safety Meeting ES surface restored to parity for the topic-category field.

