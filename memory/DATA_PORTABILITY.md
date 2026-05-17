# MASCI Operations Platform — Data Portability

> Plain-English guide to MASCI Hub backups, what you own, and how to get
> your data out — without a developer.
>
> Last updated: 2026-02-XX · Status: **ACTIVE — Stages A and B complete (CLI).**
> Stage B.1 (Owner Snapshot PDF) and Stage C (Admin UI) are NOT live yet.

---

## 1. The short version

| Question | Answer |
|---|---|
| Does MASCI own its data? | **Yes — completely.** All daily reports, JHAs, inspections, incidents, HR records, equipment records, photos, and audit logs belong to MASCI and are exportable in standard formats. |
| Is data locked into MASCI Hub? | **No.** Every record is portable as JSON, CSV/Excel, and (Stage B) PDF. Every photo is a real JPG/PNG file. |
| Can MASCI leave the platform and take everything with them? | **Yes.** A nightly backup zip + the human-readable exporter (`scripts/export_human_readable.py`) produce an archive any non-technical person can open and use. |
| Do they need a developer? | **No** for browsing photos, opening CSVs in Excel, and reading JSON-as-text. **Yes (today)** if they want every record converted into the *exact printable PDF* — that's coming in Stage B. |

---

## 2. What's inside a MASCI complete backup (technical layer)

Every nightly backup is a single self-contained zip stored in Cloudflare R2 at
`backups/auto-90d/MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip` (since
2026-02 — older backups under `backups/MASCI_complete_backup_*.zip`).

Inside the zip:

```
MASCI_complete_backup_2026-02-15_030000Z.zip
├── MANIFEST.json                   ← inventory (timestamps, record counts)
├── photos/
│   └── photos/2026/05/<source-id>/<uuid>.jpg     (real JPG/PNG bytes)
│   └── photos/2026/05/<source-id>/<uuid>.png
│   …
├── daily_reports/json/<id>.json    (one JSON file per record)
├── jhas/json/<id>.json
├── inspections/json/<id>.json
├── incidents/json/<id>.json
├── meetings/json/<id>.json
├── equipment-inspections/json/<id>.json
└── … (every Mongo collection, _id stripped)
```

**This is the technical layer.** It exists for restore, audit, and legal
discovery. It is intentionally lossless and developer-readable.

**Restore from this zip is documented in:** `/app/memory/RESTORE_DRILL.md`

---

## 3. What's stored in what format

| Record type | Today's format | Human-readable today? |
|---|---|---|
| Photos (daily report photos, incident photos, fire-ext inspections, etc.) | Real JPG/PNG files under `photos/` | ✅ **Yes — just unzip.** |
| Daily reports | JSON, one file per report | ⚠️ Text-readable, but not the printable form. CSV available in human-readable export. PDF coming in Stage B. |
| Safety inspections / audits | JSON | ⚠️ Same as above. |
| Job Hazard Analyses (JHAs) | JSON | ⚠️ Same as above. |
| Incidents / near-misses | JSON | ⚠️ Same as above. |
| Toolbox talks / safety meetings | JSON | ⚠️ Same as above. |
| Equipment inspections | JSON | ⚠️ Same as above. |
| Equipment master & assignments | JSON | ⚠️ CSV-friendly fields → Excel works fine. |
| HR records (write-ups, coaching, recognition, terminations) | JSON | ⚠️ Same as above. Sensitive fields redacted in human-readable export. |
| Asset transfers / dispatch holds | JSON | ⚠️ CSV-friendly. |
| Training records / certifications | JSON | ⚠️ CSV-friendly. |
| Audit log | JSON | ⚠️ CSV-friendly. |
| User directory (managed + mirrored) | JSON | ⚠️ CSV-friendly, password hashes redacted. |
| Configuration / role templates | JSON | ⚠️ Same as above. |
| User credentials / password hashes | JSON in technical backup ONLY | 🔒 **Not exported in human-readable layer** (security). |

---

## 4. The human-readable export (this Phase 2 build)

`/app/scripts/export_human_readable.py` takes a technical backup zip (or
the equivalent extracted folder) and produces a **second archive** designed
for non-technical browsing:

