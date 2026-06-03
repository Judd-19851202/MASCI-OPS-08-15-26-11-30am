# Timestamp Doctrine Probe Report

_Phase TRUST-TIME-1B · self-protection probe · 🔴 FAIL_

- Scanned files     : **766**
- Patterns           : **5**
- New violations     : **1**
- New warnings       : **16**
- Baselined          : **75**
- Scan runtime       : **129 ms**

## Pattern catalogue

| ID | Language | Severity | Fix |
|----|----------|----------|-----|
| `F1·slice16-replaceT` | frontend | high | Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js |
| `F2·slice19-replaceT` | frontend | high | Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js |
| `F4·toLocaleString-bare` | frontend | med | Use formatLocalDateTime() from lib/dateUtils.js — defensively coerces naive ISO as UTC. |
| `F5·toLocaleDateString-bare` | frontend | med | Use formatLocalDate() from lib/dateUtils.js. |
| `B1·datetime-utcnow` | backend | high | Use datetime.now(timezone.utc) — utcnow() returns a NAIVE datetime. |

## ⚠ New violations

- `pages/HrPayrollVariance.jsx:272` · `F1·slice16-replaceT` · `<td className="px-3 py-2 text-slate-600 font-mono text-xs">{(b.created_at || "")` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js

## · New warnings (review · not deploy-blocking)

- `components/LifecyclePanel.jsx:411` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/IncidentLifecyclePanel.jsx:415` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/SiteInspectionLifecyclePanel.jsx:561` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/UndoLastTransitionButton.jsx:64` · `F4·toLocaleString-bare` · `const at = ev.at ? new Date(ev.at).toLocaleString() : "—";`
- `components/QaqcLifecyclePanel.jsx:559` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `pages/HrEmployees.jsx:975` · `F4·toLocaleString-bare` · `<span className="text-slate-500">{new Date(h.at).toLocaleString()}</span>`
- `pages/ViewIncident.jsx:743` · `F4·toLocaleString-bare` · `{data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}`
- `pages/ViewInspection.jsx:483` · `F4·toLocaleString-bare` · `{t("Generated")} {data.created_at ? new Date(data.created_at).toLocaleString() :`
- `pages/HrEmployeeRequestsQueue.jsx:296` · `F4·toLocaleString-bare` · `{new Date(req.requested_at).toLocaleString()}`
- `pages/ViewDailyReport.jsx:637` · `F4·toLocaleString-bare` · `{data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}`
- `pages/JhaPlansHub.jsx:286` · `F5·toLocaleDateString-bare` · `? new Date(f.uploaded_at).toLocaleDateString()`
- `pages/admin/AdminJhaAcknowledgements.jsx:161` · `F4·toLocaleString-bare` · `? new Date(row.latest_acknowledged_at).toLocaleString()`
- `pages/admin/AdminJhaAcknowledgements.jsx:242` · `F4·toLocaleString-bare` · `? new Date(row.file.uploaded_at).toLocaleString()`
- `pages/admin/AdminJhaAcknowledgements.jsx:256` · `F4·toLocaleString-bare` · `{new Date(a.acknowledged_at).toLocaleString()} · {a.locale}`
- `pages/admin/AdminJhaAcknowledgements.jsx:341` · `F4·toLocaleString-bare` · `{new Date(a.acknowledged_at).toLocaleString()}`
- `pages/admin/AdminRecoveryStream.jsx:167` · `F4·toLocaleString-bare` · `{ev.at ? new Date(ev.at).toLocaleString() : "—"}`

## How to clear violations

1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.
2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. If a legacy line is reviewed and accepted as-is, add its
   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.

Run `python3 scripts/timestamp_doctrine_probe.py --bless` to
regenerate the baseline after a fix sweep.
