# Timestamp Doctrine Probe Report

_Phase TRUST-TIME-1B · self-protection probe · 🔴 FAIL_

- Scanned files     : **1026**
- Patterns           : **5**
- New violations     : **16**
- New warnings       : **49**
- Baselined          : **77**
- Scan runtime       : **180 ms**

## Pattern catalogue

| ID | Language | Severity | Fix |
|----|----------|----------|-----|
| `F1·slice16-replaceT` | frontend | high | Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js |
| `F2·slice19-replaceT` | frontend | high | Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js |
| `F4·toLocaleString-bare` | frontend | med | Use formatLocalDateTime() from lib/dateUtils.js — defensively coerces naive ISO as UTC. |
| `F5·toLocaleDateString-bare` | frontend | med | Use formatLocalDate() from lib/dateUtils.js. |
| `B1·datetime-utcnow` | backend | high | Use datetime.now(timezone.utc) — utcnow() returns a NAIVE datetime. |

## ⚠ New violations

- `components/pm/command/PmShopImpactBoard.jsx:73` · `F1·slice16-replaceT` · `{String(r.reported_at || "—").slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `components/pm/command/PmTimelineBoard.jsx:65` · `F1·slice16-replaceT` · `{String(ev.timestamp || "—").slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `components/pm/command/PmResourcesBoard.jsx:139` · `F1·slice16-replaceT` · `String(r.last_activity_at || "—").slice(0, 16).replace("T", " ")` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `components/pm/command/PmSafetyImpactBoard.jsx:72` · `F1·slice16-replaceT` · `{String(r.occurred_at || "—").slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `components/pm/command/PmSafetyImpactBoard.jsx:106` · `F1·slice16-replaceT` · `{String(r.due_at || "—").slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/OperationsCenterCommand.jsx:469` · `F1·slice16-replaceT` · `<span className="font-mono text-[10.5px] text-slate-500">{String(ev.timestamp ||` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/HrPayrollVariance.jsx:273` · `F1·slice16-replaceT` · `<td className="px-3 py-2 text-slate-600 font-mono text-xs">{(b.created_at || "")` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:211` · `F1·slice16-replaceT` · `{String(row.created_at).slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:407` · `F1·slice16-replaceT` · `<KV k="Created" v={String(doc.created_at).slice(0, 16).replace("T", " ")} />` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:408` · `F1·slice16-replaceT` · `{doc.approved_at && <KV k="Approved" v={String(doc.approved_at).slice(0, 16).rep` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:439` · `F1·slice16-replaceT` · `<span className="text-slate-600">{String(a.at).slice(0, 16).replace("T", " ")}</` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:171` · `F1·slice16-replaceT` · `<Field label="Started"          value={(a.started_at || "").slice(0,16).replace(` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:194` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(x.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:431` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(p.created_at || p.dat` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:459` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.event_at || e.recei` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:478` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js

## · New warnings (review · not deploy-blocking)

- `components/AdminUnifiedDirectoryPanel.jsx:349` · `F5·toLocaleDateString-bare` · `? new Date(u.last_login_at).toLocaleDateString()`
- `components/IncidentLifecyclePanel.jsx:422` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/NotificationBell.jsx:270` · `F4·toLocaleString-bare` · `Sound muted until {new Date(muteUntil).toLocaleString()}. Notifications still ar`
- `components/NotificationBell.jsx:285` · `F4·toLocaleString-bare` · `const localTime = n.created_at ? new Date(n.created_at).toLocaleString([], { dat`
- `components/UndoLastTransitionButton.jsx:71` · `F4·toLocaleString-bare` · `const at = ev.at ? new Date(ev.at).toLocaleString() : "—";`
- `components/triage/FocusBanner.jsx:263` · `F4·toLocaleString-bare` · `r.reported_at ? `Reported ${new Date(r.reported_at).toLocaleString()}` : null,`
- `components/triage/FocusBanner.jsx:294` · `F4·toLocaleString-bare` · `r.shift_start_at ? `Shift start: ${new Date(r.shift_start_at).toLocaleString()}``
- `components/pm/command/PmProjectFirstHome.jsx:311` · `F5·toLocaleDateString-bare` · `{d.created_at ? new Date(d.created_at).toLocaleDateString() : ""}`
- `lib/resiliency/DraftStatusPill.jsx:36` · `F4·toLocaleString-bare` · `return new Date(ts).toLocaleString();`
- `pages/HrEmployees.jsx:1072` · `F4·toLocaleString-bare` · `<span className="text-slate-500">{new Date(h.at).toLocaleString()}</span>`
- `pages/Tasks.jsx:197` · `F4·toLocaleString-bare` · `{t.source_module} · created {new Date(t.created_at).toLocaleString()}`
- `pages/Tasks.jsx:303` · `F4·toLocaleString-bare` · `<div className="text-slate-700">{new Date(task.created_at).toLocaleString()}</di`
- `pages/Tasks.jsx:308` · `F4·toLocaleString-bare` · `<div className="text-slate-700">{new Date(task.due_at).toLocaleString()}</div>`
- `pages/Tasks.jsx:349` · `F4·toLocaleString-bare` · `<div className="font-mono text-[10px] text-slate-400 mt-0.5">{new Date(c.at).toL`
- `pages/Tasks.jsx:372` · `F4·toLocaleString-bare` · `<span className="font-mono">{new Date(a.at).toLocaleString()}</span>`
- `pages/Tasks.jsx:198` · `F5·toLocaleDateString-bare` · `{t.due_at && ` · due ${new Date(t.due_at).toLocaleDateString()}`}`
- `pages/AdminTerminations.jsx:52` · `F5·toLocaleDateString-bare` · `return new Date(iso).toLocaleDateString(undefined, {`
- `pages/FleetVisibility.jsx:184` · `F4·toLocaleString-bare` · `{e.timestamp ? new Date(e.timestamp).toLocaleString() : ""}`
- `pages/FleetVisibility.jsx:224` · `F4·toLocaleString-bare` · `? new Date(group.latest_inspection_at).toLocaleString()`
- `pages/FleetVisibility.jsx:318` · `F4·toLocaleString-bare` · `{d.repaired_at && ` · ${new Date(d.repaired_at).toLocaleString()}`}`
- `pages/FleetVisibility.jsx:339` · `F4·toLocaleString-bare` · `{new Date(d.reported_at).toLocaleString()}`
- `pages/ViewIncident.jsx:745` · `F4·toLocaleString-bare` · `{data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}`
- `pages/ViewInspection.jsx:485` · `F4·toLocaleString-bare` · `{t("Generated")} {data.created_at ? new Date(data.created_at).toLocaleString() :`
- `pages/ViewMeeting.jsx:408` · `F4·toLocaleString-bare` · `{t("Generated")} {data.created_at ? new Date(data.created_at).toLocaleString() :`
- `pages/HrEmployeeRequestsQueue.jsx:335` · `F4·toLocaleString-bare` · `{new Date(req.requested_at).toLocaleString()}`
- `pages/ViewDailyReport.jsx:684` · `F4·toLocaleString-bare` · `{data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}`
- `pages/JhaPlansAdmin.jsx:391` · `F5·toLocaleDateString-bare` · `? new Date(f.uploaded_at).toLocaleDateString()`
- `pages/shop/FuelLubeVisitRecords.jsx:157` · `F4·toLocaleString-bare` · `submitted {v.submitted_at ? new Date(v.submitted_at).toLocaleString() : "—"}`
- `pages/shop/ServiceTruckReconciliationDetail.jsx:113` · `F4·toLocaleString-bare` · `<div>Start submitted: <strong>{doc.start_submitted_at ? new Date(doc.start_submi`
- `pages/shop/ServiceTruckReconciliationDetail.jsx:114` · `F4·toLocaleString-bare` · `<div>End submitted: <strong>{doc.end_submitted_at ? new Date(doc.end_submitted_a`

_…and 19 more (see JSON output)._

## How to clear violations

1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.
2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. If a legacy line is reviewed and accepted as-is, add its
   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.

Run `python3 scripts/timestamp_doctrine_probe.py --bless` to
regenerate the baseline after a fix sweep.
