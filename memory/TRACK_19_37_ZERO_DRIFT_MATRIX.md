# TRACK 19.37 · ZERO-DRIFT MATRIX

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

Proves Track 19.37 preserved every certified contract, permission, and workflow byte-for-byte.

---

## Zero-Drift Matrix

| Category | Status | Notes |
|---|---|---|
| Schemas (`incident_cases`, `incident_case_events`, `incident_case_evidence`, `corrective_actions`, `case_medical`, `case_agency_contacts`, `case_tasks`, `case_witnesses`, `case_communications`) | ✅ unchanged | No collection touched · no new indexes |
| Backend routes (existing) | ✅ unchanged | Every Phase A/C/D/E route preserved · Track 19.36 `/executive-intelligence` and `/executive-report.pdf` preserved |
| Payloads (existing) | ✅ unchanged | Scorer is a pure function |
| PDFs (existing) | ✅ unchanged | Track 19.16 Phase E and Track 19.36 boardroom PDF both preserved bit-for-bit · presence signals not yet in PDF |
| Emails | ✅ unchanged | Not touched · no new dispatches |
| Notifications | ✅ unchanged | Not touched |
| Permissions | ✅ unchanged | New endpoint uses existing Safety/Admin/PM read gate |
| Trust Spine | ✅ unchanged | Read-only surface |
| Audit events (`incident_case_events`) | ✅ unchanged | Append-only invariant preserved · no new event types |
| HR Source-of-Truth | ✅ unchanged | Not touched |
| Bilingual engine (`useT()`) | ✅ preserved | New panel uses same engine |
| Track 19.34 Field-vs-Safety grep invariant | ✅ preserved | No field-facing surface introduced |
| Track 19.35 Field Facts immutability | ✅ preserved | Workspace unchanged |
| Track 19.36 Executive Intelligence Model | ✅ additively extended | Version bumped 1.0.0 → 1.1.0 · all 20 original keys preserved · `attention_signals` added |
| CAPA state machine | ✅ unchanged | Read-only surface |
| No-auto-decision doctrine | ✅ enforced | Notice required in every payload · UI ban on forbidden vocabulary |
| Rollback paths | ✅ preserved | Additive-only |

## File-level change footprint

| Change | File | Type | Lines |
|---|---|---|---|
| Presence scorer | `backend/incident_engine/presence_score.py` | NEW | ~400 |
| Presence-score routes | `backend/incident_engine/presence_score_routes.py` | NEW | ~50 |
| Wire route + integrate into model | `backend/server.py` | EDIT | +14 |
| Import scorer + add `attention_signals` block + bump model version | `backend/incident_engine/executive_intelligence.py` | EDIT | +10 lines (+ 1-char version bump) |
| Attention Signals UI panel | `frontend/src/pages/ExecutiveCaseReport.jsx` | EDIT | +55 |

**Total: 2 new files · 3 files edited (all additive) · 0 files deleted.**

## Payload-level drift check

- All existing request/response bodies: unchanged.
- Executive Intelligence Model shape: **21 top-level keys** (20 preserved from Track 19.36 + 1 new `attention_signals`). No existing key renamed or dropped.
- New endpoint response shape: documented in `TRACK_19_37_PASSIVE_INCIDENT_PRESENCE_SCORING.md`.

## Permission drift check

- New endpoint uses the same `make_require_safety_admin_or_pm` gate as every other `/api/incident-cases/*` route.
- No public route affected.
- No permission grant changed.

## Legacy route drift check

- `/incidents/report`, `/incidents/new`, `/incidents/submit` — unchanged.
- `/safety/cases/:caseId`, `/safety/executive-intelligence`, `/safety/cases/:caseId/executive-report`, `/safety/cases/:caseId/reports/:reportType` — all unchanged.
- **NEW** `GET /api/incident-cases/{case_id}/presence-score` — additive only.

## PDF / email / notification drift check

- No modification to any PDF renderer, email dispatcher, or notification system.
- New scoring layer is JSON-only in v1.

## Audit event drift check

- `incident_case_events` append-only invariant preserved.
- No new event types.
- No new audit reasons.

## Doctrine drift check

- Track 19.34 field-facing grep invariant (`osha_recordable`, `root_cause`, `preventability`, `discipline`, `workers_comp`, `liability` absent from `incidentReportSchema.js` and `IncidentReport.jsx`) — **preserved.** Track 19.37 touches only Safety-gated surfaces.
- Track 19.35 Field Facts immutability — **preserved.** Workspace panel unchanged.
- Track 19.36 Executive Intelligence Model shape — **additively extended.** Model version bumped as required by Track 19.36 doctrine.

## Rollback drift check

Removing the scorer, the endpoint registration, the `attention_signals` block in the assembler, and the UI panel returns the platform to pre-19.37 state:
1. Delete `backend/incident_engine/presence_score.py`.
2. Delete `backend/incident_engine/presence_score_routes.py`.
3. Remove the `_register_ie_presence_score_routes(...)` block in `server.py`.
4. Remove the `attention_signals` block in `executive_intelligence.py` and revert `EXECUTIVE_INTELLIGENCE_MODEL_VERSION` to `"1.0.0"`.
5. Remove the Attention Signals `<Section>` block in `ExecutiveCaseReport.jsx`.

Rollback confidence: **HIGH.**

## Verdict

🟢 **Zero drift.** Track 19.37 is strictly additive. Every certified contract, permission, workflow, and doctrine is preserved.
