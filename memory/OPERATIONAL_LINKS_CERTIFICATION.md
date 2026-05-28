# Operational Links — Certification

**Phase V-Prelude · Wave 1 · Substrate**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Doctrine reference

- `/app/memory/OPERATIONAL_LINKING_RULES.md` (§1–§11)

## Files

| File | Purpose |
|---|---|
| `backend/routes/operational_links.py` | API surface + Pydantic models + closed-enum gates |
| `frontend/src/lib/operationalApi.js` | `listLinks` / `createLink` / `archiveLink` / `voidLink` |
| `scripts/operational_links_doctrine_probe.py` | Static + runtime doctrine probe |
| `backend/tests/test_v_prelude_wave1_substrate.py` | 19 regression tests (link probes inline) |

## API surface

```
POST   /api/operational-links
GET    /api/operational-links?project_id=...&[source_type=...]&[target_type=...]&...
GET    /api/operational-links/:id
PATCH  /api/operational-links/:id/status         { status, reason? }   # admin-only
```

**No DELETE endpoint exists.** Hard deletion is forbidden by doctrine §10.
Status flips (active · archived · voided · superseded) are the ONLY
mutation pathway.

## §10 governance probes — all 10 verified

| # | Probe | Test |
|---|---|---|
| 1 | 11 audit fields complete on every row | `test_link_audit_metadata_completeness` |
| 2 | source_type/target_type ∈ closed enum | `test_link_invalid_artifact_type_rejected` |
| 3 | relationship ∈ canonical set (no inverse stored) | `test_link_forbidden_inverse_rejected` |
| 4 | no self-link | `test_link_self_link_rejected` |
| 5 | no circular `resulted_in` | `test_link_circular_resulted_in_rejected` |
| 6 | hard DELETE forbidden | `test_link_no_hard_delete_only_status` |
| 7 | status transition matrix enforced | `test_link_supersedes_cascades_and_terminal_blocked` |
| 8 | link create does NOT mutate target | `test_link_create_does_not_mutate_target` |
| 9 | project_id scope filter honoured | `test_link_project_scope_filter` |
| 10 | unauthenticated → 401 | `test_operational_links_endpoint_requires_token` |

## Closed enums (sourced from `routes/operational_links.py`)

- **ARTIFACT_TYPES** — 21 members covering current + V-Prelude future
  (daily_report, incident, inspection, photo, attachment, field_note,
  operational_constraint, future_rfi, future_schedule_activity,
  future_schedule_import, future_external_response, safety_record,
  dispatch_event, equipment_record, employee_record, project, job,
  meeting, qa_qc_record, trench_record, jha_record).
- **CANONICAL_RELATIONSHIPS** — 14 members
  (references, caused_by, blocks, supports, evidence_for, resulted_in,
  related_to, supersedes, resolved_by, escalated_from, impacts,
  documents, response_to, generated_from).
- **FORBIDDEN_INVERSE_RELATIONSHIPS** — 3 members rejected at write time
  (blocked_by, impacted_by, escalated_to).
- **VISIBILITY_SCOPES** — 8 members (internal, pm-scope, safety-scope,
  dispatch-scope, hr-scope, cross-portal-read, external-shared,
  audit-only).
- **STATUS_VALUES** — 4 members (active, archived, voided, superseded).

## Status transition matrix

```
active     → archived · voided · superseded
archived   → active                              # reopen
voided     → active                              # admin attestation
superseded → ∅                                   # TERMINAL
```

Enforced via `ALLOWED_STATUS_TRANSITIONS` in `operational_links.py`.

## supersedes cascade

`POST /api/operational-links` with `relationship="supersedes"` is the
**only** write that mutates other rows: every existing **active** link
whose `source_type/source_id` matches the new target is flipped to
`status="superseded"` and stamped with `status_changed_at` +
`status_changed_by`. This is the explicit doctrine §3 carve-out.

## Doctrine probe (sub-second)

`scripts/operational_links_doctrine_probe.py --gate`
- Imports the doctrine enums from the module (no enum drift).
- Sweeps live preview Mongo `operational_links` (≤5000 rows).
- Hard-fails on: missing audit field · invalid enum value · forbidden
  inverse stored · self-link · circular resulted_in · archived/voided/
  superseded row missing `status_changed_at`.
- Wired into `scripts/pre_deploy_check.sh` as a blocking stage.
- Current scan: **0 violations · 0 rows (substrate clean on preview)**.

— certified by E1 · 2026-05-28
