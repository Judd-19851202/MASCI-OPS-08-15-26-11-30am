# TRACK 23.1 — ELITE V1 DAILY REPORT REBUILD

**Status:** 🟢 SHIPPED · CERTIFIED (2026-02-06)
**Certification:** 41/41 backend + 9/9 frontend + testing agent verdict `retest_needed=false`.
**Scope discipline:** V1 shell untouched. Only additive backend endpoints + new frontend files. Zero schema deletion. Same submit endpoint. Same downstream.

---

## Executive verdict

The V3 Daily Report is a **parallel React shell** at `/daily/new` behind a five-scope feature flag (`ui_flags.dr_v3`). The flag ONLY controls which shell renders. All backend endpoints, payload contract, ODS emit, Trust Spine, notifications, email dispatch, PDF, RBAC, idempotency, and downstream consumers are **byte-identical** to before this track — verified by re-running Track 22.9A / 22.9B / DR-CUTOVER-001 / DR-CUTOVER-002 test suites.

Rollback = one flag flip in `ui_flags.dr_v3.tenant_default`. No git revert. No emergency deploy. No database restore.

## What shipped

### Backend (additive only)

- **`services/cost_codes/provider.py`** — `CostCodeProvider` abstract base + `JobsMasterCostCodeProvider` (default). Registry lets future adapters (Vista, Foundation, HCSS, Spectrum, Sage, CSV import) plug in without touching UI or business logic. Env selector: `COST_CODE_PROVIDER=jobs_master` (default).
- **`routes/cost_codes.py`** — `GET /api/cost-codes/for-project?project_number=…` → `{codes:[…], count, provider}`. Empty ⇒ UI hides selector.
- **`routes/ui_flags.py`** — `resolve_dr_v3_flag()` implements five-scope priority: admin_override → pilot_user → pilot_project → denied_user → tenant_default. `GET /api/feature-flags/dr-v3`.
- **`server.py`** — registered both routers next to the existing `dr_v2_photos` registration line.

### Frontend (parallel component)

- **`pages/NewDailyReportV3.jsx`** — 9-section shell that composes existing shared primitives (JobPicker, FlUserCombo, EmployeeCombo, EquipmentCombo, SupplierCombo, PhotoUpload, SignaturePad, DailySummaryAssist). Submits via `api.post("/daily-reports", payload)` — the same canonical endpoint V1 uses.
- **`pages/DailyReportRouter.jsx`** — flag-gated wrapper. Renders V1 by default (fail-closed on error).
- **`components/daily-report-v3/SectionProjectConditions.jsx`** — Section 01 (job picker + GPS + weather).
- **`components/daily-report-v3/sections.jsx`** — Sections 02-09 + `CostCodePicker` (returns `null` when `options.length === 0`).
- **`lib/dailyReportV3Flag.js`** — `useDailyReportV3Flag` hook.
- **`app/routing/AppRoutes.jsx`** — `/daily/new` and `/daily/submit` now route through `DailyReportRouter`.

### The 9 sections

1. **Project + Conditions** — Where were we?
2. **Crew + Equipment** — Who was there?
3. **Work Performed + Production** — What got done?
4. **Materials + Tickets** — What moved?
5. **Photos + Evidence** — What can we prove?
6. **Delays / Extra Work + Safety** — What impacted today? (combined gates — single Yes/No per topic)
7. **Tomorrow + PM Attention** — What's next?
8. **Operational Summary Assist** — Single AI card (Track 22.9A `DailySummaryAssist`, no duplicate).
9. **Submit Readiness + Sign-Off** — Live readiness pill + gated Submit.

## Doctrine compliance

- ✅ **No V2 name** — enforced by `test_v3_shell_never_names_v2`.
- ✅ **Single AI card** — `DailyOperationalSummarySection` explicitly absent from V3 (locked).
- ✅ **Same backend endpoint** — `api.post("/daily-reports", …)` — locked.
- ✅ **Dropdown-first** — EmployeeCombo, EquipmentCombo, SupplierCombo, FlUserCombo, JobPicker composed — locked.
- ✅ **Cost-code hidden when absent** — `CostCodePicker` returns `null` — locked and re-verified live.
- ✅ **Combined gates** — one impact question + one safety question — locked.
- ✅ **Photo minimum preserved** — `photoMin=6` default — locked.
- ✅ **Signature required** — `SignaturePad` gates submit — locked.
- ✅ **AI never blocks submit** — DailySummaryAssist is optional and non-blocking (same wiring as Track 22.9A).
- ✅ **Test-id prefix** — every V3 testid starts with `dr-v3-` — locked.
- ✅ **Flag never controls backend** — UI-only wrapper (`DailyReportRouter`) — locked.

