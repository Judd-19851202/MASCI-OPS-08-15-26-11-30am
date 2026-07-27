# BCSS Roadmap Snapshot

## 2026-07-25 — Wave 3 Family 3 Re-Scope

Repository-backed Wave 3 family structure:

- Wave 3 Family 3A — Core Admin Operations
  - owner: `/app/backend/routes/admin_ops.py`
  - classification: read-only administrative surface
  - phase B authorization: **authorized now**

- Wave 3 Family 3B — Operations Actions
  - repository owner: `/app/backend/routes/operations_actions/api.py`
  - status: Phase B complete / independently verified / READY FOR FORMAL ADOPTION
  - canonical auth contract: one acting portal token + bound `X-Directory-Token`

- Wave 3 Family 3C — Operational Events
  - repository owner: `/app/backend/routes/operational_events.py`
  - status: Phase B complete / independently verified / READY FOR FORMAL ADOPTION
  - canonical normalized store: `operational_events`
  - admin auth contract: `X-Admin-Token` + bound `X-Directory-Token`

- Wave 3 Family 3D — Asset Mapping & Reconciliation
  - repository owner: `/app/backend/routes/asset_mapping_recon.py`
  - status: future discovery track only

## Locked master sequence

- Next bounded track: Wave 3 Family 3D — Asset Mapping & Reconciliation Phase A Discovery (only if repository evidence supports it)
- Complete Wave 3 families
- Wave 3 Formal Closeout
- Platform Survivability Program
- Production Readiness Review
- Wave 1 Deployment

## Deployment gate

Platform Survivability Program remains the mandatory, non-bypassable gate before PRR or deployment, including independent evidence for backups, Cloudflare R2 hourly backups, integrity, retention, monitoring, alerting, restore testing, rollback testing, disaster recovery, and business continuity.

## 2026-07-27 — Survivability status update

- Restore certification gate: **closed / verified in Preview**
- TRACK D-02 Backup & DR Preview certification: **verified in Preview**
  - superseded authoritative archive: `MASCI_complete_backup_2026-07-27_021533Z.zip`
  - latest Preview RPO: `GREEN`
  - latest Preview drill outcome: `ok`
- S1-2 Secrets & Configuration Recovery Certification: **verified in Preview**
- S1-3 Backup Verification Hardening: **verified in Preview**
- S1-4 Notification Delivery Certification: **implementation complete / blocked on invalid Resend API key**
  - authoritative attempted run: `s1-4-cert-e217a5ffd8` / `DR-2026-03557`
  - scoped Preview override: verified
  - current blocker: provider returns `API key is invalid`
  - current authoritative archive: `MASCI_complete_backup_2026-07-27_111254Z.zip`
  - authoritative archive location: `backups/preview/auto-90d/`
  - confidence contract: `HIGH` only with direct sidecar manifest + checksum + lineage reconciliation

### P1 next
- Rotate `RESEND_API_KEY`, restart backend, and re-run exactly one bounded S1-4 certification message to complete provider submission + webhook/provider reconciliation
- Append final proof source (`WEBHOOK`, `PROVIDER_API`, or `BOTH`) to `/app/memory/S1_4_NOTIFICATION_DELIVERY_CERTIFICATION_EVIDENCE.md`

### P2 later
- Production Readiness Review (PRR) execution