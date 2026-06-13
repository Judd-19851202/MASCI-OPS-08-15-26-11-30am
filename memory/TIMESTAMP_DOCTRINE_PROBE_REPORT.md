# Timestamp Doctrine Probe Report

_Phase TRUST-TIME-1B · self-protection probe · 🔴 FAIL_

- Scanned files     : **1000**
- Patterns           : **5**
- New violations     : **11**
- New warnings       : **26**
- Baselined          : **104**
- Scan runtime       : **170 ms**

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
- `pages/OperationsCenterCommand.jsx:482` · `F1·slice16-replaceT` · `<span className="font-mono text-[10.5px] text-slate-500">{String(ev.timestamp ||` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:165` · `F1·slice16-replaceT` · `<Field label="Started"          value={(a.started_at || "").slice(0,16).replace(` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:188` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(x.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:425` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(p.created_at || p.dat` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:453` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.event_at || e.recei` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js
- `pages/admin/AssetProfile.jsx:472` · `F1·slice16-replaceT` · `<span className="font-mono text-slate-500 w-32 shrink-0">{(e.created_at || "").s` → Use formatLocalDateTime() or formatLocalShort() from lib/dateUtils.js

## · New warnings (review · not deploy-blocking)

- `components/triage/FocusBanner.jsx:263` · `F4·toLocaleString-bare` · `r.reported_at ? `Reported ${new Date(r.reported_at).toLocaleString()}` : null,`
- `components/triage/FocusBanner.jsx:294` · `F4·toLocaleString-bare` · `r.shift_start_at ? `Shift start: ${new Date(r.shift_start_at).toLocaleString()}``
- `components/pm/command/PmProjectFirstHome.jsx:311` · `F5·toLocaleDateString-bare` · `{d.created_at ? new Date(d.created_at).toLocaleDateString() : ""}`
- `lib/resiliency/DraftStatusPill.jsx:36` · `F4·toLocaleString-bare` · `return new Date(ts).toLocaleString();`
- `pages/FleetVisibility.jsx:183` · `F4·toLocaleString-bare` · `{e.timestamp ? new Date(e.timestamp).toLocaleString() : ""}`
- `pages/FleetVisibility.jsx:223` · `F4·toLocaleString-bare` · `? new Date(group.latest_inspection_at).toLocaleString()`
- `pages/FleetVisibility.jsx:317` · `F4·toLocaleString-bare` · `{d.repaired_at && ` · ${new Date(d.repaired_at).toLocaleString()}`}`
- `pages/FleetVisibility.jsx:338` · `F4·toLocaleString-bare` · `{new Date(d.reported_at).toLocaleString()}`
- `pages/shop/FuelLubeVisitRecords.jsx:157` · `F4·toLocaleString-bare` · `submitted {v.submitted_at ? new Date(v.submitted_at).toLocaleString() : "—"}`
- `pages/shop/ServiceTruckReconciliationDetail.jsx:112` · `F4·toLocaleString-bare` · `<div>Start submitted: <strong>{doc.start_submitted_at ? new Date(doc.start_submi`
- `pages/shop/ServiceTruckReconciliationDetail.jsx:113` · `F4·toLocaleString-bare` · `<div>End submitted: <strong>{doc.end_submitted_at ? new Date(doc.end_submitted_a`
- `pages/shop/ServiceTruckReconciliationDetail.jsx:114` · `F4·toLocaleString-bare` · `<div>Reviewed by: <strong>{doc.reviewed_by || "—"}</strong>{doc.reviewed_at ? ` `
- `pages/shop/ShopManagerQueue.jsx:181` · `F4·toLocaleString-bare` · `const reportedAt = defect.reported_at ? new Date(defect.reported_at).toLocaleStr`
- `pages/shop/ShopManagerQueue.jsx:182` · `F4·toLocaleString-bare` · `const assignedAt = defect.assigned_at ? new Date(defect.assigned_at).toLocaleStr`
- `pages/shop/ShopManagerQueue.jsx:183` · `F4·toLocaleString-bare` · `const startedAt = defect.repair_started_at ? new Date(defect.repair_started_at).`
- `pages/shop/ShopManagerQueue.jsx:184` · `F4·toLocaleString-bare` · `const completedAt = defect.repaired_at ? new Date(defect.repaired_at).toLocaleSt`
- `pages/shop/ShopMyAssignments.jsx:51` · `F4·toLocaleString-bare` · `const reportedAt = defect.reported_at ? new Date(defect.reported_at).toLocaleStr`
- `pages/shop/ShopMyAssignments.jsx:52` · `F4·toLocaleString-bare` · `const acceptedAt = defect.accepted_at ? new Date(defect.accepted_at).toLocaleStr`
- `pages/shop/ShopMyAssignments.jsx:53` · `F4·toLocaleString-bare` · `const startedAt = defect.repair_started_at ? new Date(defect.repair_started_at).`
- `pages/shop/ShopMyAssignments.jsx:54` · `F4·toLocaleString-bare` · `const completedAt = defect.repaired_at ? new Date(defect.repaired_at).toLocaleSt`
- `pages/shop/UnitHistoryTimeline.jsx:96` · `F4·toLocaleString-bare` · `try { return new Date(iso).toLocaleString(); } catch { return iso; }`
- `pages/shop/ServiceTruckReconciliationRecords.jsx:174` · `F4·toLocaleString-bare` · `start submitted {row.start_submitted_at ? new Date(row.start_submitted_at).toLoc`
- `pages/shop/ServiceTruckReconciliationRecords.jsx:175` · `F4·toLocaleString-bare` · `end submitted {row.end_submitted_at ? new Date(row.end_submitted_at).toLocaleStr`
- `pages/shop/FuelLubeVisitDetail.jsx:73` · `F4·toLocaleString-bare` · `<div>Submitted at: <strong>{visit.submitted_at ? new Date(visit.submitted_at).to`
- `pages/admin/AssetProfile.jsx:296` · `F4·toLocaleString-bare` · `<Tile label="Last Seen" testid="ap-motive-located" value={live.located_at ? new `
- `pages/admin/AssetProfile.jsx:330` · `F4·toLocaleString-bare` · `{operator.as_of ? <> · <span className="font-mono">{new Date(operator.as_of).toL`

## How to clear violations

1. Replace ad-hoc rendering with helpers from `lib/dateUtils.js`.
2. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.
3. If a legacy line is reviewed and accepted as-is, add its
   `path::pattern_id::line` key to `scripts/timestamp_pattern_baseline.json`.

Run `python3 scripts/timestamp_doctrine_probe.py --bless` to
regenerate the baseline after a fix sweep.
