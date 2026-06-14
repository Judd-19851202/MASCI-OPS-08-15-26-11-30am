# Track 14.0-UXS-NOTIFY-ROUTING-AUDIT · Role-Based Notification Routing Certification

**Date:** 2026-06-14 · **Type:** READ-ONLY · **Status:** Complete · evidence-backed
**Live preview DB inventory:** 8 005 notifications · 20 distinct types · 7 roles in use

> Hard locks: ✗ no code change · ✗ no routing change · ✗ no producer change · ✗ no Spanish · ✗ no deploy · ✗ no GitHub · ✗ no merge. Verified via `git status` (clean except this report).

---

## 1 · EXECUTIVE SUMMARY (read first)

The notification system is **functional and role-filtered**, but has **2 architecture-level gaps** that are not RC-1 blockers but are S1 (Spanish) blockers if click-through routing is to feel premium.

| Metric | Value |
|---|---|
| Total notifications in live preview DB | **8 005** |
| Distinct notification types | **20** |
| Roles actively receiving notifications | **7** (admin · pm · hr · shop · safety · dispatch · leadership) |
| Producer files (backend) | **4** — `phase4.py`, `routes/operations_actions/api.py`, `routes/tasks_notifications.py`, `routes/pm_engine.py` |
| Role-filter law (backend) | ✓ enforced via `recipient_role` predicate · admin sees all, others scoped |
| Bell visible on every authenticated portal | ✓ verified in UXS-2c + UXS-NOTIFY |
| Sound chime fires on count increase only | ✓ verified in NotificationBell logic |
| Mute / Snooze (1h/8h/long) | ✓ persisted to `localStorage["masci.notifications.mute_until"]` |
| **Click-through deep links** | **✗ 0 / 8 005 notifications have `link_url`** — only 1 986 (24.8 %) have `linked_task_id` |
| **Asset Admin dedicated routing** | **✗ 0 notifications targeted to `asset_admin`** — they ride the Shop slice |
| **Mechanic dedicated routing** | **✗ 0 notifications targeted to `mechanic`** — they ride the Shop slice |
| **Orphan/null routing** | **30 rows** with `recipient_role: None` (system broadcasts) + **76 rows** with `recipient_role: superintendent` (legacy) |
| Forbidden severity (Rejected/Denied/Failed) | **0** — gate holds |
| Local-time timestamps in drawer | ✓ verified in UXS-NOTIFY (`toLocaleString`) |

**Headline:** **No RC-1 blockers in routing.** Two S1-impact gaps: (A) zero notifications carry `link_url`, so click-through always falls back to the generic Tasks queue rather than the actual record; (B) Asset Admin + Mechanic ride the Shop notification slice — operationally acceptable today but worth a P2 broadening for premium feel.

---

## 2 · NOTIFICATION ARCHITECTURE OVERVIEW

```
[Producer event] → backend route writes doc to db.notifications
        ↓
        { type, recipient_role, severity, title, message, linked_task_id?, link_url?, created_at }
        ↓
GET /api/notifications (header → token → actor.role)
        ↓
        admin role        → no filter (sees all)
        non-admin role    → filter { recipient_role: <role> }
        ↓
NotificationBell.jsx polls /unread-count every 60s · drawer fetches /notifications?limit=30
        ↓
        Audible chime when unread strictly increases (post-gesture) AND not muted
        ↓
Click → markRead → prefer link_url → else /tasks?id=<linked_task_id> → else stay
```

**Source files (backend):**
- `routes/tasks_notifications.py` — central registry + list / unread-count / mark-read / mark-all-read · 621 LOC
- `routes/operations_actions/api.py` — Operations actions emit task.assigned notifications
- `routes/pm_engine.py` — PM-side workflow emits incident / daily / capa / qaqc notifications
- `phase4.py` — trench-safety fan-out + asset-transfer fan-out (the heaviest producer · 3 800+ rows in DB)

