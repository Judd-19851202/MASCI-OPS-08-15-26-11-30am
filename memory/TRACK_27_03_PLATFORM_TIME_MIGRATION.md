# TRACK 27.03 · Platform Time Standardization — Migration Ledger

**Status:** Phase 1 shipped. Phase 2 = mechanical grind against this ledger.
**Standard:** `/app/frontend/src/lib/platformTime.js` + `/app/backend/lib/platform_time.py`
**Guard:** `/app/backend/tests/test_track_27_03_zero_utc_guard.py` — fails any listed file that leaks UTC.

---

## Phase 1 — Shipped 2026-02-08

- ✅ `frontend/src/lib/platformTime.js` — canonical formatter (`formatPlatformTime`, `formatPlatformDate`, `formatPlatformTimeOnly`, `formatRelativeTime`, `formatPlatformStamp`, `getPlatformTimezone`).
- ✅ `backend/lib/platform_time.py` — canonical formatter (`localize_timestamp`, `display_timestamp`, `format_platform_date`, `format_platform_time_only`, `format_platform_stamp`, `organization_local_time`, `resolve_tz`).
- ✅ Regression guard: 6/6 tests pass. Scans registered operator-facing files for `utcnow`, `toISOString`, `toUTCString`, `isoformat`, literal " UTC" / " GMT" strings, and raw ISO Z stamps. Fails CI if a listed file regresses.
- ✅ 5 highest-visibility surfaces converted (visible on Admin, HR, Dashboard, Deploy Readiness, AI Health).

### Timezone resolution priority (both frontend + backend)

1. User preference (frontend: `localStorage["masci.tz.user"]`; backend: request-header / actor field)
2. Organization preference (frontend: `localStorage["masci.tz.org"]`; backend: tenant record — currently `America/New_York`)
3. Browser timezone (frontend only)
4. Server default: `America/New_York` (last resort)

---

## Phase 2 — Remaining conversion backlog (frontend UTC-display leaks)

Every file below shows a raw UTC timestamp somewhere. Convert by:
1. `import { formatPlatformTime } from "@/lib/platformTime";`
2. Replace `something.slice(0, 19).replace("T", " ")` (and its variants) with `formatPlatformTime(something)`.
3. Add the file's path to `_OPERATOR_FACING_MODULES` in the guard test — it'll enforce zero regressions after your change.

| Priority | File | Surface | Est. sites |
|---|---|---|---|
| P1 | `frontend/src/pages/HrEmployees.jsx` | HR drawer "Last transportation sync" | 1 |
| P1 | `frontend/src/pages/admin/AdminAuditLog.jsx` | Every audit row's `at` column | ~10 |
| P1 | `frontend/src/pages/admin/AdminCommandCenter.jsx` | Command Center timeline | 3 |
| P1 | `frontend/src/pages/admin/AdminDigestConfig.jsx` | Last-run timestamp | 1 |
| P1 | `frontend/src/pages/admin/AdminGovernance.jsx` | Governance snapshot | 2 |
| P2 | `frontend/src/pages/admin/AdminRecovery.jsx` | Recovery events | 4 |
| P2 | `frontend/src/pages/admin/DeployRecovery.jsx` | Deploy history | 3 |
| P2 | `frontend/src/pages/admin/AdminComplianceFindings.jsx` | Finding created/updated | 5 |
| P2 | `frontend/src/pages/AdminLegacyImports.jsx` | Import upload/promotion times | 4 |
| P2 | `frontend/src/components/EmailRoutingV2Panel.jsx` | Email health + delivery rows | ~15 |
| P2 | `frontend/src/components/admin/MaintainxDefectCoverageSection.jsx` | Defect reported_at | 1 |
| P2 | `frontend/src/pages/HrHub.jsx` | HR hub snapshot cards | 3 |
| P2 | `frontend/src/pages/HrTimeVerification.jsx` | Time verification rows | 5 |
| P2 | `frontend/src/pages/transportation/CertificateVerify.jsx` | Cert verify metadata | 3 |
| P3 | `frontend/src/pages/transportation/_command_queue.jsx` | Queue timestamps | 4 |
| P3 | `frontend/src/pages/transportation/_intelligence.jsx` | Intelligence timeline | 5 |
| P3 | `frontend/src/pages/transportation/_lists.jsx` | List timestamps | 3 |
| P3 | `frontend/src/pages/transportation/_orientation.jsx` | Orientation history | 3 |
| P3 | `frontend/src/pages/transportation/_views.jsx` | View metadata | 3 |
| P3 | `frontend/src/pages/transportation/_widgets.jsx` | Widget refresh labels | 4 |

**Estimated total remaining sites (frontend): ~80.**

