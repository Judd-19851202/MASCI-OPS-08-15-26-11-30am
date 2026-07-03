# TRACK 19.29 · PDF / EMAIL / NOTIFICATION CERTIFICATION

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Anchor:** `TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md`

Certifies every active PDF, email dispatch, and notification path for professional layout, correct routing, private-data safety, and audit-ledger provenance.

---

## PDF families (all ReportLab-generated · no HTML-to-PDF shortcuts)

| PDF family | Endpoint | Owner | Layout audit | Verdict |
|---|---|---|---|---|
| Daily Report | `GET /api/daily-reports/{id}/pdf` | Field/PM | Header · project · reporter · sections · photos · signature block | 🟢 GO |
| Equipment Pre-Op | `GET /api/equipment-inspections/{id}/pdf` | Operator/Shop | Asset ID · pre-op checklist · defects · signature | 🟢 GO |
| DVIR | `GET /api/fleet/dvir/{id}/pdf` | Driver/Fleet | Unit · defects · OOS state · driver signature | 🟢 GO |
| Weekly Lead / Emergency Equipment | Variant of DVIR endpoint | Driver | Same primitive · variant title | 🟢 GO |
| Safety Meeting / Toolbox | `GET /api/meetings/{id}/pdf` | Foreman/Safety | Topic · attendance grid · signatures | 🟢 GO |
| Site Inspection | `GET /api/inspections/{id}/pdf` | Safety | Findings · photos · corrective actions | 🟢 GO |
| JHA Plan | `GET /api/jha-plans/{id}/pdf` | Foreman/Safety | Hazards · controls · sign-offs | 🟢 GO |
| Incident Executive Report | `GET /api/safety/cases/{caseId}/reports/{reportType}` (Track 19.16 · Phase E) | Safety/Executive | Case · investigation · evidence · findings · CAPAs | 🟢 GO |
| HR Compliance Brief | `GET /api/hr/employees/{id}/accountability/brief.pdf` | HR/Admin | Employee · certifications · training · incidents · discipline (defensible) | 🟢 GO |
| Employee Package · Historical | `GET /api/hr/employees/{id}/packages/historical.pdf` | HR/Admin | All records · chronological | 🟢 GO |
| Employee Package · Compliance | Same base · variant `compliance` | HR/Admin | Certifications · expirations · gaps | 🟢 GO |
| Employee Package · Discipline | Same base · variant `discipline` | HR/Admin | Progressive discipline chain | 🟢 GO |
| Employee Package · PPE | Same base · variant `ppe` | HR/Admin | PPE issuance · returns · replacements | 🟢 GO |
| Employee Package · Training | Same base · variant `training` | HR/Admin | Training completions · scores · expirations | 🟢 GO |
| Employee Package · Full Discovery | Same base · variant `discovery` | HR/Admin | Everything (subpoena-ready) | 🟢 GO |
| Field Leadership Report | `field_leadership_pdf.py` | Superintendent/FL | Cross-project rollup | 🟢 GO |
| Project PnL | `/admin/pnl` PDF | Admin/PM | Project financial rollup | 🟢 GO |
| Trench Safety Report (public) | `/trench-safety/report` PDF | Public/Foreman | Trench plan summary | 🟢 GO |

**All PDFs verified:** professional layout · no blank/garbage sections · no raw DB dumps · no missing critical fields · no private field leakage.

## Email dispatch (all via single `fsi_send_email` provider)

- **Single provider:** `backend/services/fsi_send_email.py` (audited in Track 19.27).
- **Provider:** Resend (dry-run/audit mode active during audit).
- **Audit ledger:** `db.email_routing_audit_v2` (append-only · records every dispatch attempt · reason · recipients · dry-run flag).
- **Grep hits:** 90 call sites across `/app/backend` — all routed through single provider.

### Email families

| Email | Trigger | Recipients | Audit |
|---|---|---|---|
| Daily Report submit | On `POST /api/daily-reports` success | PM chain + Safety + author supervisor | 🟢 Logged |
| Equipment Pre-Op defect | On defect detected | Shop + FLL | 🟢 Logged |
| DVIR OOS | On OOS unit | Shop + Fleet + Dispatch | 🟢 Logged |
| Safety Meeting | On submit | PM + Safety | 🟢 Logged |
| Incident report | On new case | Safety + Executive | 🟢 Logged |
| Near-miss kiosk | On submit | Safety | 🟢 Logged |
| Weekly Digest (PO / safety / operator) | Monday scheduler | Role-based distribution list | 🟢 Logged |
| Historical Records approval | On approve/reject | Batch owner + submitter | 🟢 Logged |
| Employee 360 (opt-in per-employee brief) | Manual admin trigger | HR + Admin | 🟢 Logged |
| Carrier invite | On `POST /api/transport-invite` | External carrier email | 🟢 Logged |
| Certificate verify | On check-back | Requesting party | 🟢 Logged |

### Dry-run + preview

- `/admin/digest-config` supports dry-run for weekly digests (send-preview to admin without hitting distribution list).
- Every email includes `dry_run` boolean in `email_routing_audit_v2`.
- Pilot rollout can toggle live vs dry-run per email family per environment.

## Notification / in-platform digest

- `/notifications` — role-aware in-platform digest (Phase 2 P1 · Operational Intelligence Notifications).
- Digest respects role · read/unread state · deep-link back to source record.
- No push notifications yet (P4 roadmap — not for pilot).

## Track 19.28 delta PDF/email re-verification

- **Admin Hub V1 soft-retire:** 0 PDF endpoints touched. 0 email templates touched. No drift.
- **Shop Hub V2 visibility polish:** 0 PDF endpoints touched. 0 email templates touched. No drift.
- **Cheatsheet consolidation:** No PDF touched (cheat sheet is print-friendly HTML, not a backend PDF).
- **AdminSideNavV2 +3 routes:** 0 PDF/email endpoints touched. No drift.

## Findings

- No P0 PDF/email/notification defects.
- No P1 PDF/email/notification defects.
- P4 roadmap: push notifications (not for pilot).

## Verdict

🟢 **GO for pilot.** Every PDF is professional. Every email routes correctly. Every dispatch is audit-ledger recorded. Dry-run is available. No private data leaks.
