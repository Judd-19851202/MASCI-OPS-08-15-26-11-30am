# Track 19.18 · Technical Cleanup Report

Scope: cleanup only where zero-drift is maintained. No behavior changes.

## 1. Dead `eslint-disable` directives removed

`/app/frontend/src/pages/IncidentReport.jsx` — four `eslint-disable-next-line react-hooks/exhaustive-deps` directives were flagged by the linter as "unused" (the underlying rule stopped triggering after earlier hardening). All four removed.

Before: 4 unused directive warnings.  
After: 0 warnings.

## 2. `report_render.py` SyntaxError fix (carried from 19.17)

An f-string with an escaped-quote inside `p.get(\"index\")` prevented the module from importing. Refactored the alt-text into a named local (`alt_text`) so the f-string expression stays legal on Python 3.11.

Verified: `python -c "from incident_engine import report_render"` succeeds.

## 3. Backend/frontend Spanish label alignment for `security`

`constants.py` had `("security", "Security", "Seguridad")` while the frontend used "Site Security" / "Seguridad del Sitio". Because backend labels can surface in PDFs and emails, this was a latent i18n drift risk.

Aligned to: `("security", "Site Security", "Seguridad del Sitio")`.  
Zero-drift preserved — `security` is a Track 19.17 additive type, not a legacy 19.16 baseline.

## 4. Not touched (by policy)

- Legacy `/api/incidents` route — untouched.
- Legacy incident schemas — untouched.
- Pre-existing 706-baseline i18n duplicate keys — **not deduped in this track**. Deduping is a separate cleanup pass; deduping them here would obscure the Track 19.18 diff. All my new keys are unique.
- No refactor of the incident-engine module structure. `reports.py`, `report_render.py`, `constants.py`, `vocabulary.py`, `state_machine.py` all left in place.

## 5. Consolidation candidates deferred

Deferred to a future dedicated cleanup track (would touch too many files for a polish pass):

- Move the `HIGH_SEVERITY` set from `IncidentReport.jsx` to `incidentReportSchema.js` (severity as schema metadata).
- Extract shared timeline dot-color helper from `SafetyCaseWorkspace.jsx` if reused by the Incident Report Viewer.
- Consolidate the ~700 pre-existing i18n duplicate keys.

Each of these is safe but would balloon the diff.

## 6. Files touched

```
backend/incident_engine/constants.py     (label alignment)
backend/incident_engine/report_render.py (Track 19.18 cover/exec/timeline/rca upgrade)
backend/tests/test_track_19_18_pdf_excellence.py            (NEW)
backend/tests/test_track_19_18_safety_case_workspace.py     (NEW)
frontend/src/pages/SafetyCaseWorkspace.jsx (Track 19.18 polish)
frontend/src/pages/IncidentReport.jsx      (eslint-disable cleanup)
frontend/src/lib/i18n.js                   (Track 19.18 EN→ES entries)
```

Total surface: 7 files. Additive, focused, reversible.
