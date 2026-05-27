# Schedule Backup & Retention Model
## Phase V.0 · Architecture & Governance · 2026-05-27

> Two-layer storage, immutable revisions, content-addressable raw
> uploads. Doctrine-locked.

---

## 1 · Two-Layer Storage

| Layer | Holds |
|---|---|
| Mongo | Parsed schedule data, revision metadata, activity / relationship / milestone / calendar rows, constraint links, audit trails, validation reports. |
| R2 | Raw `.xer` / XML uploads (immutable, content-addressable), generated lookahead PDFs, generated critical-path PDFs. |

Same split as RFI. Same R2 bucket (`masci-attachments`). Same Mongo
cluster. No new infrastructure.

---

## 2 · Mongo Collections (recap from `P6_IMPORT_ARCHITECTURE.md`)

| Collection | Purpose | Indexes |
|---|---|---|
| `schedule_imports` | Every upload (raw + validation result) | `project_number+uploaded_at` |
| `schedules` | Current active schedule per project | `project_number+active` (unique-on-active) |
| `schedule_revisions` | One row per accepted revision | `project_number+revision_number` |
| `schedule_activities` | Activities per revision | `revision_id+task_id` · `revision_id+critical` · `revision_id+late_start_date` |
| `schedule_relationships` | P6 logical edges | `revision_id+from_task` · `revision_id+to_task` |
| `schedule_milestones` | Milestones | `revision_id+task_id` |
| `schedule_calendars` | Calendars | `revision_id+calendar_id` |
| `schedule_constraints_native` | P6 native constraints | `revision_id+task_id` |
| `schedule_audit` | Append-only audit | `project_number+occurred_at` |

---

## 3 · Retention Schedule

| Object | Live retention | Cold retention | Hard delete |
|---|---|---|---|
| Raw `.xer` / XML in R2 | indefinite | 7 years after project closeout | **never automatic** |
| `schedule_imports` (every upload) | indefinite | 7 years | **never automatic** |
| `schedules` (active) | always present while project active | rolled to revision archive at closeout | **never automatic** |
| `schedule_revisions` (each accepted revision) | indefinite | 7 years | **never automatic** |
| `schedule_activities` and child collections per revision | indefinite | 7 years | **never automatic** |
| Rejected uploads (raw file + validation report) | 90 days minimum · indefinite by default | 7 years (audit) | **never automatic** |
| Generated lookahead / CP PDFs | indefinite | 7 years | **never automatic** |
| `schedule_audit` | indefinite | 7 years | **never automatic** |

7 years matches the RFI retention window — claim cycles can extend
years past closeout, especially on federal contracts.

---

## 4 · Immutability Contract

- A raw upload, once persisted, is **never** mutated. New uploads
  produce new sha256 keys.
- A revision, once accepted, is **never** edited. Errors are corrected
  by a new revision.
- A rejected upload is preserved in R2 even though it never became
  active.
- Validation reports are append-only history on `schedule_imports`.
- An audit-trail entry is append-only.

Anything that mutates an accepted revision's parsed data is **rejected
by doctrine**.

---

## 5 · Backups

The Schedule subsystem inherits the existing Mongo backup pipeline.
The new collections (§ 2) are added to:

- The nightly backup set.
- The R2 backup integrity check (raw files verified by sha256 against
  Mongo metadata).
- The restore-drill script (`/app/scripts/restore_drill.py`).

No new cron. No new alert channel. No new dashboard.

---

## 6 · Dispute Package Extension

The RFI Dispute Package (`RFI_BACKUP_RETENTION_MODEL §6`) is extended
in V.6 to include schedule artifacts when an RFI has linked
constraints touching the schedule:

```
DisputePackage/{project}/{generated_ts}/
  rfi/                              # existing RFI bundle
  schedule/
    active_revision_at_submission/
      activities.csv
      relationships.csv
      milestones.csv
      lookahead.pdf
      critical_path.pdf
    revision_history.csv
    activity_history_for_linked_tasks/
      <task_id>.json                # every revision's state for these activities
    raw_xer_at_submission.xer       # the .xer that was active when the RFI was submitted
  constraints/                      # linked constraints with full audit
  MANIFEST.md                       # sha256 inventory
```

This is **the** claim-defense artifact: every linked schedule
activity's lineage from the moment the RFI was raised through every
subsequent schedule revision.

---

## 7 · Active-Revision Atomicity

Activating a new revision happens inside a single Mongo transaction:

```python
async with db.client.start_session() as s:
    async with s.start_transaction():
        await db.schedules.update_one(
            {"project_number": pn, "active": True},
            {"$set": {"active": False, "deactivated_at": now, "superseded_by": new_id}},
            session=s,
        )
        await db.schedules.update_one(
            {"_id": new_id},
            {"$set": {"active": True, "activated_at": now}},
            session=s,
        )
        await db.schedule_audit.insert_one(
            {"project_number": pn, "kind": "activation", "actor": ..., "from": prior_id, "to": new_id},
            session=s,
        )
```

If the transaction fails, the active revision remains the prior one.
No half-states.

---

## 8 · Index Rebinding on Activation

When a new revision activates, the system performs a **rebind pass**:

1. Iterate every `rfi_constraints` row whose linked activity task_ids
   reference the prior revision.
2. For each, look up the matching task_id in the new revision.
3. If found → update the constraint's `revision_id` reference.
4. If not found → flag the constraint as `link_orphaned` and surface
   it in the operational-impact view.

This rebind pass is performed asynchronously after activation. It is
itself audited (`schedule_audit.kind=rebind`).

---

## 9 · GDPR / PII

Schedule data contains no PII by design. `.xer` files store activity
names, dates, codes — not people. The only PII in the subsystem is:

- `created_by` / `last_updated_by` user references on `schedule_imports`.
- `actor` references in `schedule_audit`.

Both are internal-only. External tokenized schedule access (V.6+)
masks these.

---

## 10 · Performance Envelope

- Backup window: nightly · existing schedule unchanged.
- Restore drill: must include schedule collections within the current
  drill's time budget. If drill time grows past 15 minutes, add
  per-collection sub-drills.
- R2 lifecycle: no new rules needed. The existing lifecycle policy
  covers the new `schedules/` prefix.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Storage layout lands in V.3 (schedule shell). Backup extension lands in V.4 (P6 import MVP).
