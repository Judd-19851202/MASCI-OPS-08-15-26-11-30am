# RFI Backup & Retention Model
## Phase V.0 · Architecture & Governance · 2026-05-27

> Legal-defensibility spine for every RFI record. Mongo + R2 split.
> Append-only audit. No casual delete. Doctrine-locked.

---

## 1 · Two-Layer Storage Doctrine

| Layer | Responsibility |
|---|---|
| **Mongo (Atlas · `masci_safety` / `masci_safety_preview`)** | Live operational state · indexes · search · audit trail · revision metadata · constraint links · permission tokens. |
| **Cloudflare R2 (`masci-attachments`)** | Immutable artifacts: PDFs · attachments · photos · `.xer` files · dispute packages · revision snapshots. |

The split mirrors existing platform doctrine (R2 already houses daily
report photos, safety attachments, safety documents). RFI does **not**
introduce a new storage tier. It inherits the proven one.

---

## 2 · What Lives Where

### 2.1 — Mongo collections (NEW for RFI)

| Collection | Purpose |
|---|---|
| `rfis` | One row per RFI (current state) |
| `rfi_revisions` | One row per submitted revision (immutable history) |
| `rfi_audit` | Append-only state-transition + access trail |
| `rfi_external_tokens` | Tokenized external access envelopes |
| `rfi_external_audit` | Append-only external action trail |
| `rfi_distributions` | Multi-recipient routing groups |
| `rfi_constraints` *(shared with schedule subsystem)* | Constraint records (see SCHEDULE_CONSTRAINT_MODEL) |

### 2.2 — R2 keys

```
rfi/
  {project_number}/
    {rfi_id}/
      rev-001/
        body.pdf
        attachments/<file_id>.<ext>
        photos/<file_id>.jpg
      rev-002/
        body.pdf
        ...
      audit/
        external_<token_id>_<ts>.json   # immutable copies of audit events
      response_pdfs/
        from_cei_<ts>.pdf
        from_engineer_<ts>.pdf
```

**Every PDF and every attachment is content-addressable.** Once written,
it is never modified. Revisions create new keys. Old keys remain.

---

## 3 · Retention Schedule

| Object | Live retention | Cold retention | Hard delete |
|---|---|---|---|
| `rfis` (current state) | indefinite while project active | 7 years after project closeout | **never automatic** |
| `rfi_revisions` | indefinite | 7 years after project closeout | **never automatic** |
| `rfi_audit` | indefinite | 7 years after project closeout | **never automatic** |
| `rfi_external_tokens` (revoked / expired) | 90 days | 7 years (anonymized) | **never automatic** |
| `rfi_external_audit` | indefinite | 7 years | **never automatic** |
| PDFs / attachments / photos (R2) | indefinite while project active | 7 years (lifecycle-managed) | **never automatic** |

7 years is the federal-contract baseline for DOT / FAA disputes and
closeout audits. It is intentionally conservative — storage is cheap
compared to discovery cost.

---

## 4 · Delete Doctrine

- **Hard delete:** prohibited platform-wide for RFI records.
- **Void:** the only "removal" operation. Preserves the snapshot,
  carries a `void_reason`, requires dual control (PM + Admin), enters
  the audit trail.
- **Project closeout:** moves RFI records into a `closed_archive` view
  but does not delete. PMs and Admins can still read them. Executive
  read remains.

---

## 5 · Backup Discipline

The RFI subsystem **inherits the existing platform backup pipeline**:

- Nightly Mongo backups via `scheduler` → `backup_health` collection
  (already monitored by `/api/health/full`).
- R2 lifecycle rules already in place for `masci-attachments`.
- Restore drills (`/app/scripts/restore_drill.py`) MUST be extended to
  cover the new RFI collections during V.1.

No new backup infrastructure. No new cron. No new alert channel.

---

## 6 · Dispute Package Doctrine

When a dispute arises (claim, audit request, change-order
negotiation), PM can request a **Dispute Package** for a project or a
specific RFI. The package is a single ZIP written to R2 containing:

- All RFI revisions (PDFs).
- All response PDFs.
- All audit-trail entries (JSON · pretty-printed).
- All external-token audit entries.
- All linked daily-report rows (CSV).
- All linked constraint rows (CSV).
- All photos and attachments referenced.
- A `MANIFEST.md` that lists everything with sha256 hashes.

Dispute packages are **immutable** once generated. New disputes generate
new packages. Old packages stay.

This is the legal-defensibility deliverable. Build it once, use it for
every claim.

---

## 7 · Field-Recovery Doctrine

If a draft RFI is lost (phone offline, browser crash, app close):

- Drafts auto-save to Mongo every 30 seconds while editing.
- The PM/Superintendent's "Resume Draft" link surfaces unsaved drafts
  on the next session.
- No draft is lost without an explicit user-initiated discard.

Drafts older than 30 days with no activity are flagged but **not
deleted automatically**. Superintendent receives a single in-app
prompt: *"Draft from <date> · still relevant?"* Their answer is
audited.

---

## 8 · GDPR / PII Discipline

External recipient emails and IPs are stored in audit trails. We
intentionally retain them — they are part of the legal record. PII
minimization rules apply to **operational displays only**: external
recipient lists in the UI show name + role + masked email; the
audit-trail export shows full email + IP.

If a recipient requests PII export, Admin can produce a per-email
extract from `rfi_external_audit`.

---

## 9 · Implementation Note (V.1 / V.2)

The retention rules above are **doctrine**. The mechanical
implementation lands in V.1:

- Mongo collections created with appropriate indexes (`rfi_id`,
  `project_number`, `state`, `submitted_at`, `response_due_at`).
- R2 key prefix `rfi/` reserved.
- `restore_drill.py` extended to include `rfis`, `rfi_revisions`,
  `rfi_audit`, `rfi_external_tokens`, `rfi_external_audit`.
- Dispute package generator lands in V.2 (after first real RFIs
  exist).

---

## 10 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Storage layout locks during V.1.
