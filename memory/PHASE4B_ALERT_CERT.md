# PHASE 4B — ALERT CERTIFICATION

**Phase:** 4B · Alerts (in-app only — per operator decision)
**Date:** 2026-02
**Verdict:** 🟢 **PASS**

## Architecture
**No new alerts collection.** Alerts are a derived projection computed on-demand from the existing source-of-truth collections (`trench_safety_assets`, `trench_safety_holds`, `trench_safety_certifications`, `trench_safety_inspections`). This guarantees alerts cannot drift from the operational state.

## Endpoint
`GET /api/trench-safety/alerts?asset_id=…&kind=…` — returns `{alerts: [{asset_id, kind, severity, opened_at, message, link, source_ref}], count, counts: {<kind>: n}, generated_at}`.

## Alert kinds covered
- `failed_inspection`
- `critical_damage`
- `hold_applied` (one per active hold)
- `expired_certification`
- `missing_certification`
- `due_soon_30` / `due_soon_60` / `due_soon_90`
- `inspection_overdue`

## Delivery (in-app only — per operator decision)
- Safety Portal alerts page (consumed by Hub banner)
- Asset Detail header (per-asset alerts)
- Project Panel (per-row hold + cert status)
- Public field view (`TrenchSafetyQrLanding`) — DO-NOT-USE banner now covers Safety / Certification / Maintenance / Inspection Holds (Phase 4B extension)

## Out of scope (operator-locked)
- No Resend email expansion
- No Twilio SMS expansion

## Tests (all PASS)
- `test_alerts_endpoint_returns_failed_inspection_alert`
- `test_alerts_endpoint_returns_critical_damage_alert`
- `test_alerts_filter_by_kind`

## Conclusion
🟢 Alerts are deterministic, derived, in-app only. **NO disconnected alert pipelines exist.**
