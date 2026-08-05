# Timestamp Doctrine Probe Report

_Phase TRUST-TIME-1B · self-protection probe · 🔴 FAIL_

- Scanned files     : **1358**
- Patterns           : **5**
- New violations     : **44**
- New warnings       : **1**
- Baselined          : **10**
- Scan runtime       : **248 ms**

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
- `pages/HrEmployees.jsx:1835` · `F2·slice19-replaceT` · `<Row2 label="Last Transportation sync" value={data.last_sync_at ? data.last_sync` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/OperationsCenterCommand.jsx:475` · `F1·slice16-replaceT` · `<span className="font-mono text-[10.5px] text-slate-500">{String(ev.timestamp ||` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AdminLegacyImports.jsx:301` · `F1·slice16-replaceT` · `{firstFile?.uploaded_by_name || "—"} · {(row.created_at || "").slice(0, 16).repl` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/HrPayrollVariance.jsx:274` · `F1·slice16-replaceT` · `<td className="px-3 py-2 text-slate-600 font-mono text-xs">{(b.created_at || "")` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:211` · `F1·slice16-replaceT` · `{String(row.created_at).slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:407` · `F1·slice16-replaceT` · `<KV k="Created" v={String(doc.created_at).slice(0, 16).replace("T", " ")} />` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:408` · `F1·slice16-replaceT` · `{doc.approved_at && <KV k="Approved" v={String(doc.approved_at).slice(0, 16).rep` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:439` · `F1·slice16-replaceT` · `<span className="text-slate-600">{String(a.at).slice(0, 16).replace("T", " ")}</` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:171` · `F1·slice16-replaceT` · `<Stat label="Last sync" value={p.last_sync_at ? p.last_sync_at.slice(0, 16).repl` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:172` · `F1·slice16-replaceT` · `<Stat label="Last success" value={p.last_successful_sync_at ? p.last_successful_` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:173` · `F1·slice16-replaceT` · `<Stat label="Last failure" value={p.last_failed_sync_at ? p.last_failed_sync_at.` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:691` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-xs">{(r.started_at || r.occurred_at || "` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:1235` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(r.started_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:385` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-slate-500">{(x.created_at || "").slice(0` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:581` · `F1·slice16-replaceT` · `<td className="px-2 py-2 font-mono text-amber-900/70">{(h.created_at || "").slic` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:624` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-slate-500">{(h.created_at || "").slice(0` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:819` · `F1·slice16-replaceT` · `<div className="text-slate-500 text-[10px]">{(r.last_activity_at || "").slice(0,` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:842` · `F1·slice16-replaceT` · `Computed at {(data.now || "").slice(0, 16).replace("T", " ")} · {totals.matched}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:173` · `F1·slice16-replaceT` · `<Field label="Started"          value={(a.started_at || "").slice(0,16).replace(` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:196` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(x.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:433` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(p.created_at || p.dat` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:461` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.event_at || e.recei` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:480` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/DeployRecovery.jsx:134` · `F2·slice19-replaceT` · `<span className="font-mono text-slate-500 whitespace-nowrap">{(b.started_at || "` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/admin/DeployRecovery.jsx:151` · `F2·slice19-replaceT` · `<span className="font-mono text-slate-500">{(h.deployed_at || "").slice(0, 19).r` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/CertificateVerify.jsx:77` · `F2·slice19-replaceT` · `<Row label="Completed" value={(cert.completed_at || "").slice(0, 19).replace("T"` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_views.jsx:262` · `F2·slice19-replaceT` · `Last scan: {data.last_run_at ? data.last_run_at.slice(0, 19).replace("T", " ") :` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:237` · `F2·slice19-replaceT` · `<Row label="Started" value={(last.started_at || "").slice(0, 19).replace("T", " ` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:238` · `F2·slice19-replaceT` · `<Row label="Completed" value={(last.completed_at || "").slice(0, 19).replace("T"` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:493` · `F2·slice19-replaceT` · `Last run: {data?.last_run_at ? data.last_run_at.slice(0, 19).replace("T", " ") :` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_command_queue.jsx:598` · `F2·slice19-replaceT` · `<Row label="Last run" value={(lastRun.ts || "").slice(0, 19).replace("T", " ")} ` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_lists.jsx:1151` · `F2·slice19-replaceT` · `<Row label="HR updated" value={data.hr_linkage.updated_at.slice(0, 19).replace("` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_lists.jsx:1177` · `F2·slice19-replaceT` · `Last synced: {data.hr_projection.synced_at.slice(0, 19).replace("T", " ")} ({dat` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_lists.jsx:1302` · `F2·slice19-replaceT` · `Schema {snap.schema_version} · Computed {(snap.computed_at || "").slice(0, 19).r` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_orientation.jsx:556` · `F2·slice19-replaceT` · `{row.last_audit_at.slice(0, 19).replace("T", " ")} ·` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:188` · `F2·slice19-replaceT` · `<span>· Generated {(data.generated_at || "").slice(0, 19).replace("T", " ")}</sp` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:439` · `F2·slice19-replaceT` · `Schema {data.schema_version} · Generated {(data.generated_at || "").slice(0, 19)` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:625` · `F2·slice19-replaceT` · `Schema {data.schema_version} · Window {data.range?.days} days · Generated {(data` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js
- `pages/transportation/_intelligence.jsx:853` · `F2·slice19-replaceT` · `Schema {signals.schema_version} · Generated {(signals.generated_at || "").slice(` → Use formatLocalDateTime() or formatUtcForAudit() from lib/dateUtils.js

## · New warnings (review · not deploy-blocking)

- `pages/DevHub.jsx:165` · `F4·toLocaleString-bare` · `return new Date(iso).toLocaleString(undefined, {`

## How to clear violations

1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.
2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. If a legacy line is reviewed and accepted as-is, add its
   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.

Run `python3 scripts/timestamp_doctrine_probe.py --bless` to
regenerate the baseline after a fix sweep.
