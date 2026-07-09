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

| Priority | Area | Files | Notes |
|---|---|---|---|
| P1 | `backend/services/pdf/*` | ~8 files | PDF headers/footers, timestamps in body |
| P1 | `backend/services/dr_ai/prompt_builder*.py` | 2 files | AI prompts must reference local time per mission |
| P1 | Email routing templates in `backend/services/email/*` | ~5 files | "Sent at" lines |
| P2 | `backend/routes/*_export.py` — CSV/xlsx writers | ~10 files | Excel column headers |
| P2 | Notification builders | ~6 files | Operator-facing toast/pill payloads |
| P3 | AI summary text builders | ~4 files | Grounded narrative "generated at" line |

**Estimated operator-facing backend files: ~35.**

Owner: main-agent · Target: rolling · Risk: medium (PDF/email — needs visual verification per surface).

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
