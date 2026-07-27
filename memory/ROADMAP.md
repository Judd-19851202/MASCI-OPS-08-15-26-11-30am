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
  - latest authoritative archive: `MASCI_complete_backup_2026-07-27_021533Z.zip`
  - latest Preview RPO: `GREEN`
  - latest Preview drill outcome: `ok`

### P1 next
- Secrets and Configuration Recovery Certification (S1-2)
- Backup Verification Hardening (S1-3): raise lineage confidence from `MEDIUM` to `HIGH` by binding newest-manifest evidence directly into authoritative preview reporting paths
- Notification Delivery Certification (S1-4)

### P2 later
- Production Readiness Review (PRR) execution