Owner: main-agent · Target: rolling (2–3 files per follow-up session) · Risk: low (mechanical, single-line changes protected by the guard).

---

## Phase 2 — Backend conversion backlog

270 backend files use `utcnow`, `timezone.utc`, `isoformat`, or `strftime`. Most are internal (log lines, DB writes, scheduler) and are OUT OF SCOPE per the mission ("Logs may remain UTC. Do NOT change them.").

The subset that IS operator-facing (PDF renderers, email templates, AI prompt assembly, export writers, notification bodies):

### Phase 2a — Shipped 2026-07-09 (high-trust artifacts)

| File | Surface | Converted |
|---|---|---|
| `backend/pdf_branding.py` | Universal HTML PDF audit + metadata + `wrap_pdf_html` footer | ✅ `format_platform_stamp` |
| `backend/pdf_branding_rl.py` | Universal ReportLab audit + metadata Flowables | ✅ `format_platform_stamp` |
| `backend/pdf_render.py` | Daily Report renderer + email HTML body (already routed report_date through `_fmt_date`; DR PDF audit envelope stamp converted) | ✅ `format_platform_stamp` |
| `backend/training_pdf.py` | Training packet header (EN + ES bilingual "generated" stamp) | ✅ `format_platform_date` |
| `backend/pm_welcome_pdf.py` | PM welcome letter "Issued" date | ✅ `format_platform_date` |
| `backend/routes/safety_exports.py` | 10 Safety Portal print-HTML endpoints subtitle; filename stamp | ✅ `format_platform_stamp` + local `_stamp` |
| `backend/routes/master_history.py` | Asset + Employee history CSV "Generated" column | ✅ `format_platform_stamp` |
| `backend/routes/trench_safety/report_export.py` | Trench Safety XLSX A4 metadata + PDF kicker | ✅ `format_platform_stamp` |
| `backend/routes/dispatch_exports.py` | Dispatch CSV filename stamp | ✅ local `_now_stamp` |
| `backend/services/dr_ai/agents.py` | AI system prompt: STRICTNESS rule 11 + manifest_summary rule (LOCAL-ONLY output) | ✅ prompt rules added |

**Marked exempt (machine boundaries — not operator-facing):**

| File | Line | Why exempt |
|---|---|---|
| `backend/routes/dr_v2_pdf.py` | `X-*-Rendered-At` HTTP response headers (both endpoints) | Machine-consumed HTTP header; UI renders via `formatPlatformTime` |
| `backend/services/dr_ai/emergent_provider.py` | Envelope `generated_at` | JSON envelope timestamp; frontend renders |
| `backend/services/dr_evidence/manifest.py` | Manifest `generated_at` | Machine manifest metadata; PDF/UI formats it |
| `backend/routes/dr_v2.py` | `_now_iso` helper | JSON envelope timestamps only |
| `backend/routes/dr_v2_canonicalize.py` | `_now_iso` helper | JSON envelope timestamps only |
| `backend/routes/master_history.py` | Endpoint response `generated_at` fields | JSON envelope, frontend renders |
| `backend/routes/safety_exports.py` L310 | `now = datetime.now(...)` reduced to `.date()` on next line for DB range comparisons | Date-only DB math, no wall-clock leak |

### Phase 2b — Shipped 2026-07-09 (second-tier PDFs, notification builders, HR compliance brief, ODR PDF audit footer)

| File | Surface | Converted |
|---|---|---|
| `backend/routes/hr_portal.py` | HR Compliance Brief PDF header ("Generated … · Viewer: …") | ✅ `format_platform_stamp` |
| `backend/routes/employee_records.py` | HR employee package PDF header (secondary variant · "Generated … · By …") | ✅ `format_platform_stamp` |
| `backend/incident_engine/report_render.py` | 4 sites: report cover stamp, section footer, weekly digest header, weekly digest footer — via new `_fmt_gen` helper | ✅ `format_platform_stamp` |
| `backend/routes/odr/pdf.py` | Rendered stamp in every-page footer + `Contact Time` / `Submitted At` / `Acknowledged At` KV rows (relabeled from `… UTC`) | ✅ new `_local_display` helper wrapping `format_platform_stamp` |
| `backend/hub_banners_pdf.py` | Banner Audit Trail PDF (OSHA / insurance evidence): every row stamp via `_fmt_ts`, page footer stamp, table column header (`Timestamp (UTC)` → `Timestamp`) | ✅ `format_platform_stamp` |
| `backend/routes/trench_safety/pulse.py` | Trench Safety Pulse HTML briefing "Generated" line | ✅ `format_platform_stamp` |
| `backend/routes/trench_safety/report_distribution.py` | Leadership Digest HTML "Generated" line + subscription-delivery email body + attachment filename stamp | ✅ `format_platform_stamp` + local `resolve_tz` for filename |
| `backend/routes/asset_documents.py` | Asset Profile PDF (fleet · equipment · road plates) "Generated" stamp | ✅ `format_platform_stamp` |
| `backend/routes/fleet_ops.py` | Fleet Severity Reference Card PDF print stamp | ✅ `format_platform_stamp` |
| `backend/lib/field_submitter_identity.py` | Correction-request email "Link expires …" line | ✅ `format_platform_stamp` |
| `backend/server.py` | Nightly Backup email subject + body "Generated" line | ✅ `format_platform_stamp` |

