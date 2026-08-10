# PRE-C10 R2 Namespace Isolation + Provenance Retrospective

Date: 2026-08-10
Status: In force in preview codebase; PRE-C10 remains OPEN / NO-GO.

## 1) Scope of this bounded review

This review was limited to the user-directed P0 storage defect and to prior PRE-C10 repairs whose justification could have depended on treating preview records as if they were current production business truth.

This review does **not** reopen the full `117` already-closed obligations. A row is only reopened if there is concrete evidence that preview/provenance misunderstanding produced an incorrect implementation.

## 2) Storage blast radius inventory

### Canonical storage families reviewed

| Family | New write path | Read path(s) | Delete path(s) | Current governed ownership rule |
|---|---|---|---|---|
| `photos` | `backend/photo_storage.py::upload_photo_bytes` | `read_photo_bytes`, `read_photo_bytes_sync`, photo/gallery/operational consumers | `delete_photo` | New writes now land under `photos/{env}/...`; deletes only allowed for current-env-owned namespaced keys |
| `documents` | `backend/photo_storage.py::upload_document_data_url` | existing document/attachment consumers via `photo://` refs | `delete_photo` where reused | New writes now land under `documents/{env}/...`; legacy refs remain readable |
| `safety-docs` | `backend/safety_doc_storage.py::upload_doc_bytes` | `read_doc_bytes` | `delete_doc` | New writes now land under `safety-docs/{env}/...`; deletes blocked for legacy/unowned/cross-env keys |
| `promo-assets` | `backend/promo_assets_storage.py::upload_bytes` | `presigned_url`, admin promo asset routes | `delete_ref` | New writes now land under `promo-assets/{env}/...`; deletes blocked outside current env ownership |
| `backups` | `backend/server.py::_run_complete_archive_to_r2` via `upload_local_file` + sidecar `upload_bytes` | backup list/state/verification/recovery readers | no shared-bucket app delete path added here | Already governed under `backups/{env}/auto-90d/...`; explicit-key overwrite guard now prevents unsafe cross-env or legacy overwrite |

### Main affected runtime consumers confirmed

- `routes/operational_attachments.py`
- `routes/asset_documents.py`
- `routes/safety_portal/documents.py`
- `routes/safety_portal/fire_ext_attachments.py`
- `routes/promo_assets.py`
- `routes/operations_actions/api.py`
- backup/archive flows in `backend/server.py`

### Architectural contract now implemented

1. New environment-aware writes are deterministic in both preview and production.
2. Preview writes cannot collide with production namespaced writes.
3. Production writes cannot collide with preview namespaced writes.
4. Legacy existing refs remain readable without migration.
5. Destructive deletion now requires deterministic current-environment ownership.
6. Legacy unowned keys are **read-compatible but delete-protected**.
7. Explicit-key writes now refuse unsafe overwrite of existing legacy/unowned objects.
8. No bulk object move/delete/migration was introduced.

## 3) Implemented storage change summary

### Added shared ownership authority

File: `backend/lib/storage_ownership.py`

Introduced a small shared authority for:

- normalized environment identity,
- environment-aware key construction,
- deterministic ownership parsing,
- current-environment delete eligibility,
- safe reference construction.

### Code changes applied

- `backend/photo_storage.py`
  - new photo writes now use `photos/{env}/...`
  - new document/attachment writes now use `documents/{env}/...`
  - explicit-key uploads now block unsafe overwrite of existing legacy/unowned keys
  - deletes now refuse legacy or cross-environment object destruction
- `backend/safety_doc_storage.py`
  - new writes now use `safety-docs/{env}/...`
  - explicit-key uploads now block unsafe overwrite of existing legacy/unowned keys
  - deletes now refuse legacy or cross-environment object destruction
- `backend/promo_assets_storage.py`
  - new writes now use `promo-assets/{env}/...`
  - deletes now refuse legacy or cross-environment object destruction
- `backend/routes/operational_attachments.py`
  - now rebuilds refs through canonical storage helper
- `backend/routes/asset_documents.py`
  - now rebuilds refs through canonical storage helper

## 4) Verification evidence captured in this batch

### Focused unit/regression

