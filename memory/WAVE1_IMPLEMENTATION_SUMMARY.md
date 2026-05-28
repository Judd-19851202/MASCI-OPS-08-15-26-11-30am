# WAVE1 — Implementation Summary

**Phase V-Prelude · Wave 1 · Substrate Engineering**
**Status:** 🟢 **COMPLETE** (preview env)
**Date:** 2026-05-28
**Authorization:** Operator command "START V-PRELUDE WAVE 1" (2026-05-28).
**Environment:** APP_ENV=preview · DB_NAME=masci_safety_preview.
**Production:** NOT TOUCHED. Production deploy gated behind 24-hr
observation + explicit Wave 2 authorization.

---

## What this wave produced

Wave 1 builds **operational intelligence substrate** — the foundational
infrastructure every future operational system (RFI, Schedule, P6 import,
external response chains) will rely on. No RFI implementation, no
scheduling, no dashboards, no AI copilot, no auth expansion.

Four substrate components were delivered:

| Component | Purpose | Surface |
|---|---|---|
| **Operational Constraints** | Operational blocker memory | `/api/constraints` · `/constraints` |
| **Operational Links** | Single-source-of-truth relationship layer | `/api/operational-links` |
| **Operational Timeline** | Calm, read-only chronology aggregator | `/api/timeline` |
| **Photo Governance** | Thin governance metadata on existing photos | `/api/photos/:id/...` |

---

## Files added / modified

### Backend (new)
- `backend/routes/operational_links.py`
- `backend/routes/operational_constraints.py`
- `backend/routes/operational_timeline.py`
- `backend/routes/photo_governance.py`

### Backend (modified)
- `backend/server.py` — router mounts + index-ensure on startup.
  No mutation of any existing route, model, or capability.

### Frontend (new)
- `frontend/src/lib/constraintCapabilities.js`
- `frontend/src/lib/operationalApi.js`
- `frontend/src/components/operational/ChronologyPanel.jsx`
- `frontend/src/components/operational/SeverityPill.jsx`
- `frontend/src/pages/Constraints.jsx`
- `frontend/src/pages/NewConstraint.jsx`
- `frontend/src/pages/ConstraintDetail.jsx`

### Frontend (modified)
- `frontend/src/App.js` — three new `<Route>` mounts. No other change.

### Tests (new)
- `backend/tests/test_v_prelude_wave1_substrate.py` — **19 tests, all pass.**

### Doctrine probes (new)
- `scripts/operational_links_doctrine_probe.py`
- `scripts/pre_deploy_check.sh` — wired the new probe stage.

### Governance registries (updated)
- `memory/TRUST_SURFACES.json` — added `operational-constraints`,
  `operational-links`, `operational-timeline`, `photo-governance`.

---

## Doctrine adherence checklist

- [x] **OPERATIONAL_LINKING_RULES.md** §1–§11 implemented verbatim.
- [x] **OPERATIONAL_CONSTRAINT_FOUNDATION.md** API surface matches §4
      ("API surface — Wave 1").
- [x] **OPERATIONAL_TIMELINE_FOUNDATION.md** — read-only, ≤200 items,
      single project per call, newest-first.
- [x] **PHOTO_GOVERNANCE_STANDARD.md** — thin metadata layer, NO blob
      mutation, NO new collection, links via `operational_links`.
- [x] **TRUST-TIME-1** — every timestamp tz-aware `Z`-suffixed UTC ISO.
- [x] **No `_id` leak** — every response is a Pydantic model.
- [x] **No hard DELETE** — status flips only on links; void on
      constraints.
- [x] **No auth expansion** — reuses existing `_require_any_portal_token`.
- [x] **No visual doctrine drift** — calm, text-first; single-red
      severity pill; no charts, no gantt, no badges-of-engagement.
- [x] **Capability scoping** — `constraintCapabilities.js` mirrors
      `poCapabilities.js` (portal context FIRST gate, not token presence).
- [x] **Reversible** — drop the four router mounts in `server.js`,
      drop the three routes in `App.js`, delete the two collections.

---

## Backend test result

```
backend/tests/test_v_prelude_wave1_substrate.py — 19 passed in 7.01s
```

Covers:
- Constraint CRUD + chronology + resolve + chronology append.
- Link audit-field completeness, closed enums, forbidden inverses,
  self-link reject, circular `resulted_in` reject.
- Status transition matrix (active→archived→active; superseded terminal).
- Link creation does NOT mutate the target (§3).
- Project-scope filter (§7) honoured.
- Timeline sort + max-items + project_id required.
- Unauth requests rejected (401 / 403).

---

## Pre-deploy probes — all green

```
authority_mismatch_probe         · scan_ms=89   · 0 new violations
timestamp_doctrine_probe         · scan_ms=119  · 0 new violations
operational_links_doctrine_probe · scan_ms=733  · 0 new violations
```

---

## What this wave deliberately did NOT do

- ❌ RFI implementation — that's V.1 (locked until Wave 4 + 72-hr observ.).
- ❌ Schedule / P6 / XER ingestion — V.2/V.3 (locked).
- ❌ External response chains — V.4 (locked).
- ❌ Dashboard expansion — operational doctrine forbids it.
- ❌ AI copilot / auto-tag / auto-link — explicit doctrine veto.
- ❌ Auth expansion — reuses `_require_any_portal_token` verbatim.
- ❌ Production deploy — explicit Wave 1 hard rule.

---

## Stop condition

Per the operator directive:
> "After Wave 1 implementation: STOP. Enter 24-hour observation window.
> Await explicit operator authorization before Wave 2 begins."

This wave is **frozen** until the operator issues "start V-Prelude Wave 2".

— certified by E1 · V-Prelude Wave 1 · 2026-05-28