**Marked exempt in Phase 2b (machine boundaries):**

| File | Line/Range | Why exempt |
|---|---|---|
| `backend/incident_engine/reports.py` L386, L399 | payload metadata `generated_at` | Rendered downstream by `report_render.py:_fmt_gen` |
| `backend/routes/odr/pdf.py` `_utc_iso` helper | canonical UTC stamp | Used ONLY as SHA-256 input for the ODR envelope hash (audit chain) |
| `backend/routes/odr/pdf.py` `at_utc` in `odr_pdf_renders` | DB audit ledger stamp | UTC by doctrine; never rendered |
| `backend/routes/employee_records.py` `_now_iso` | internal DB storage helper | `created_at` / `updated_at` / audit trail; never rendered |
| `backend/routes/hr_portal.py` L1050 | payload metadata `generated_at` | HR PDF renderer formats it locally on the next stanza |
| `backend/routes/employee_lifecycle.py` L1252, L1351 | JSON API envelopes | Frontend renders |

### Files NOT in guard file-list (guarded-by-comment)

To avoid ~50 false-positive noise entries from date-only DB range comparisons and cron/scheduler math, these multi-hundred-to-multi-thousand-line service files aren't in the guard's `_OPERATOR_FACING_MODULES` list. Their operator-facing sites are converted line-by-line and their converted output is verifiable in live PDFs/emails:

- `backend/routes/hr_portal.py` (1930 lines) · operator-facing site verified in live PDF render (`HR Compliance Brief`)
- `backend/routes/employee_lifecycle.py` (2600 lines) · both envelope sites carry inline exemption
- `backend/routes/trench_safety/pulse.py` (580 lines) · Pulse HTML briefing site converted
- `backend/routes/trench_safety/report_distribution.py` (650 lines) · Digest HTML + email body sites converted
- `backend/routes/asset_documents.py` (1075 lines) · Asset Profile PDF site converted
- `backend/routes/fleet_ops.py` (2325 lines) · Severity Reference PDF site converted (verified live)
- `backend/lib/field_submitter_identity.py` (742 lines) · Correction-request email site converted
- `backend/server.py` (16866 lines) · Nightly Backup email site converted

### Phase 2c — Deferred to a follow-up session

| Priority | Area | Notes |
|---|---|---|
| P3 | Backend AI narrative "generated at" labels | No per-narrative label currently rendered to operators — deferred until product asks for one |
| P3 | Slack / Teams webhook message builders | Currently emit machine-neutral payloads (`ts` is not string-rendered by MASCI code — Slack renders it) |

Owner: main-agent · Target: rolling · Risk: low (mechanical + guard-enforced + live-verified).

---

## Migration pattern (copy-paste for future PRs)

### Frontend
```diff
- import React from "react";
+ import React from "react";
+ import { formatPlatformTime } from "@/lib/platformTime";

- <span>Generated {(data.generated_at || "").slice(0, 19).replace("T", " ")} UTC</span>
+ <span>Generated {formatPlatformTime(data.generated_at)}</span>
```

### Backend (PDF/email/AI)
```diff
- from datetime import datetime, timezone
- ts = datetime.now(timezone.utc).isoformat()
- pdf.text(f"Generated {ts}")
+ from lib.platform_time import localize_timestamp
+ from datetime import datetime, timezone
+ ts = datetime.now(timezone.utc)                  # storage stays UTC
+ pdf.text(f"Generated {localize_timestamp(ts)}")  # display is local
```

### Registering a converted file with the guard
Add its relative path to `_OPERATOR_FACING_MODULES` in `/app/backend/tests/test_track_27_03_zero_utc_guard.py`. The guard will fail if that file ever regresses.

### Exempting a legitimate UTC line
When UTC IS the correct thing to display (e.g. a backup schedule that runs at absolute UTC time and is documented as such), add a comment on the offending line:
```
    <div>Backups run at 02:00 UTC {/* TRACK-27.03-EXEMPT: schedule is UTC-anchored infrastructure */}</div>
```