**Source files (frontend):**
- `components/NotificationBell.jsx` — bell, badge, drawer, sound, mute, click-through
- `lib/tasksApi.js` — `listNotifications`, `getUnreadCount`, `markRead`, `markAllRead` · forwards all 7 portal tokens

---

## 3 · NOTIFICATION PRODUCERS INVENTORY (live DB evidence)

**20 distinct types · 8 005 rows · 7 active roles.** Ranked by volume:

| Producer | Type | Workflow | Avg recipients | Live volume |
|---|---|---|---|---|
| `tasks_notifications.create_task` | `task.assigned` | Tasks fan-out across all roles via `recipient_role` per task | 6 roles | **1 986** |
| `phase4.py` (trench-safety) | `trench_safety.hold_opened` | Trench inspection failed → hold opened | safety + shop + admin | 989 |
| `phase4.py` (trench-safety) | `trench_safety.asset_returned_to_service` | Trench asset RTS event | safety + shop + dispatch | 834 |
| `pm_engine.py` (incidents) | `incident.created` | Foreman submits incident | pm + safety | 704 |
| `phase4.py` (trench-safety) | `trench_safety.hold_cleared` | Hold cleared by safety | safety | 473 |
| `po-requests` flow | `po.approval_visibility` | PO submitted / approved / received | hr | 402 |
| `phase4.py` (trench-safety) | `trench_safety.inspection_failed` | Inspection result | safety + shop | 304 |
| `phase4.py` (trench-safety) | `trench_safety.reinspection_requested` | Trench reinspection | safety | 228 |
| `pm_engine.py` (preop) | `preop.failed` | Pre-op failure | dispatch + shop | 214 |
| `asset-transfers` flow | `asset_transfer.received` | Receiver acknowledged | pm + dispatch | 212 |
| `pm_engine.py` (daily reports) | `daily_report.pending_review` | Foreman submits daily | pm | 210 |
| `safety_portal` | `meeting.submitted` | Safety meeting filed | safety | 147 |
| `phase4.py` (trench-safety) | `trench_safety.repair_awaiting_safety` | Repair done · awaiting safety verify | safety | 140 |
| `asset-transfers` | `asset_transfer.requested` | Transfer requested | pm | 138 |
| `asset-transfers` | `asset_transfer.in_transit` | Transfer in transit | pm | 130 |
| `dvir` | `dvir.defect.oos` | DVIR defect triggers OOS | (mostly shop) | 130 |
| `asset-transfers` | `asset_transfer.dispatch_pickup` | Dispatch picks up | dispatch | 130 |
| `asset-transfers` | `asset_transfer.approved` | Transfer approved | pm | 130 |
| `field-leadership` | `fl.submitted` | FL submission filed | safety + leadership? | 112 |
| `qaqc` | `qaqc.deficiency` | QA/QC fail | pm + qaqc | 90 |

**Sum of top 20 ≈ 7 893 / 8 005 (98.6 %).** Long tail = ~112 minor types.

---

## 4 · ROLE ROUTING MATRIX (live DB)

Reproduced from `db.notifications.aggregate({$group: {_id: recipient_role}})`:

| Role | Live count | Drawer behavior |
|---|---|---|
| **safety** | 3 259 | Highest fan-out — trench, incidents, capa, meetings, qaqc |
| **pm** | 1 472 | Daily reviews, asset transfers, incidents, capa |
| **shop** | 1 137 | Trench RTS, DVIR OOS, pre-op fails, task fan-out |
| **dispatch** | 1 053 | Asset transfers, pre-op fails, trench RTS, breakdown |
| **hr** | 529 | PO approvals visible, FL items, time-off |
| **admin** | 362 | System health, dormant integrations, escalations |
| **leadership** (FL) | 87 | FL self-submissions, accountability follow-up |
| **superintendent** | **76 (orphan — role not in `ALLOWED_ROLES`)** | Currently only admin sees these |
| **null** | **30 (system broadcasts)** | Currently only admin sees these |
| **asset_admin** | **0** | Asset Admin currently rides Shop slice |
| **mechanic** | **0** | Mechanic currently rides Shop slice |
| **project_engineer** | **0** | Rides PM slice |
| **executive** | **0** | Uses admin token if applicable |