```
MASCI_HUMAN_READABLE_EXPORT_2026-02-15_120000Z.zip
├── README_START_HERE.txt              ← read this first
├── MANIFEST.json                      ← what's inside, counts, timestamps
├── EXPORT_INDEX.csv                   ← every record ever exported, one row each
├── DATA_DICTIONARY.csv                ← what each field means
├── PHOTOS_AND_ATTACHMENTS/
│   ├── Daily_Reports/<date>/<uuid>.jpg
│   ├── Safety_Incidents/<date>/<uuid>.jpg
│   ├── Fire_Extinguishers/<date>/<uuid>.jpg
│   ├── Equipment/<unit>/<date>/<uuid>.jpg
│   ├── HR/<record>/<uuid>.jpg
│   └── ORPHANED_FILES/                ← photos with no record association
│       └── INDEX.csv
├── DAILY_REPORTS/
│   ├── By_Date/2026-02-15/<DR-id>__<project>__<superintendent>.json
│   ├── By_Project/<project>/<DR-id>__<date>.json
│   └── CSV/daily_reports.csv
├── SAFETY/
│   ├── Incidents/<date>/<id>.json
│   ├── JHAs/<project>/<id>.json
│   ├── Inspections/<date>/<id>.json
│   ├── Meetings/<date>/<id>.json
│   ├── Fire_Extinguishers/<unit>/<id>.json
│   ├── Safety_Training/<id>.json
│   └── CSV/<one CSV per collection>
├── HR/
│   ├── Field_Leadership_Records/<id>.json  (write-ups, coaching, eval, etc.)
│   ├── Employee_Directory/<id>.json        (PII-redacted)
│   ├── Payroll_Variance/<id>.json
│   └── CSV/<one CSV per collection>
├── EQUIPMENT/
│   ├── Equipment_Master/<unit>.json
│   ├── Equipment_Inspections/<date>/<id>.json
│   ├── Asset_Assignments/<id>.json
│   └── CSV/<one CSV per collection>
├── DISPATCH/
│   ├── Asset_Transfers/<id>.json
│   ├── Asset_Holds/<id>.json
│   ├── Transfer_Requests/<id>.json
│   └── CSV/<one CSV per collection>
├── TRAINING/
│   ├── Training_Records/<id>.json
│   ├── Training_Videos/<id>.json
│   └── CSV/<one CSV per collection>
├── ADMIN_AUDIT/
│   ├── Audit_Log/<date>/<id>.json
│   ├── User_Directory/<id>.json            (PII/credentials redacted)
│   ├── Role_Templates/<id>.json
│   └── CSV/<one CSV per collection>
├── PROJECTS/
│   ├── Projects/<id>.json
│   ├── Jobs_Master/<id>.json
│   └── CSV/<one CSV per collection>
├── RAW_JSON/
│   └── <every original JSON record, unchanged>     ← for technical recovery
└── SYSTEM/
    ├── Backup_Info.txt
    ├── Export_Log.txt
    ├── Export_Errors.csv
    └── Verification_Report.txt
```

### What's portable today (Stage A + Stage B)

✅ Photos and attachments grouped by record type, with an orphan bucket
✅ CSV per collection — opens cleanly in Excel / Google Sheets / Power BI
✅ JSON per record, organized by date / project / unit (whichever is most useful)
✅ **Per-record PDF — hybrid strategy** (Stage B):
   - **Bespoke platform layouts** for Daily Reports, Equipment Inspections, and QA/QC Inspections. These use the exact templates the live "Download PDF" buttons use, so the export PDFs are byte-equivalent to what the platform prints from the UI today.
   - **Generic platform layout** (same `pdf_render.render_record_pdf` path the UI uses, generic body) for Safety Inspections, Safety Meetings, JHAs, and Incidents. They share the platform's letterhead, footer, and styling, but are field-table layouts rather than form-faithful reproductions. **Wording note:** these are NOT bespoke per-form recreations; they are the same generic layout the live UI's Download PDF currently produces for these record types.
   - **Field Leadership records** (write-ups, coaching, recognition, terminations, equipment checkout/return, employee evaluations, payroll adjustments, etc.) use a dedicated `field_leadership_pdf.render_field_leadership_pdf` renderer.
   - **Standardized fallback PDF** for every other record type (fire extinguishers, asset transfers, training records, audit logs, projects, jobs, role templates, etc.) — clean two-column field table with MASCI / Powered by ForgedOps™ branding. This is a generic record card, not a form-faithful reproduction.
