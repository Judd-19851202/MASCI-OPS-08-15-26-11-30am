# Regression Protection Plan

Date: 2026-07-14
Track: DR-01

## Existing tests worth preserving

### Draft continuity / actor isolation
- `frontend/src/lib/__tests__/track_26_08_daily_report_draft_continuity.test.jsx`
- `backend/tests/test_track_19_04_form_session_isolation.py`

### Draft telemetry health contract
- `backend/tests/test_daily_report_draft_health_contract.py`

### Smart Prefill / crew-hours amendment contract
- `backend/tests/test_track_19_06_amendment_smart_prefill_crew_hours.py`

### Daily Report recovery contract
- `backend/tests/test_track_26_02_daily_report_recovery.py`

## Missing regression locks that should be added during repair

### G1 · Active shell parity
Assert that whichever shell `DailyReportRouter` can serve has:
- the canonical draft base key
- the canonical scope contract
- Smart Prefill availability
- queue/idempotency parity

### G2 · Scope stability
Assert Daily Report draft scope does **not** change when `report_number` preview arrives.

### G3 · Cross-shell draft continuity
Assert a draft written in one shell is restorable from the other shell if both remain routed.

### G4 · Queue repair parity
Assert V3 queue items hit the same Daily Report repair logic as V1.

### G5 · Single Smart Prefill apply path
Assert exactly one explicit Smart Prefill apply function exists in the active shell.

### G6 · `crewMemory` boundary
Assert local setup memory UI is not reused for server `recent-context` offers.

### G7 · Lifecycle flush reality
Add browser-level regression around pagehide / background / tab close on the active shell, especially iPad/Safari-class behavior.

## Certification-oriented test matrix

| Area | Static contract | Browser flow | Backend/API |
|---|---|---|---|
| Draft key parity | Yes | Yes | N/A |
| Draft restore | Yes | Yes | N/A |
| Queue retry | Partial | Yes | N/A |
| Smart Prefill availability | Yes | Yes | Yes (`/recent-context`) |
| Smart Prefill apply semantics | Yes | Yes | Yes |
| V2 legacy containment | Yes | N/A | Yes |

## Protection principle

The next repair should not only fix the reported symptoms. It must lock the **absence of shell drift** as a tested invariant.
