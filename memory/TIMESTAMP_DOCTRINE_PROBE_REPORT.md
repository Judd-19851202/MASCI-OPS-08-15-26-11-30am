# Timestamp Doctrine Probe Report

_Phase TRUST-TIME-1B · self-protection probe · 🔴 FAIL_

- Scanned files     : **887**
- Patterns           : **5**
- New violations     : **24**
- New warnings       : **39**
- Baselined          : **53**
- Scan runtime       : **152 ms**

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
- `pages/AssetTransfers.jsx:214` · `F1·slice16-replaceT` · `{String(row.created_at).slice(0, 16).replace("T", " ")}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:409` · `F1·slice16-replaceT` · `<KV k="Created" v={String(doc.created_at).slice(0, 16).replace("T", " ")} />` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:410` · `F1·slice16-replaceT` · `{doc.approved_at && <KV k="Approved" v={String(doc.approved_at).slice(0, 16).rep` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:411` · `F1·slice16-replaceT` · `{doc.in_transit_at && <KV k="In transit" v={String(doc.in_transit_at).slice(0, 1` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:412` · `F1·slice16-replaceT` · `{doc.received_at && <KV k="Received" v={String(doc.received_at).slice(0, 16).rep` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:413` · `F1·slice16-replaceT` · `{doc.closed_at && <KV k="Closed" v={String(doc.closed_at).slice(0, 16).replace("` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/AssetTransfers.jsx:441` · `F1·slice16-replaceT` · `<span className="text-slate-600">{String(a.at).slice(0, 16).replace("T", " ")}</` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:161` · `F1·slice16-replaceT` · `<Stat label="Last sync" value={p.last_sync_at ? p.last_sync_at.slice(0, 16).repl` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:162` · `F1·slice16-replaceT` · `<Stat label="Last success" value={p.last_successful_sync_at ? p.last_successful_` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:163` · `F1·slice16-replaceT` · `<Stat label="Last failure" value={p.last_failed_sync_at ? p.last_failed_sync_at.` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:681` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-xs">{(r.started_at || r.occurred_at || "` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminIntegrationCenter.jsx:1225` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(r.started_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:340` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-slate-500">{(x.created_at || "").slice(0` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:536` · `F1·slice16-replaceT` · `<td className="px-2 py-2 font-mono text-amber-900/70">{(h.created_at || "").slic` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:579` · `F1·slice16-replaceT` · `<td className="px-3 py-2 font-mono text-slate-500">{(h.created_at || "").slice(0` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:774` · `F1·slice16-replaceT` · `<div className="text-slate-500 text-[10px]">{(r.last_activity_at || "").slice(0,` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AdminDispatch.jsx:797` · `F1·slice16-replaceT` · `Computed at {(data.now || "").slice(0, 16).replace("T", " ")} · {totals.matched}` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:421` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(p.created_at || p.dat` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:449` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.event_at || e.recei` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:468` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/trench_safety/TrenchSafetyReportDistribution.jsx:225` · `F1·slice16-replaceT` · `{t("Last run")}: {s.last_run_at ? s.last_run_at.slice(0, 16).replace("T", " ") :` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/trench_safety/TrenchSafetyPulse.jsx:104` · `F1·slice16-replaceT` · `{t("Last generated")}: <span className="font-mono">{lastGen ? lastGen.slice(0, 1` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/trench_safety/TrenchSafetyPulse.jsx:256` · `F1·slice16-replaceT` · `<div className="text-xs text-slate-500 font-mono">{p.generated_at?.slice(0,16).r` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js

## · New warnings (review · not deploy-blocking)

- `components/AdminUnifiedDirectoryPanel.jsx:344` · `F5·toLocaleDateString-bare` · `? new Date(u.last_login_at).toLocaleDateString()`
- `components/DriverCommandProfile.jsx:148` · `F4·toLocaleString-bare` · `Completed: {last.completed_at ? new Date(last.completed_at).toLocaleString() : "`
- `components/DriverCommandProfile.jsx:160` · `F4·toLocaleString-bare` · `? `${operations.last_motive_activity.event_family} · ${new Date(operations.last_`
- `components/DriverCommandProfile.jsx:275` · `F4·toLocaleString-bare` · `value={equipment_usage.last_operated_at ? new Date(equipment_usage.last_operated`
- `components/DriverCommandProfile.jsx:313` · `F4·toLocaleString-bare` · `<KV label="Last Sync" value={motive.last_sync ? new Date(motive.last_sync).toLoc`
- `components/DriverCommandProfile.jsx:314` · `F4·toLocaleString-bare` · `<KV label="Last GPS Activity" value={motive.located_at ? new Date(motive.located`
- `components/DriverCommandProfile.jsx:358` · `F4·toLocaleString-bare` · `const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";`
- `components/DriverCommandProfile.jsx:115` · `F5·toLocaleDateString-bare` · `<KV label="Hire Date" value={identity.hire_date ? new Date(identity.hire_date).t`
- `components/LifecyclePanel.jsx:411` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/ShopOpsIntelPanel.jsx:32` · `F4·toLocaleString-bare` · `const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";`
- `components/ShopOpsIntelPanel.jsx:149` · `F5·toLocaleDateString-bare` · `const last = eq.last_seen ? new Date(eq.last_seen).toLocaleDateString() : "never`
- `components/MotiveOpsIntelPanel.jsx:52` · `F4·toLocaleString-bare` · `const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";`
- `components/MotiveDriverIntelPanel.jsx:125` · `F4·toLocaleString-bare` · `const when = ev.received_at ? new Date(ev.received_at).toLocaleString() : "—";`
- `components/IncidentLifecyclePanel.jsx:415` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/SiteInspectionLifecyclePanel.jsx:561` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/UndoLastTransitionButton.jsx:64` · `F4·toLocaleString-bare` · `const at = ev.at ? new Date(ev.at).toLocaleString() : "—";`
- `components/EquipmentMasterPanel.jsx:513` · `F4·toLocaleString-bare` · `{u.deleted_at ? new Date(u.deleted_at).toLocaleString() : "—"}`
- `components/AdminAccessControlPanel.jsx:279` · `F5·toLocaleDateString-bare` · `{u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "—"}`
- `components/QaqcLifecyclePanel.jsx:559` · `F4·toLocaleString-bare` · `{new Date(ev.at).toLocaleString()}`
- `components/admin/MappingCleanupTab.jsx:511` · `F5·toLocaleDateString-bare` · `{r.located_at ? new Date(r.located_at).toLocaleDateString() : "—"}`
- `components/oa/HistoryFeed.jsx:64` · `F4·toLocaleString-bare` · `<span className="font-mono">{new Date(e.at).toLocaleString()}</span>`
- `pages/HrEmployees.jsx:987` · `F4·toLocaleString-bare` · `<span className="text-slate-500">{new Date(h.at).toLocaleString()}</span>`
- `pages/ViewIncident.jsx:743` · `F4·toLocaleString-bare` · `{data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}`
- `pages/ViewInspection.jsx:483` · `F4·toLocaleString-bare` · `{t("Generated")} {data.created_at ? new Date(data.created_at).toLocaleString() :`
- `pages/HrEmployeeRequestsQueue.jsx:296` · `F4·toLocaleString-bare` · `{new Date(req.requested_at).toLocaleString()}`
- `pages/ViewDailyReport.jsx:682` · `F4·toLocaleString-bare` · `{data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}`
- `pages/JhaPlansHub.jsx:286` · `F5·toLocaleDateString-bare` · `? new Date(f.uploaded_at).toLocaleDateString()`
- `pages/admin/AdminIntegrationCenter.jsx:1446` · `F4·toLocaleString-bare` · `{g.last_activity_at ? new Date(g.last_activity_at).toLocaleString() : "—"}`
- `pages/admin/AdminJhaAcknowledgements.jsx:161` · `F4·toLocaleString-bare` · `? new Date(row.latest_acknowledged_at).toLocaleString()`
- `pages/admin/AdminJhaAcknowledgements.jsx:242` · `F4·toLocaleString-bare` · `? new Date(row.file.uploaded_at).toLocaleString()`

_…and 9 more (see JSON output)._

## How to clear violations

1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.
2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. If a legacy line is reviewed and accepted as-is, add its
   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.

Run `python3 scripts/timestamp_doctrine_probe.py --bless` to
regenerate the baseline after a fix sweep.
