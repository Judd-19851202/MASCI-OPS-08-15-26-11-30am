# Wave 1.1 — Operational Timeline Sidecar · Implementation Summary

**Phase V-Prelude · Wave 1.1 · Elite Stabilization Pass**
**Status:** 🟢 **COMPLETE · preview env**
**Date:** 2026-05-28
**Authorization:** Operator command "PHASE V-PRELUDE · WAVE 1.1" (2026-05-28).
**Environment:** APP_ENV=preview · DB_NAME=masci_safety_preview.
**Production:** NOT TOUCHED.

---

## What this pass produced

Wave 1.1 is the **controlled-exposure step** for the Wave 1 substrate.
The Operational Timeline is now visible inside one — and only one —
high-context PM surface. No expansion of scope, no new endpoints, no
mutations, no notifications.

### Single surface
- **PM Project Detail** at `/pm/projects/:projectNumber` — a calm
  detail page that hosts the `OperationalTimelineSidecar` component.
- Entry: clickable `project_number` cells in `PmJobsRead`.
- Layout: project header + sidecar. No tiles, no KPIs, no charts.

### Sidecar contract (`OperationalTimelineSidecar.jsx`)
- **Passive** — no controls beyond a refresh icon. No "add event", no
  "edit", no "delete", no toggles.
- **Read-only** — sole call is `GET /api/timeline?project_id=...`.
- **Bounded** — `max-h-[420px]` scroll container; first 30 rows visible
  by default with a "Show all" affordance. No infinite-scroll trap.
- **Truncation flag** — surfaces calmly if backend `truncated=true`.
- **Role-aware** — backend already filters `audit-only` links from
  non-admin actors. No client-side role logic added.
- **Mobile-safe** — single-column rendering at 390 px; refresh control
  ≥32 px tap target; no body overflow.

---

## Files added / modified

### Added (frontend)
- `frontend/src/components/operational/OperationalTimelineSidecar.jsx`
- `frontend/src/pages/PmProjectDetail.jsx`

### Modified (frontend)
- `frontend/src/App.js` — added route `/pm/projects/:projectNumber`.
- `frontend/src/components/pm/PmJobsRead.jsx` — made `project_number`
  cell a `<Link>` (no new column, no row chrome).

### Added (backend tests)
- `backend/tests/test_v_prelude_wave1_1_sidecar.py` (8 tests).
- `backend/tests/pw_suite/test_v_prelude_wave1_1_sidecar_calmness.py`
  (10 Playwright tests across desktop · iPad · mobile).

### Updated (governance)
- `memory/TRUST_SURFACES.json` — registered
  `operational-timeline-sidecar` (passive=true).

### Backend
- **Zero backend code changes.** Wave 1.1 is read-only consumption of
  the existing `/api/timeline` substrate. No new endpoints, no schema
  changes.

---

## Doctrine adherence checklist

- [x] Sidecar mounts ONLY on PM Project Detail page (Wave 1.1 §2).
- [x] No dashboards, no home pages, no hub mounts.
- [x] Timeline remains passive + read-only (Wave 1.1 §10).
- [x] No timeline mutation controls (Wave 1.1 §8).
- [x] No notification expansion (Wave 1.1 §9).
- [x] No infinite-scroll history feeds — bounded `max-h-[420px]`.
- [x] No social-style activity stream — calm slate text via existing
      `ChronologyPanel`.
- [x] No new collection, no schema mutation.
- [x] No backend auth expansion — re-uses Wave 1's
      `_require_any_portal_token` gate.
- [x] Mobile-safe: thumb-safe controls (≥32 px) · no horizontal body
      overflow · single column.
- [x] TRUST-TIME-1 timestamps preserved end-to-end (Z-suffixed UTC ISO).
- [x] Reversible — drop the two new files, revert two `App.js` lines,
      revert one `PmJobsRead.jsx` cell.

---

## Test result

```
backend/tests/test_v_prelude_wave1_1_sidecar.py            — 8 passed
backend/tests/pw_suite/test_v_prelude_wave1_1_sidecar_calmness.py
    desktop · ipad · mobile sweep                          — 10 passed
                                                              (2 mobile-only
                                                              tests correctly
                                                              skipped on
                                                              desktop / ipad)
backend/tests/test_v_prelude_wave1_substrate.py            — 19 passed
                                                              (no regression)
```

## Doctrine probes — all green

```
authority_mismatch_probe         · 0 new violations  · 89 ms
timestamp_doctrine_probe         · 0 new violations  · 119 ms
operational_links_doctrine_probe · 0 violations      · sub-second
```

---

## What Wave 1.1 deliberately did NOT do

- ❌ Wave 2 work (Operational Search / Field Memory).
- ❌ RFI / Schedule / P6 implementation.
- ❌ Dashboard additions.
- ❌ Notification or fan-out expansion.
- ❌ Workflow automation.
- ❌ Timeline mutation controls.
- ❌ Multi-portal mount (no Safety/Dispatch/Admin/Exec hub mounts).
- ❌ Cross-project aggregation surface.

---

## Stop condition

Per operator directive:
> "After Wave 1.1: STOP. Remain inside 24-hour observation posture.
> Await explicit operator authorization: 'start V-Prelude Wave 2'."

Wave 2 is **LOCKED.**

— certified by E1 · V-Prelude Wave 1.1 · 2026-05-28
