# BCSS Roadmap Snapshot

## 2026-07-25 — Wave 3 Family 3 Re-Scope

Repository-backed Wave 3 family structure:

- Wave 3 Family 3A — Core Admin Operations
  - owner: `/app/backend/routes/admin_ops.py`
  - classification: read-only administrative surface
  - phase B authorization: **authorized now**

- Wave 3 Family 3B — Operations Actions
  - repository owner: `/app/backend/routes/operations_actions/api.py`
  - status: Phase B implementation in progress / bounded to Family 3B only
  - canonical auth contract: one acting portal token + bound `X-Directory-Token`

- Wave 3 Family 3C — Operational Events
  - repository owner: `/app/backend/routes/operational_events.py`
  - status: future discovery track only

- Wave 3 Family 3D — Asset Mapping & Reconciliation
  - repository owner: `/app/backend/routes/asset_mapping_recon.py`
  - status: future discovery track only

## Locked master sequence

- Complete Wave 3 families
- Wave 3 Formal Closeout
- Platform Survivability Program
- Production Readiness Review
- Wave 1 Deployment

## Deployment gate

Platform Survivability Program remains the mandatory, non-bypassable gate before PRR or deployment, including independent evidence for backups, Cloudflare R2 hourly backups, integrity, retention, monitoring, alerting, restore testing, rollback testing, disaster recovery, and business continuity.