✅ Photos resolved offline — `photo://` references inside records are pre-resolved to local data: URLs from the extracted backup, so PDFs render correctly even without R2 access.
✅ Defensive timeout — pathological legacy records (pre-iter64 with multi-MB embedded base64 photos) that hang the renderer are capped at 20 seconds and fall through to the standardized layout. NEVER crashes the export.
✅ Master index (`EXPORT_INDEX.csv`) — every record in the archive with title, date, project, JSON path, **PDF path**, and photo paths
✅ Data dictionary — what each field means
✅ Raw JSON preserved for technical recovery (`RAW_JSON/`)
✅ Verification report — counts (records, photos, PDFs by strategy, failures), errors, warnings, source backup hash
✅ Bad records skipped gracefully (logged, never crash the whole export)
✅ Sensitive fields (passwords, secrets, API keys, tokens) redacted in module folders; preserved in RAW_JSON for IT only

### What's coming next (Stage B.1)

⏳ Owner Snapshot PDF — a single ~10-page "company-at-a-glance" summary
   at the root of the archive (active employees, projects, last 30 days
   of incidents, last 90 days of training compliance, equipment fleet
   roster, audit-log highlights). Built after core Stage B PDFs are
   verified in production use.

### What's coming after that (Stage C)

⏳ Admin UI button: **Admin → Data Portability → Export Human-Readable
   Archive**. Audit-logged, admin-only, expiring download link, optional
   date-range / module scope, async generation, status polling.

---

## 5. How to extract a downloaded backup

### From a Cloudflare R2 download

1. Download the backup zip from R2 (Cloudflare dashboard → `masci-hub` bucket → `backups/auto-90d/` → newest)
2. Save it to your computer
3. **For technical browsing**: just double-click → see structure in §2 above
4. **For human-readable browsing**: feed it to the exporter

### Running the human-readable exporter

```bash
# From the platform repo
python3 /app/scripts/export_human_readable.py \
    --backup /path/to/MASCI_complete_backup_2026-02-15_030000Z.zip \
    --out /path/to/output/folder
```

The exporter:
- Reads the backup zip (never modifies it)
- Produces `MASCI_HUMAN_READABLE_EXPORT_<timestamp>.zip` in the output folder
- Prints a summary on completion (records exported, photos copied, errors)

**Optional flags:**
- `--company-name "MASCI"` — name in archive filename (or env `EXPORT_COMPANY_NAME`)
- `--modules SAFETY,HR` — limit to specific business modules (default: all)
- `--no-zip` — leave the output as a folder instead of zipping it
- `--dry-run` — count records, generate report, write nothing
- `--from-source-folder <path>` — use an already-extracted backup folder
  instead of a zip (useful for very large archives)

---

## 6. How to use the human-readable archive

1. **Start here:** open `README_START_HERE.txt` in any text editor (Notepad, TextEdit, VS Code, etc.)
2. **Find a specific record**: search `EXPORT_INDEX.csv` in Excel — every record in the archive is one row with title, date, project, employee, and file paths
3. **Browse by category**: open the folder for the module you want (DAILY_REPORTS, SAFETY, HR, EQUIPMENT, DISPATCH, TRAINING, ADMIN_AUDIT, PROJECTS)
4. **Open in Excel**: every `CSV/` subfolder contains spreadsheets for that module — drop into Excel/Sheets/Power BI/Tableau
5. **Photos**: open `PHOTOS_AND_ATTACHMENTS/<category>/` — all photos are real JPG/PNG files, organized by record
6. **Audit / lawyer / compliance**: hand them the entire zip. `EXPORT_INDEX.csv` + `Verification_Report.txt` are the headline artifacts.
7. **Technical recovery**: developers/IT should look at `RAW_JSON/` and `MANIFEST.json` — these mirror the technical-layer backup format.

