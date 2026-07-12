# TRACK 27.09 · Backup Provenance, Integrity Truthfulness & Retention-Decision Readiness

Date: 2026-07-12
Execution mode: read-only production evidence collection

## Production identity

- app_env: `production`
- db_name: `masci_safety`
- source_hash: `9e79ada45d05d246df4819140c5fde91`
- storage_bucket: `masci-hub`

## Direct bucket truth

- Total objects: **10177**
- Total bytes: **350655277412**
- Backup objects: **876**
- Backup bytes: **347835260056**
- Backup share of bucket: **0.991958**

## Provenance lineage

- Newest backup: `backups/auto-90d/MASCI_complete_backup_2026-07-12_150040Z.zip`
- Oldest backup: `backups/MASCI_complete_backup_2026-05-11_141538Z.zip`
- Lineage groups: `{"auto-90d": {"bytes": 323666427987, "count": 376}, "legacy-root": {"bytes": 24168832069, "count": 500}}`
- Manifest coverage: `{"present": 368, "unknown": 508}`

## Observability defects

- Inventory `prefix=backups/` defect on deployed production: **FAIL**
- Integrity metadata defect on deployed production: **FAIL**

## Restore capability

- RPO status: **GREEN**
- RTO status: **AMBER**
- Last drill present: **False**
- Latest direct-R2 backup manifest: `MANIFEST.json`

## Duplicate / repetition evidence

- Duplicate ETag groups: **0**
- Duplicate manifest groups: **0**

## Operator decision readiness

The operator decision table is saved in `/app/memory/track_27_09/operator_decision_table.json`.

## Immutable evidence package

Saved under `/app/memory/track_27_09/` with SHA256 manifest in `evidence_manifest.json`.
Combined bundle hash: `18c8e49f5c2802b8146347ea70459395f0956a07874fb2bc0e262448d2df2f0f`