- `python -m pytest /app/backend/tests/test_prec10_r2_environment_isolation.py /app/backend/tests/test_iter429_op_attachments_r2.py /app/backend/tests/test_iter64_photo_storage.py -q`
- Result: `25 passed`

### Live preview runtime proof

Verified against preview runtime + preview Mongo:

1. Safety Documents
   - uploaded a new document
   - persisted `file_data` as `doc://.../safety-docs/preview/...`
   - downloaded identical bytes
   - deleted record successfully
2. Operational Attachments
   - uploaded a new attachment
   - persisted `r2_key` under `photos/preview/...`
   - fetched identical bytes
   - deleted record successfully
3. Promo Assets
   - uploaded a new promo asset
   - persisted `file_key` under `promo-assets/preview/...`
   - detail/read path returned a playable presigned URL
   - deleted record successfully

## 5) Bounded provenance retrospective classification

| Reviewed work item | Classification | Reopen? | Reason |
|---|---|---:|---|
| Public/internal data-leak lock-down on `/api/jobs`, `/api/equipment-master`, `/api/employees` | VALID APPLICATION REPAIR | No | Security/auth boundary correction independent of preview business data interpretation |
| Logout/session/access-boundary repairs | VALID APPLICATION REPAIR | No | Auth/session correctness issue, not business-truth interpretation |
| KPI metadata/consumer parity repairs | VALID APPLICATION REPAIR | No | Consumer-lineage and help metadata correctness; does not force KPI values to zero |
| PM Project Detail / Executive UI crash fixes | VALID APPLICATION REPAIR | No | UI/runtime defect only |
| Admin OS false-red OCC evaluator repairs | VALID APPLICATION REPAIR | No | Technical status-evaluation correctness; did not rewrite business facts |
| AI gateway availability resolution | VALID APPLICATION REPAIR | No | Integration-status truth repair; unrelated to preview data provenance |
| Governance synthetic/certification exclusion tightening | VALID PREVIEW/CERTIFICATION REPAIR | No | Properly distinguishes fixture/certification rows from operator/business truth in preview |
| Daily-report employee-link deterministic backfill path + placeholder guard | VALID PREVIEW/CERTIFICATION REPAIR | No | Preview-only deterministic data hygiene path; not a production-truth claim and no incorrect code logic found |
| Recovery 4 GiB bounded archive ceiling increase | VALID APPLICATION REPAIR | No | Resource-bound reliability change; unrelated to preview business truth |
| Cross-environment R2 namespace isolation | INCORRECT SANDBOX-DRIVEN ARCHITECTURE GAP | Yes — fixed in this batch | Preview and production shared object-key namespace remained unsafe; smallest safe environment-aware repair now applied |

## 6) Retrospective conclusion

- Reviewed items requiring reopen due to provenance misunderstanding: **1**
- That item was the shared-bucket namespace/ownership gap, and it is repaired in code in this batch.
- Additional previously closed PRE-C10 rows were **not** reopened because no concrete evidence showed that provenance misunderstanding produced an incorrect implementation.

### Explicit bounded-review counts

- **VALID APPLICATION REPAIRS = 7**
- **VALID PREVIEW/CERTIFICATION REPAIRS = 2**
- **QUESTIONABLE SANDBOX-DRIVEN LOGIC CHANGES = 0**
- **INCORRECT SANDBOX-DRIVEN LOGIC CHANGES = 1**

### Explicit defect disposition

- Confirmed preview ↔ production shared object-namespace defect: **CLOSED — FIXED IN CODE AND VERIFIED**
- Legacy reads remain supported.
- Existing production references were not bulk-migrated or broken.
- New preview writes/deletes/overwrites are prevented from affecting production-owned objects.
- No additional questionable sandbox-driven logic changes were found, so previously certified work is **not reopened** on provenance grounds.

## 7) Remaining governed follow-up after this batch

1. Continue KPI closure against authoritative tested-environment truth chains.
2. Continue Admin OS / C1-C9 / Public-Device / Coaching / Owner / Recurrence rows unaffected by storage changes.
3. Keep disputed preview governance/business-looking records frozen unless a later issue proves a concrete application or certification need.
4. Re-certify affected storage/admin/runtime rows inside the PRE-C10 denominator as the broader closure program continues.