---

## 7. What MASCI owns vs. what the platform provides

| | MASCI owns | ForgedOps platform provides |
|---|---|---|
| All operational records (daily reports, JHAs, incidents, etc.) | ✅ | Storage, retrieval, search, PDF render |
| All photos and attachments | ✅ | Object-storage hosting (R2) |
| All HR / safety / training records | ✅ | Workflow, audit log, role-based access |
| All audit logs | ✅ | Capture, persistence |
| User identities (employee names, emails, roles) | ✅ | Authentication, RBAC enforcement |
| Password hashes / API keys / OAuth secrets | ❌ MASCI's own credentials (used to access third-party services) belong to MASCI; the platform's own internal session tokens are platform infrastructure | Session-token generation, password hashing |

**Cleanly stated:** the platform is a tool MASCI rents to operate on data
MASCI owns. There is no proprietary lock-in on the data layer.

---

## 8. What MASCI cannot get out

| Item | Reason | Mitigation |
|---|---|---|
| Other tenants' data (future SaaS) | Multi-tenant isolation | Won't matter for MASCI; SaaS customers get only their own tenant's data |
| Live session tokens | Ephemeral, regenerated per login | Not data — auth artifact |
| Internal platform code | Property of the platform vendor (ForgedOps) | MASCI owns the data, not the code |
| Anything older than the R2 lifecycle window | After Stage 2 Round 2 hardening, new backups auto-expire after 90 days (see `R2_RETENTION_AUDIT.md`) | Legacy backups under `backups/*.zip` are NOT subject to the 90-day rule — they remain until manually deleted with explicit approval |

---

## 9. Sensitive-data handling in the human-readable export

The exporter automatically redacts the following fields in any record
written under module folders (the technical `RAW_JSON/` mirror is
unchanged — developers/IT only):

- `password`, `password_hash`, `hash`, `secret`, `api_key`, `token`, `bearer`
- Any field whose name contains `password` / `secret` / `token` / `api_key`

If MASCI ever needs the original unredacted form, it lives in `RAW_JSON/`
and the original technical backup. The human-readable folders are intended
to be safe to share with a non-technical operator or auditor.

Collections excluded from human-readable folders entirely (still in `RAW_JSON/`):

- `admin_users`, `hr_users`, `shop_users`, `dispatch_users`, `project_managers`, `users` (credential collections)
- `signatures` (raw image blobs, no meaningful CSV form)
- `job_photo_thumb_cache` (binary cache, not source-of-truth)
- `system_counters`, `notifications` (operational ephemera)

---

## 10. Current limitations

- **Per-record PDFs in the export are hybrid, not uniformly form-faithful.** Bespoke layouts exist for Daily Reports, Equipment Inspections, QA/QC Inspections, and Field Leadership records. Safety Inspections / Safety Meetings / JHAs / Incidents currently route through the platform's generic layout (same one the live UI uses for those record types' Download PDF). Everything else uses the standardized fallback. The export is honest about which is which in `Verification_Report.txt`.
- **Photo→record association is best-effort.** The current convention is `photos/<YYYY>/<MM>/<source-id>/<uuid>.<ext>` — the `<source-id>` is matched back to a record id. Photos that don't match a known record go to `PHOTOS_AND_ATTACHMENTS/ORPHANED_FILES/`.
- **No Admin UI yet** (Stage C). The exporter is CLI-only today; run it from the repo. The eventual UI will let an admin trigger this without shell access.
- **No Owner Snapshot PDF yet** (Stage B.1). The high-level "company-at-a-glance" summary is not generated today.
- **Module classifier is hand-maintained.** New collections added to the platform will land in an "OTHER" bucket until explicitly mapped. The exporter logs unmapped collections in `Verification_Report.txt` so we know to update the map.
- **R2 lifecycle is not yet active.** Backups are written to the lifecycle-scoped `backups/auto-90d/` prefix, but the 90-day expiration rule has NOT been applied to the bucket (pending operator R2 token rotation — see `R2_RETENTION_AUDIT.md`). Until that rule is applied, no backup expires automatically.