## Cost Code Provider abstraction

Today: `JobsMasterCostCodeProvider` reads `jobs_master.cost_codes[]`.
Tomorrow: register any subclass. Example future adapter:

```python
class VistaCostCodeProvider(CostCodeProvider):
    name = "vista"
    async def list_for_project(self, project_number: str) -> List[CostCode]:
        # Call Vista API; normalize to {code, description, active}.
        ...

register_provider("vista", VistaCostCodeProvider)
# Set COST_CODE_PROVIDER=vista in env. Zero UI change.
```

## Test envelope

- **`test_track_23_1_cost_code_provider.py`** — provider contract, singleton, registry, filtering, dedup, sort, case-insensitivity, unknown-provider fallback.
- **`test_track_23_1_ui_flag_resolver.py`** — five-scope priority, case-insensitive email, missing flag doc, env default.
- **`test_track_23_1_v3_ui_shape.py`** — nine sections composed, canonical submit endpoint, no V2 name, single AI card, cost-code hides when empty, router wraps at /daily/new, dropdown-first primitives, combined gates, testid prefix.
- **`test_track_23_1_live_api.py`** (created by testing agent) — 8 live API assertions.

## Rollout runbook

- **Pilot**: `db.ui_flags.updateOne({_id:"dr_v3"}, {$addToSet:{pilot_users:"pilot@masci.com"}}, {upsert:true})`.
- **Pilot a project**: `db.ui_flags.updateOne({_id:"dr_v3"}, {$addToSet:{pilot_projects:"25-21"}}, {upsert:true})`.
- **Tenant flip**: `db.ui_flags.updateOne({_id:"dr_v3"}, {$set:{tenant_default:true}}, {upsert:true})`.
- **Emergency rollback**: `db.ui_flags.updateOne({_id:"dr_v3"}, {$set:{tenant_default:false, pilot_users:[], pilot_projects:[]}}, {upsert:true})` — every operator returns to V1 on next page load.
- **Admin URL override** (support only): append `?dr_v3=1` to `/daily/new`.

## Downstream compatibility snapshot (re-verified)

| Consumer | Status | Evidence |
|---|---|---|
| PM Command Center | ✅ unchanged | V3 posts to `/api/daily-reports` — same `daily_reports` collection reads |
| Admin dashboards | ✅ unchanged | same |
| HR Daily Reports | ✅ unchanged | same |
| Safety Portal | ✅ unchanged | same |
| Shop / Dispatch | ✅ unchanged | same |
| ODS Facts (6 types) | ✅ unchanged | `ingest_dr_v1_report` still fires from POST handler |
| Trust Spine | ✅ unchanged | `emit_record_created` still fires |
| PM auto-email | ✅ unchanged | `schedule_auto_email('daily-report', doc)` still fires |
| Bell notifications | ✅ unchanged | same |
| Idempotency | ✅ unchanged | `with_idempotency` wraps `_do_create` (V1 flow) |
| Photo intelligence (22.9B) | ✅ unchanged | same enqueue + reconciler |
| PDF renderer | ✅ unchanged (still doesn't read `ai_accepted_summary` — 22.9C target) |
| CSV export | ✅ unchanged | same |
| Historical reports | ✅ unchanged | schema not modified |

## Deferred to next tracks

- **🔵 Track 22.9C** — PDF/email/PM screen read of `ai_accepted_summary` + photo observations. Highest-value remaining ROI gap.
- **🟡 Track 23.2** — Admin UI for `jobs_master.cost_codes[]` seeding (today codes are seeded via Mongo directly or API).
- **🟡 Track 23.3** — Migrate the remaining V1-only affordances (Smart Prefill, Crew Setup Restore, Draft Restore/Archive prompts, offline queue integration) into the V3 shell. Currently V3 shell submits online-first; V1 remains the "safe" shell for operators who need the resiliency stack.
- **🟡 Track 23.4** — Wire the pilot expansion (Admin UI to add pilot_users / pilot_projects without direct Mongo access).
