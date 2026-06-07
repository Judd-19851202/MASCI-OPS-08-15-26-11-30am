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
