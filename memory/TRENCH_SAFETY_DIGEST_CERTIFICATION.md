# Phase 7.5C · Digest Certification

## Reuse path
`backend/routes/trench_safety/notifications.py:build_trench_digest_section(db)` is the canonical builder. Consumed by:
- `backend/routes/notifications.py:_build_safety_digest` (Safety Hub live digest `/api/safety/notifications/digest`).
- The weekly Safety Digest cron (`safety_digest.py`) inherits it through the shared aggregator.

No new cron. No new collection.

## Metrics included (per directive)
| Metric | Source query |
|---|---|
| Open Safety Holds | `trench_safety_holds` where `is_active=true` and `kind="Safety Hold"` |
| Open Certification Holds | same, `kind="Certification Hold"` |
| Open Inspection Holds | same, `kind="Inspection Hold"` |
| Open Maintenance Holds | same, `kind="Maintenance Hold"` |
| Repairs Awaiting Verification | `trench_safety_repairs` where `status="Completed"` and `requires_reinspection=true` |
| Expiring Certifications (30d) | `trench_safety_certifications` where `status="Active"` and `expires_at` in next 30 days |
| New Damage Reports (7d) | `trench_safety_repairs` where `source="Public QR Damage Report"` and `received_at` ≥ 7 days ago |
| Failed Inspections (7d) | `trench_safety_inspections` where `result="Fail"` and `submitted_at` ≥ 7 days ago |

All queries hit canonical collections — no parallel store, no caching layer.

## Live verification (admin token, preview env)
```
GET /api/safety/notifications/digest
→ ok: true
  sections includes { key: "trench_safety", title: "Trench Safety — 207 item(s) requiring attention", count: 207,
                      trench_safety: {
                        open_safety_holds: 4,
                        open_certification_holds: 0,
                        open_inspection_holds: 23,
                        open_maintenance_holds: 4,
                        repairs_awaiting_verification: 2,
                        expiring_certifications_30d: 0,
                        new_damage_reports_7d: 0,
                        failed_inspections_7d: 201,
                      } }
```

## How the weekly cron picks it up
The existing weekly Safety Digest renderer reads sections from the digest payload. Once Phase 7.5C is merged the trench section is part of the payload, so the Mon 14:00 UTC email automatically gains the trench safety block without any code change in `safety_digest.py`.

## Frontend exposure
- `NotificationBell` → reads `db.notifications` directly (unchanged).
- Safety Hub digest tile → reads `/api/safety/notifications/digest` → renders the new `trench_safety` section item like any other section.

## Severity ladder
- `severity: "high"` when `open_safety_holds > 0` (matches Safety Hold ⇒ Critical bell severity).
- `severity: "medium"` otherwise (matches existing digest grades).