---

## 11. Roadmap

| Stage | Status | Description |
|---|---|---|
| A — Foundation | ✅ Done | Doc + CSV per module + photo extraction + index + verification report + tests + storage-target-neutral exporter |
| B — PDF rendering | ✅ Done (CLI, hybrid strategy) | Per-record PDFs · bespoke layouts for daily reports / equipment inspections / QA/QC / field leadership · generic platform layout for inspections / meetings / JHAs / incidents · standardized fallback for everything else · offline photo resolution · 20s per-record render watchdog · failure-tolerant |
| B.1 — Owner Snapshot PDF | ⏳ Next | One ~10-page summary at the archive root: active employees, projects, last 30 days of incidents, last 90 days of training compliance, equipment fleet roster, audit-log highlights |
| C — Admin UI | ⏳ Later | Admin → Data Portability page: button, scope/date selector, async generation, audit log, expiring download link (writes to a tmpdir, reaped after delivery) |
| D — Tenant-aware (SaaS) | Future | `EXPORT_COMPANY_NAME` env hook already in place; will be `{tenant}_HUMAN_READABLE_EXPORT_…` when multi-tenant lands |
| E — MASCI-server delivery | Future | Nightly/weekly export generated from latest R2 backup → pushed to customer-owned archive server → local tmpdir reaped. Exporter unchanged; thin upload wrapper added separately. |
| F — Scheduled exports | Future | Cron / Celery-driven trigger for E |

---

## 12. Storage architecture — where exports live, where they go

This is the explicit architecture for how the two backup layers relate. **R2 stays the disaster-recovery layer. The human-readable layer is for customer access, audit, and offboarding — and is designed to live on the customer's own infrastructure, not in R2.**

### Two-layer model

| Layer | Lives in | Purpose | Retention |
|---|---|---|---|
| **Technical backup** (existing) | Cloudflare R2 (`backups/auto-90d/*.zip` + legacy `backups/*.zip`) | Disaster recovery, restore, audit-of-last-resort | 90 days on `backups/auto-90d/` (future objects only); legacy backups retained indefinitely until manual cleanup |
| **Human-readable export** (this build) | **NOT R2 by default.** Generated on demand, streamed to the customer-owned destination, removed from app storage after delivery. | Customer access, audit / legal / compliance packages, offboarding | Configurable per export (no platform-side persistence by default) |

### Why we don't park human-readable exports in R2

- Per-record PDFs (coming in Stage B) plus rendered CSVs balloon the storage footprint 3–5× the technical zip. R2 lifecycle (90 days) doesn't cleanly express "keep the audit package for the customer, not the platform."
- The customer is the rightful owner of the human-readable export. It belongs in their archive, not the platform vendor's.
- Different retention obligations: technical backups serve disaster recovery (short half-life); audit packages may need 7+ years (legal hold) — wrong tool for the same shelf.

### Delivery targets (architectural placeholders)

The exporter is **storage-target-neutral by design.** It writes the final zip to whatever `--out` directory it's given and exits. It does NOT:

- talk to R2
- read or write any app-internal directory by default
- assume the result will be persisted anywhere

This means the eventual Admin UI can plug in any of these delivery paths without touching the exporter:

| Delivery target | Status | How it integrates |
|---|---|---|
| Operator's local laptop (CLI today) | ✅ Available now | `python3 scripts/export_human_readable.py --backup … --out ~/Downloads/masci_exports` |
| Admin browser download (expiring URL) | ⏳ Stage C | Generate to a tmpdir → upload to short-lived presigned location → email link → reap the tmpdir |
| **Customer-owned MASCI server** (future) | ⏳ Future | Generate to a tmpdir → push over a documented protocol (SFTP / WebDAV / signed POST) to the customer's archive endpoint → reap the tmpdir |
| Customer's S3-compatible archive (future SaaS) | ⏳ Future | Same as above, S3 PUT instead |
| Email attachment | ❌ Never | Audit packages are too large and contain PII; email is the wrong transport |