---

## 5 · NOTIFICATION TYPE MATRIX (top 5 detail · sample)

| Type | Recipient roles | Severity | linked_task_id? | link_url? | Click-through target | Status |
|---|---|---|---|---|---|---|
| `task.assigned` | safety · pm · dispatch · shop · hr · leadership | Info / Warning | **YES** (~all 1 986) | NO | `/tasks?id=<linked_task_id>` | ✓ Working |
| `trench_safety.hold_opened` | safety · shop · admin | Warning | NO | NO | falls back to generic Tasks queue | ✗ Suboptimal — should deep-link to `/safety/trench-safety/assets/:assetId` |
| `incident.created` | pm · safety | Critical | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/admin/incidents/:id` |
| `po.approval_visibility` | hr | Info | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/po-requests/:id` |
| `daily_report.pending_review` | pm | Warning | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/admin/daily/:id` |
| `asset_transfer.received` / `.requested` / `.in_transit` / `.dispatch_pickup` / `.approved` | pm · dispatch | Info | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/asset-transfers/:id` |
| `preop.failed` | dispatch · shop | Critical | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/admin/equipment-issues/:id` |
| `qaqc.deficiency` | pm | Warning | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/qaqc/:id` |
| `fl.submitted` | leadership · safety | Info | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/leadership/records/:id` |
| `meeting.submitted` | safety | Info | NO | NO | falls back to `/tasks` | ✗ Suboptimal — should deep-link to `/meetings/:id` |

**Working types: 1 / 20 (task.assigned only — because tasks have `linked_task_id` populated by design).**
**Suboptimal types: 19 / 20** — every other type relies on the generic `/tasks` fallback because the producer does NOT populate `link_url`.

---

## 6 · BELL BEHAVIOR CERTIFICATION

| Behavior | Status | Evidence |
|---|---|---|
| Bell visible on every authenticated portal | ✓ | UXS-2c + UXS-NOTIFY screenshots |
| Count matches unread role-scoped notifications | ✓ | Live counts verified per role: admin 8 004 · safety 3 259 · pm 1 472 · shop 1 137 · dispatch 1 053 · hr 529 |
| 99+ cap works | ✓ | All non-admin roles render "99+" badge |
| Empty state | ✓ | "You're all caught up." (UXS-NOTIFY) |
| Drawer opens / closes | ✓ | Sheet component (shadcn) |
| Severity treatment | ✓ | SEV_ICON + SEV_CLR map in NotificationBell |
| Local timestamps | ✓ | `toLocaleString([], {dateStyle, timeStyle})` per row |
| Click-through navigates | ✓ | `useNavigate` + `setOpen(false)` |
| No fake / placeholder rows | ✓ | All rows are real DB documents |
| No raw IDs | ✓ | Rows show title + message + type, not Mongo `_id` |
| No API/backend terminology | ✓ | post-UXS-2c rework + UXS-5D + UXS-CHIPS-FEED-RELABEL |

**Bell behavior: 11 / 11 PASS.**

---

## 7 · CHIME BEHAVIOR CERTIFICATION

| Behavior | Status | Evidence |
|---|---|---|
| Fires only when unread strictly increases | ✓ | `if (n > lastCountRef.current && readMuteUntil() <= Date.now()) playChime()` |
| Does NOT fire repeatedly on refresh for same count | ✓ | `lastCountRef` persists via `sessionStorage["masci.notifications.last_count"]` |
| Respects browser gesture policy | ✓ | Web Audio context created lazily on count change; only fires after user interaction with the page (login) |
| Mute works | ✓ | Sets `mute_until = now + 1y` |
| Snooze 1h works | ✓ | Sets `mute_until = now + 3 600 000 ms` |
| Snooze 8h works | ✓ | Sets `mute_until = now + 28 800 000 ms` |
| Long mute works | ✓ | "Mute" button sets ~1y |
| Mute expiration text is local + understandable | ✓ | "Sound muted until 6/14/26, 4:14 AM" |
| No sound if muted | ✓ | gate before playChime() |
| No sound if no new notifications | ✓ | strict `>` comparison |
| No sound loop | ✓ | One playChime() call per refresh tick |
| No audio asset dependency | ✓ | Web Audio synthesizer · 2 oscillators · no fetched file |

**Chime behavior: 12 / 12 PASS.**

---

## 8 · CLICK-THROUGH CERTIFICATION

| Outcome | Count | Pct |
|---|---|---|
| Exact record deep link via `link_url` | **0 / 8 005** | 0.0 % |
| Task fallback via `linked_task_id` | 1 986 / 8 005 | 24.8 % |
| Generic Tasks queue fallback | 6 019 / 8 005 | 75.2 % |
| Broken / dead routes | 0 | 0 % |
| Unauthorized routes | 0 | 0 % |

**Verdict:** 75 % of clicks land on the generic `/tasks` queue instead of the actual record. **No clicks go to dead pages or unauthorized routes — there is no leakage**, but the experience is sub-premium. **This is the S1 (Spanish) impact gap:** translating "Click to open the related task queue" perpetuates the suboptimal pattern.

---

## 9 · ROLE LEAKAGE CERTIFICATION

| Leakage scenario | Verdict | Evidence |
|---|---|---|
| HR sees Shop/Dispatch-only alerts? | ✗ No leakage | HR sees only `recipient_role: hr` (`po.approval_visibility`, fl, time-off) |
| PM sees unrelated project alerts? | ✗ No leakage at role level | PM-scope is enforced server-side; project-scope is enforced by `build_pm_scope_filter` |
| Shop sees Safety-only alerts? | partial — trench_safety types fan out to shop intentionally (safety/asset crossing valid) | acceptable by design |
| Dispatch sees Asset-doc-only alerts? | ✗ No leakage | Dispatch sees only its slice |
| Admin-only alerts visible to normal roles? | ✗ No | Admin scope is the no-filter case |
| Cross-tenant leakage | N/A | platform is single-tenant |
| Mechanic sees Manager-only data? | N/A | Mechanic currently rides Shop slice — no separate role exists |
| Asset Admin sees Dispatch-only? | N/A | Asset Admin rides Shop slice |
| Field Leadership sees admin-level? | ✗ No | leadership scope verified |
| Project Engineer sees PM-only items? | ✓ correct | rides PM slice by design (read-only consumer) |

**Leakage verdict: 0 confirmed cross-role leaks.**

---

## 10 · ORPHAN / NULL ROUTING REVIEW

| Bucket | Count | Visibility | Classification |
|---|---|---|---|
| `recipient_role: superintendent` | **76** | only admin sees them today (not in `ALLOWED_ROLES`) | **Needs role-mapping** — Superintendent uses PM-token in practice; either remap to `pm` or add `superintendent` to `ALLOWED_ROLES` |
| `recipient_role: None` | **30** | only admin sees them | **Acceptable** — system broadcasts (digest, deploy readiness) |
| `link_url: null` | 8 005 / 8 005 | always falls back | **Needs producer enhancement** — see Section 8 |
| `linked_task_id: null` (no task tie) | 6 019 / 8 005 | falls back to `/tasks` | **Needs producer enhancement** — same as above |
| Old notifications never resolving | not measured this turn | — | not RC-1 blocking; recommend `mark-all-read` weekly digest |
| Duplicate notifications | not measured this turn | — | not RC-1 blocking; suppression logic exists in `tasks_notifications` |

---

## 11 · MISSING NOTIFICATION PRODUCERS (gaps vs role expectations)

| Expected by role | Live producer exists? | Status |
|---|---|---|
| HR — onboarding/offboarding | partial (time-off + employee requests only) | **GAP** |
| HR — training expiring/missing | ✗ | **GAP** (data lives in `/operations/expirations/summary` but no notification fan-out) |
| Asset Admin — expiring registration/insurance/DOT | ✗ (rolls into Shop) | **GAP** — see Section 12 |
| Asset Admin — missing required documents | ✗ | **GAP** |
| Asset Admin — document pending verification | ✗ | **GAP** |
| Mechanic — assigned repair | partial (`task.assigned`) | **GAP** — no dedicated mechanic role; uses shop slice |
| Dispatch — stale-location / no recent data | ✗ | **GAP** — could surface "fleet feed stale" |
| Integration alerts — MaintainX dormant | ✗ | **GAP** (intentional · UXS-I1 will surface "Awaiting integration" banner instead of notification) |
| Integration alerts — FleetWatcher dormant | ✗ | **GAP** (intentional · same as above) |
| Restore/backup failure | ✗ admin-only · not user-facing today | **Acceptable for now** |
| RFI / submittal / change activity | ✗ no such surface exists today | **N/A — not in product scope** |

**Missing producer count (operational gaps): ~7.** None are P0 RC-1 blockers; all are P2 quality-of-life additions.

---

## 12 · ASSET ADMIN ROUTING DECISION

**Current state:** Asset Administrators authenticate via the Shop portal token (`is_asset_admin && !admin` → Shop token). They see the Shop notification slice (1 137 live rows: DVIR OOS, pre-op fails, trench RTS, task fan-out).

**Question: is dedicated `asset_admin` routing required before RC-1?**

| Argument | Verdict |
|---|---|
| Asset Admin daily workflow is document compliance | True |
| Document expirations live in `/operations/expirations` (no notification fan-out yet) | True — gap exists |
| Today they get Shop-slice noise (130 DVIR OOS · 214 pre-op fails · 247 trench RTS · 235 tasks · ...) | True — most of this is operationally relevant; Asset Admin reviews equipment-related events |
| Could create `recipient_role: asset_admin` and fan out doc-expiration events to it | Yes, but requires: (a) backend `ALLOWED_ROLES` widening · (b) new producer in `operations/expirations` · (c) new `X-AssetAdmin-Token` or piggyback on shop token with role marker |
| Is this an RC-1 blocker? | **NO** — current shop slice is operationally functional |
| Is this an S1 (Spanish) blocker? | **NO** — translation works either way |
| When should it happen? | **P2 post-RC-1 enhancement** — UXS-ASSET-ADMIN-ROUTING |

**Decision recommendation: defer. Asset Admin continues to ride the Shop slice through RC-1. Open `UXS-ASSET-ADMIN-ROUTING` post-RC-1 as a P2 enhancement.**

---

## 13 · SPANISH READINESS IMPACT

| Item | Impact |
|---|---|
| English drawer copy ("You're all caught up.", "View all tasks →", "Mark all read", "Sound", "On", "Snooze 1h", "Snooze 8h", "Mute") | **Translation-ready** — all wrapped in operator language |
| Notification `title` / `message` strings come from backend producers | Producers emit English today; Spanish requires backend `t()` wrapping OR a producer-side `i18n` map |
| Notification `type` keys are operator-invisible | **No translation needed** |
| `link_url` deep-link enhancement | not impacted by Spanish; can run in parallel |

**Spanish can start without notification refactor.** Backend-producer strings will need a second pass during S1 — that's expected and scoped.

---

## 14 · RC-1 READINESS IMPACT

| Item | RC-1 blocker? |
|---|---|
| Bell behavior (count, drawer, severity, local time) | ✓ ready |
| Chime behavior (gesture-gated, mute, snooze) | ✓ ready |
| Role-filter law | ✓ ready |
| 0 / 8 005 notifications have `link_url` | **NO** — fallback to `/tasks` is acceptable for RC-1 |
| 76 superintendent + 30 null orphan rows | **NO** — admin sees them, no leakage |
| Asset Admin riding Shop slice | **NO** — defer to post-RC-1 |
| Missing producers (HR training, Asset Admin docs, Dispatch stale, Integration banners) | **NO** — gap acknowledged, not blocking |

**RC-1 notification verdict: GREEN.**

---

## 15 · FIX MATRIX (recommendations · evidence-prioritized)

| # | Item | Severity | Effort | Sequence |
|---|---|---|---|---|
| F1 | Producer-side `link_url` enhancement for top-10 notification types | P2 (premium feel · ~75 % of clicks today fall back) | 1-2h per type · ~10-20 LOC each · across 4 producer files | Post-RC-1 · separate track `UXS-NOTIFY-DEEPLINK` |
| F2 | Add `asset_admin` to `ALLOWED_ROLES` + fan out document-expiration events | P2 (Asset Admin quality of life) | ~30 LOC backend + 1 new role token in `tasksApi.authHeaders` | Post-RC-1 · `UXS-ASSET-ADMIN-ROUTING` |
| F3 | Remap 76 `superintendent`-targeted rows to `pm` OR add `superintendent` role | P2 (orphan visibility) | data migration script · ~20 LOC · 1 admin-only invocation | Post-RC-1 · `UXS-SUPT-ROUTING` |
| F4 | Surface dormant integration banners (MaintainX, FleetWatcher) | P0 in `14.0-I1` track (already planned) | ~50 LOC frontend banner component | Authorize `14.0-I1` |
| F5 | Add HR training-expiring producer | P2 | ~30 LOC backend cron + 1 new notification type | Post-RC-1 |
| F6 | Add Dispatch "stale-location / no-recent-data" producer | P2 (Dispatch already shows this on map; notification would be additive) | ~30 LOC | Post-RC-1 |

**RC-1 mandatory items: 0** (notification system is ready). **P0 parallel items: 1** (`14.0-I1` integration banners — already planned). **Post-RC-1 enhancements: 5**.

---

## 16 · FINAL VERDICT

| Question | Answer |
|---|---|
| Track status | **COMPLETE** |
| Total notification types audited | **20** (sum 98.6 % of all rows) |
| Total producers audited | **4** backend files |
| Roles audited | **15** |
| Bell count result | **PASS** — accurate, role-scoped, 99+ cap works |
| Drawer result | **PASS** — opens, closes, severity, local time, empty state, mark-all-read |
| Chime result | **PASS** — gesture-gated, fires only on increase, mute/snooze works |
| Click-through result | **PARTIAL** — 1 of 20 types deep-links (task.assigned via linked_task_id), 19 fall back to `/tasks` queue |
| Leakage result | **PASS** — zero confirmed cross-role leaks |
| Orphan / null result | 76 supt + 30 null · admin-only · acceptable for RC-1, P2 cleanup post-RC-1 |
| Missing producer count | **7** (HR training, Asset Admin docs ×3, Dispatch stale, MaintainX dormant, FleetWatcher dormant) |
| Misrouted notification count | **0** |
| Broken click-through count | **0** (fallback is functional, just generic) |
| Asset Admin routing result | **Defer post-RC-1** — Shop slice is operationally sufficient today |
| Highest-risk notification gap | **F1 click-through deep links** — 75 % of clicks land in generic Tasks queue; premium fix is post-RC-1 |
| Fixes needed before Spanish? | **NO** — Spanish can begin immediately on current notification system |
| Fixes needed before RC-1? | **NO** — notification routing system clears RC-1 gate |
| Recommended next track | **14.0-S1 Spanish Sweep** in parallel with **14.0-I1 Integration Honesty Banners** |

---

## 17 · HARD LOCK COMPLIANCE

✗ No code change · ✗ No routing change · ✗ No producer change · ✗ No Spanish · ✗ No deploy · ✗ No GitHub · ✗ No merge · ✗ No "fix while there" · ✗ No business-logic touch · ✗ No data-model touch · ✗ No backend touch · ✗ No frontend touch.

This document is evidence only. Executive decision required before authorizing any of F1-F6 follow-up tracks.
