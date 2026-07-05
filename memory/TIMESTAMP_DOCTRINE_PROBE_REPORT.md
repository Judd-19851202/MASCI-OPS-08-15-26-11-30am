# Timestamp Doctrine Probe Report

_Phase TRUST-TIME-1B · self-protection probe · 🔴 FAIL_

- Scanned files     : **1189**
- Patterns           : **5**
- New violations     : **38**
- New warnings       : **77**
- Baselined          : **67**
- Scan runtime       : **211 ms**

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
- `components/dispatch/DispatchDecisionChip.jsx:236` · `F2·slice19-replaceT` · `Generated {(data.generated_at || "").slice(0, 19).replace("T", " ")} · v{data.sc` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/HrEmployees.jsx:1571` · `F2·slice19-replaceT` · `<Row2 label="Last Transportation sync" value={data.last_sync_at ? data.last_sync` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/OperationsCenterCommand.jsx:475` · `F1·slice16-replaceT` · `<span className="font-mono text-[10.5px] text-slate-500">{String(ev.timestamp ||` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/HrHub.jsx:406` · `F2·slice19-replaceT` · `Last eligibility compute: {data.last_eligibility_compute ? data.last_eligibility` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/HrPayrollVariance.jsx:273` · `F1·slice16-replaceT` · `<td className="px-3 py-2 text-slate-600 font-mono text-xs">{(b.created_at || "")` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:211` · `F1·slice16-replaceT` · `{String(row.created_at).slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:407` · `F1·slice16-replaceT` · `<KV k="Created" v={String(doc.created_at).slice(0, 16).replace("T", " ")} />` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:408` · `F1·slice16-replaceT` · `{doc.approved_at && <KV k="Approved" v={String(doc.approved_at).slice(0, 16).rep` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:439` · `F1·slice16-replaceT` · `<span className="text-slate-600">{String(a.at).slice(0, 16).replace("T", " ")}</` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:385` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-slate-500">{(x.created_at || "").slice(0` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:581` · `F1·slice16-replaceT` · `<td className="px-2 py-2 font-mono text-amber-900/70">{(h.created_at || "").slic` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:624` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-slate-500">{(h.created_at || "").slice(0` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:819` · `F1·slice16-replaceT` · `<div className="text-slate-500 text-[10px]">{(r.last_activity_at || "").slice(0,` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:842` · `F1·slice16-replaceT` · `Computed at {(data.now || "").slice(0, 16).replace("T", " ")} · {totals.matched}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:171` · `F1·slice16-replaceT` · `<Field label="Started"          value={(a.started_at || "").slice(0,16).replace(` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:194` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(x.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:431` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(p.created_at || p.dat` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:459` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.event_at || e.recei` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:478` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/transportation/CertificateVerify.jsx:41` · `F2·slice19-replaceT` · `<Row label="Completed" value={(cert.completed_at || "").slice(0, 19).replace("T"` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_views.jsx:233` · `F2·slice19-replaceT` · `Last scan: {data.last_run_at ? data.last_run_at.slice(0, 19).replace("T", " ") :` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:237` · `F2·slice19-replaceT` · `<Row label="Started" value={(last.started_at || "").slice(0, 19).replace("T", " ` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:238` · `F2·slice19-replaceT` · `<Row label="Completed" value={(last.completed_at || "").slice(0, 19).replace("T"` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:493` · `F2·slice19-replaceT` · `Last run: {data?.last_run_at ? data.last_run_at.slice(0, 19).replace("T", " ") :` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:598` · `F2·slice19-replaceT` · `<Row label="Last run" value={(lastRun.ts || "").slice(0, 19).replace("T", " ")} ` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_lists.jsx:1147` · `F2·slice19-replaceT` · `<Row label="HR updated" value={data.hr_linkage.updated_at.slice(0, 19).replace("` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_lists.jsx:1173` · `F2·slice19-replaceT` · `Last synced: {data.hr_projection.synced_at.slice(0, 19).replace("T", " ")} ({dat` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_lists.jsx:1298` · `F2·slice19-replaceT` · `Schema {snap.schema_version} · Computed {(snap.computed_at || "").slice(0, 19).r` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_orientation.jsx:556` · `F2·slice19-replaceT` · `{row.last_audit_at.slice(0, 19).replace("T", " ")} ·` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:169` · `F2·slice19-replaceT` · `<span>· Generated {(data.generated_at || "").slice(0, 19).replace("T", " ")}</sp` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:420` · `F2·slice19-replaceT` · `Schema {data.schema_version} · Generated {(data.generated_at || "").slice(0, 19)` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:606` · `F2·slice19-replaceT` · `Schema {data.schema_version} · Window {data.range?.days} days · Generated {(data` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:822` · `F2·slice19-replaceT` · `Schema {signals.schema_version} · Generated {(signals.generated_at || "").slice(` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js

## · New warnings (review · not deploy-blocking)

- `components/AdminUnifiedDirectoryPanel.jsx:349` · `F5·toLocaleDateString-bare` · `? new Date(u.last_login_at).toLocaleDateString()`
- `components/AdminJobMasterPanel.jsx:503` · `F4·toLocaleString-bare` · `{j.deleted_at ? new Date(j.deleted_at).toLocaleString() : "—"}`
- `components/PlatformTrustValidator.jsx:95` · `F4·toLocaleString-bare` · `setLastRun(new Date().toLocaleString());`
- `components/IncidentLifecyclePanel.jsx:422` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/PlatformTrustDashboard.jsx:84` · `F4·toLocaleString-bare` · `return new Date(iso).toLocaleString();`
- `components/PlatformTrustDashboard.jsx:294` · `F4·toLocaleString-bare` · `setLastRun(new Date().toLocaleString());`
- `components/NotificationBell.jsx:445` · `F4·toLocaleString-bare` · `Sound muted until {new Date(muteUntil).toLocaleString()}. Notifications still ar`
- `components/NotificationBell.jsx:460` · `F4·toLocaleString-bare` · `const localTime = n.created_at ? new Date(n.created_at).toLocaleString([], { dat`
- `components/UndoLastTransitionButton.jsx:71` · `F4·toLocaleString-bare` · `const at = ev.at ? new Date(ev.at).toLocaleString() : "—";`
- `components/EquipmentMasterPanel.jsx:521` · `F4·toLocaleString-bare` · `{u.deleted_at ? new Date(u.deleted_at).toLocaleString() : "—"}`
- `components/AdminAccessControlPanel.jsx:366` · `F5·toLocaleDateString-bare` · `{u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "—"}`
- `components/OperationsTrustCenter.jsx:111` · `F4·toLocaleString-bare` · `return new Date(iso).toLocaleString();`
- `components/OperationsTrustCenter.jsx:588` · `F4·toLocaleString-bare` · `setLastRun(new Date().toLocaleString());`
- `components/MasterListPanel.jsx:511` · `F4·toLocaleString-bare` · `{row.deleted_at ? new Date(row.deleted_at).toLocaleString() : "—"}`
- `components/operational_intelligence/OperationalThread.jsx:40` · `F4·toLocaleString-bare` · `return new Date(dt).toLocaleString(undefined, {`
- `components/triage/FocusBanner.jsx:263` · `F4·toLocaleString-bare` · `r.reported_at ? `Reported ${new Date(r.reported_at).toLocaleString()}` : null,`
- `components/triage/FocusBanner.jsx:294` · `F4·toLocaleString-bare` · `r.shift_start_at ? `Shift start: ${new Date(r.shift_start_at).toLocaleString()}``
- `components/team/AssignmentHistoryDrawer.jsx:44` · `F4·toLocaleString-bare` · `return new Date(at).toLocaleString();`
- `components/pm/command/PmProjectFirstHome.jsx:504` · `F5·toLocaleDateString-bare` · `{d.created_at ? new Date(d.created_at).toLocaleDateString() : ""}`
- `components/dispatch/AssignmentDrawer.jsx:43` · `F4·toLocaleString-bare` · `return new Date(iso).toLocaleString();`
- `lib/resiliency/DraftStatusPill.jsx:36` · `F4·toLocaleString-bare` · `return new Date(ts).toLocaleString();`
- `pages/HrEmployees.jsx:1238` · `F4·toLocaleString-bare` · `<span className="text-slate-500">{new Date(h.at).toLocaleString()}</span>`
- `pages/HrEmployees.jsx:360` · `F5·toLocaleDateString-bare` · `{new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day:`
- `pages/SafetyCaseWorkspace.jsx:52` · `F4·toLocaleString-bare` · `try { return new Date(dt).toLocaleString(); } catch { return dt; }`
- `pages/SafetyCaseWorkspace.jsx:57` · `F5·toLocaleDateString-bare` · `try { return new Date(dt).toLocaleDateString(undefined, { year: "numeric", month`
- `pages/Tasks.jsx:197` · `F4·toLocaleString-bare` · `{t.source_module} · created {new Date(t.created_at).toLocaleString()}`
- `pages/Tasks.jsx:303` · `F4·toLocaleString-bare` · `<div className="text-slate-700">{new Date(task.created_at).toLocaleString()}</di`
- `pages/Tasks.jsx:308` · `F4·toLocaleString-bare` · `<div className="text-slate-700">{new Date(task.due_at).toLocaleString()}</div>`
- `pages/Tasks.jsx:349` · `F4·toLocaleString-bare` · `<div className="font-mono text-[10px] text-slate-400 mt-0.5">{new Date(c.at).toL`
- `pages/Tasks.jsx:372` · `F4·toLocaleString-bare` · `<span className="font-mono">{new Date(a.at).toLocaleString()}</span>`

_…and 47 more (see JSON output)._

## How to clear violations

1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.
2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. If a legacy line is reviewed and accepted as-is, add its
   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.

Run `python3 scripts/timestamp_doctrine_probe.py --bless` to
regenerate the baseline after a fix sweep.