The exporter takes no opinion on which of these the operator picks. Each Stage C / future delivery integration will be a **thin wrapper** that calls the exporter, then uploads the result, then deletes the staged folder. No exporter redesign needed.

### Temporary-storage rule (current behavior)

When the exporter finishes:

- ✅ **Zip mode (default)**: the staged folder is deleted; only the final `*.zip` remains at `--out`.
- ✅ **`--no-zip`**: the folder is preserved at `--out` (operator chose this explicitly).
- ✅ **`--dry-run`**: only `Verification_Report.txt` is written (no records).

The platform itself **never** auto-persists a human-readable export to R2 or to any app-internal disk on its own. Generated exports exist for as long as the operator's chosen `--out` directory exists. **If the operator doesn't move it to long-term storage, it disappears with the operator's tmpdir** — which is the desired behavior for sensitive HR/safety packages.

### Future architecture target (Phase 3+)

```
                        ┌──────────────────────────┐
   Nightly (existing)   │  Cloudflare R2           │
   ─────────────────►   │  backups/auto-90d/*.zip  │   ← technical, restore-grade,
                        │  90-day lifecycle        │     90-day window
                        └──────────────────────────┘

   Nightly / weekly     ┌──────────────────────────┐
   (future Phase 3+)    │  MASCI-owned server      │
   ─────────────────►   │  human-readable archive  │   ← customer-owned, long-term,
                        │  /archive/YYYY/MM/…      │     PDF/CSV/photos, audit-ready
                        └──────────────────────────┘
```

In that target:

- Nightly: technical backup → R2 (unchanged).
- Nightly or weekly cadence (TBD by operator): generate human-readable export from the latest technical backup → push to customer-owned MASCI server → reap local tmpdir.
- The push step is a **separate, future integration**. The exporter itself does not change.

### What is locked in now to make that future work cleanly

1. ✅ Exporter has no R2 client, no app-internal write paths, no implicit persistence.
2. ✅ `--out` is required (no default to `/app/...`). If nobody tells it where to write, it doesn't write.
3. ✅ Default mode is `zip`. The intermediate folder is cleaned up after zipping.
4. ✅ Source can be a downloaded backup zip OR an already-extracted folder, so the future Phase-3 pipeline can extract once and re-use.
5. ✅ Tenant-aware filename (`{EXPORT_COMPANY_NAME}_HUMAN_READABLE_EXPORT_…`) so multi-tenant doesn't need a rename later.
6. ✅ Verification report includes source SHA-256, so the future delivery wrapper can attach provenance to the upload metadata.

### What is explicitly NOT in this build (per user mandate)

- ❌ MASCI server upload integration — deferred to Phase 3+.
- ❌ Scheduled-export cron — deferred.
- ❌ Persistent human-readable storage in R2 — by design, this is not where these archives belong.
- ❌ Admin UI button — deferred to Stage C (script + doc first, no fake UI).

---

## 13. Audience cheat sheet

| Who | What they need | Where to look |
|---|---|---|
| **MASCI owner / exec** | "Show me what we have" | `README_START_HERE.txt` → `EXPORT_INDEX.csv` |
| **HR manager** | Personnel records, write-ups, terminations | `HR/` folder |
| **Safety manager** | Incidents, JHAs, inspections, training | `SAFETY/` and `TRAINING/` folders |
| **Superintendent** | Daily reports, crew, equipment | `DAILY_REPORTS/` and `EQUIPMENT/` folders |
| **Attorney / compliance / auditor** | Everything, with provenance | Whole zip + `Verification_Report.txt` + `EXPORT_INDEX.csv` |
| **IT / developer** | Restore the platform | `RAW_JSON/` + the technical backup + `RESTORE_DRILL.md` |
| **MASCI offboarding from platform** | Take everything | Run exporter on latest backup → hand over the resulting zip |

---

## 14. The answer to "Can I get all of my data out?"

**Yes — via the CLI exporter today, via an Admin UI once Stage C ships.** The exporter is end-to-end functional and has been verified against a real 168 MB R2 backup, producing a 160+ PDF archive. Stage B.1 (Owner Snapshot PDF) and Stage C (Admin UI button + audited download) are explicitly deferred — see § 11 roadmap.
