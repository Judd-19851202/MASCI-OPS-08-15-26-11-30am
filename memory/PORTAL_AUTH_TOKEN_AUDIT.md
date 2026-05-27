# Portal Auth & Token Routing Audit

*Owner: platform integrity · iter437 / Phase IV-AUTH-FIX*
*Status: 🟢 P0 FIX SHIPPED · regression coverage in place*
*Last updated: 2026-02-27*

## 1. Why this audit exists

A manual preview review revealed PM-portal users clicking shared roster
pages (PM People, PM Suppliers, PM Equipment Fleet) saw an **"Admin login
required"** error toast and the page failed to render. The same risk
exists for any non-Admin shell that re-mounts panels originally built for
the Admin Hub.

Doctrine reminder (iter180 P0 · 2026-05-16):
> Every route under `/api/admin/*` is strict-admin. Shop, PM, HR, Safety,
> Dispatch, and Field-Leadership tokens are rejected on that namespace by
> design. There are no per-portal bypasses.

Frontend components that hardcode `/api/admin/*` endpoints therefore
cannot be mounted outside the Admin Hub without an Admin token leak.

## 2. Root cause

Shared list panels in `/app/frontend/src/components/` were originally
written for the Admin Hub and have their endpoints hard-coded:

| Shared panel | Hardcoded endpoint pattern |
|---|---|
| `EmployeeMasterPanel.jsx` | `/employees` (list) + 7 × `/admin/employees/*` |
| `SupplierMasterPanel.jsx` | `/suppliers` (list) + 7 × `/admin/suppliers/*` |
| `EquipmentMasterPanel.jsx` | `/equipment-master` (list) + 6 × `/admin/equipment-master/*` |
| `AdminJobMasterPanel.jsx` | `/admin/jobs/*` — 100% admin-namespaced |
| `EquipmentStatusBoard.jsx` | `/equipment-status-board` (admin-only gate) |
| `AutoEmailRoutingPanel.jsx` | `/auto-email/routing-table` (admin-only) |
| `ComplianceExportPanel.jsx` | `/exports/csv`, `/exports/summary`, `/exports/full-backup` (admin-only) |
| `TrainingStatsStripe.jsx` | `/admin/training/stats` |

`PmSections.jsx` re-mounted all of the above inside `PmShell`. The PM
axios interceptor attached `X-PM-Token` to every outbound call;
`require_admin` rejected each `/api/admin/*` call with `401 "Admin
login required"`; the global toast handler surfaced that message; PMs
were blocked from reading rosters they're entitled to read via the
public `listEndpoint`.

Backend gates are correct. The bug is exclusively in the frontend's
endpoint targeting.

## 3. Cross-portal scan results

### 3.1 PM Portal — `/pm/*`

| Sidebar entry | Panel(s) | Endpoint dependency | Required token | Verdict | Action taken |
|---|---|---|---|---|---|
| `/pm` Overview | `PmHub` (tile grid) | PM-scoped reads only | PM | ✓ Safe | None — kept as-is |
| `/pm/daily` | `DailyReportsDashboard` (shared) | `/daily-reports` (PM-scoped) | PM | ✓ Safe | Kept |
| `/pm/inspections` | `Dashboard` (shared) | `/inspections` (PM-scoped) | PM | ✓ Safe | Kept |
| `/pm/meetings` | `MeetingsDashboard` (shared) | `/meetings` (PM-scoped) | PM | ✓ Safe | Kept |
| `/pm/incidents` | `IncidentsDashboard` (shared) | `/incidents` (PM-scoped) | PM | ✓ Safe | Kept |
| `/pm/photos` | `JobPhotosLibrary` | `/job-photos/*` | PM | ✓ Safe | Kept |
| `/pm/field-leadership` | `PmFieldLeadership` | `/field-leadership/*` | PM | ✓ Safe | Kept |
| `/pm/fleet` | `EquipmentStatusBoard` ✗ + `EquipmentMasterPanel` + `EquipmentPartsPanel` | mixed | Admin (for status board) + PM (rest) | 🔴 Broken | **Removed EquipmentStatusBoard**. `EquipmentMasterPanel` now mounts with `readOnly` (skips `/admin/equipment-master/*`). `EquipmentPartsPanel` retained (PM-safe via `require_shop_or_admin`). |
| `/pm/people` | `EmployeeMasterPanel` | `/employees` + `/admin/employees/*` | Admin (status/CRUD) | 🔴 Broken | **`readOnly` prop added** — only the public `/employees` list endpoint is called. |
| `/pm/suppliers` | `SupplierMasterPanel` | `/suppliers` + `/admin/suppliers/*` | Admin (status/CRUD) | 🔴 Broken | **`readOnly` prop added** — only the public `/suppliers` list endpoint is called. |
| `/pm/posters` | `SitePostersPanel` + `TrainingStatsStripe` ✗ | mixed | Admin (training stats) | 🔴 Partial | **Removed TrainingStatsStripe** from PM mount. SitePostersPanel kept (no API calls). |
| `/pm/jobs` | `AdminJobMasterPanel` | 100% `/admin/jobs/*` | Admin-only | 🔴 Broken | **Route removed.** No read-only equivalent exists; PMs see their jobs through `PmHub` overview, `/pm/daily`, and `/po-requests`. Recommended owner: Admin. |
| `/pm/routing` | `AutoEmailRoutingPanel` | `/auto-email/routing-table` | Admin-only | 🔴 Broken | **Route removed.** Recommended owner: Admin (System & Communications). |
| `/pm/compliance-export` | `ComplianceExportPanel` | `/exports/csv`, `/exports/summary`, `/exports/full-backup` | Admin-only (+ admin-strict) | 🔴 Broken | **Route removed.** Recommended owner: Admin (compliance & audits). |
| `/pm/qaqc` | `PmQaqcList` | `/qaqc-inspections` (PM-scoped) | PM | ✓ Safe | Kept |
| `/pm/crew-compliance` | `PmCrewCompliance` | `/pm/crew-compliance/*` | PM | ✓ Safe | Kept |
| `/pm/jha-plans` | `JhaPlansAdmin` (shared) | `/job-hazard-plans` (public) | PM | ✓ Safe | Kept |
| `/pm/trench-boxes` | `TrenchBoxesAdmin` (shared) | `/trench-boxes` (public) | PM | ✓ Safe | Kept |
| `/pm/equipment` | `EquipmentDashboard` (shared) | `/equipment-inspections` (PM-scoped) | PM | ✓ Safe | Kept |

### 3.2 HR Portal — `/hr/*`

Scanned `pages/HrChangePassword.jsx`, `pages/HrDailyReports.jsx`,
`pages/HrTimeVerification.jsx`, and the HR portal layout
(`pages/hr/*` and HR-mounted components).

| Surface | Endpoint dependency | Verdict |
|---|---|---|
| HR hub tiles | `/hr/*` (HR-token gated) | ✓ Safe |
| HR Time Verification | `/api/hr/time-verification` | ✓ Safe |
| HR Daily Reports | `/api/hr/*` | ✓ Safe |
| HR Training Records | `/api/hr/training-records` | ✓ Safe |
| HR Field Leadership read | `/api/hr/field-leadership` | ✓ Safe |
| `pages/SafetyEmployeeProfiles.jsx` (shared with HR via multi-role read gate) | `/api/employees/*` | ✓ Safe |

HR does NOT mount any of the shared admin panels (Employee/Supplier/
Equipment master, Job master, ComplianceExport, AutoEmailRouting,
TrainingStats). No regression.

### 3.3 Safety Portal — `/safety-portal/*`

| Surface | Endpoint dependency | Verdict |
|---|---|---|
| `pages/SafetyDashboard.jsx`, `pages/SafetyDocuments.jsx`, etc. | `/api/safety-portal/*` (Safety-token gated) | ✓ Safe |
| Cross-portal reads (employees, documents, training) | `/api/employees`, `/api/safety-documents` (multi-role gate) | ✓ Safe |

Safety portal does NOT mount any of the audited shared admin panels.
No regression.

### 3.4 Dispatch Portal — `/dispatch-portal/*`

| Surface | Endpoint dependency | Verdict |
|---|---|---|
| `pages/DispatchHub.jsx`, `pages/DispatchBoard.jsx`, etc. | `/api/dispatch/*` (Dispatch-token gated) + `/api/operations/*` (multi-portal read) | ✓ Safe |

Dispatch does NOT mount any shared admin panels. No regression.

### 3.5 Shop Portal — `/shop`

| Surface | Endpoint dependency | Verdict |
|---|---|---|
| `pages/ShopHub.jsx` + sub-pages | `/api/equipment-inspections/*`, `/api/equipment-parts/*` (shop-or-admin gated, accepts Shop AND PM AND admin tokens by design) | ✓ Safe |

Shop does NOT mount the audited shared admin panels (EmployeeMaster,
SupplierMaster, etc.). No regression.

### 3.6 Field Leadership Portal — `/field-leadership/portal/*`

| Surface | Endpoint dependency | Verdict |
|---|---|---|
| `FieldLeadershipPortalDashboard.jsx`, `FieldLeadershipDriverQualification.jsx` | `/api/field-leadership/portal/*` (FL-token gated) | ✓ Safe |
| Cross-portal reads (driver-qualification, dispatch-today) | dedicated FL-portal proxy endpoints | ✓ Safe |

FL portal does NOT mount any shared admin panels. No regression.

### 3.7 `/admin/*` routes accessible to non-Admin tokens (defense-in-depth check)

These admin-shell routes are gated `AP(...)` (Admin OR PM) in
`App.js`. If their inner components call `/api/admin/*`, a PM landing
on those URLs will still see "Admin login required". These were NOT
the reported regression but are flagged here for follow-up.

| Route | Inner component | `/admin/*` calls | Verdict |
|---|---|---|---|
| `/admin/pnl` | `ProjectPnlPage` | `/admin/projects/list`, `/admin/projects/pnl` | 🟡 Will 401 PM. Backend uses `require_admin` which DOES accept PM tokens on non-`/admin/*` paths, but these ARE `/admin/*` paths so PM is denied. **Out of scope for this iteration** — `/admin/pnl` is a admin-namespaced URL; PMs should reach P&L via `PmHub` job tiles instead. Recommend moving inner endpoints to `/api/projects/pnl` (non-admin namespace) in a future pass. |
| `/admin/qaqc` | `AdminQaqcList` | `/admin/qaqc-inspections/export.csv` | 🟡 Same pattern as P&L. Non-admin tokens already cannot reach this route in normal flows; covered by future follow-up. |
| `/admin/inspections`, `/admin/meetings`, `/admin/daily-reports` | dashboards | `/inspections`, `/meetings`, `/daily-reports` (PM-scoped) | ✓ Safe |
| `/admin/jha-plans`, `/admin/trench-boxes`, `/admin/equipment` | shared dashboards | non-admin namespace | ✓ Safe |

### 3.8 Panels removed from PM, recommended owning surface

| Panel | Current endpoint dependency | Required token | PM-safe alt | Recommended owning portal |
|---|---|---|---|---|
| `AdminJobMasterPanel` | `/admin/jobs/*` (CRUD + bulk-replace) | Admin | None today | Admin (System Governance / Master Lists) |
| `EquipmentStatusBoard` | `/equipment-status-board` (`require_admin`) | Admin | None today | Admin (Fleet Operations) — could later be widened to `require_admin_or_dispatch_or_pm` if operationally desired |
| `AutoEmailRoutingPanel` | `/auto-email/routing-table` (`require_admin`) | Admin | None | Admin (System & Communications) |
| `ComplianceExportPanel` | `/exports/csv`, `/exports/summary` (`require_admin`), `/exports/full-backup` (`require_admin_strict`) | Admin / Admin-Strict | None | Admin (Compliance & Risk) |
| `TrainingStatsStripe` | `/admin/training/stats` | Admin | None | Admin (Training Governance) |

## 4. Fix shipped (frontend-only · additive · reversible)

**No backend rewrites.** Token gates remain unchanged; the iter180
boundary that rejects PM tokens on `/api/admin/*` is doctrine and
stays in place.

| Change | File | Diff size |
|---|---|---|
| Add `readOnly` prop to `MasterListPanel` (skip status/archive/CRUD, hide write UI) | `frontend/src/components/MasterListPanel.jsx` | ~14 lines net |
| Add `readOnly` prop to `EmployeeMasterPanel` | `frontend/src/components/EmployeeMasterPanel.jsx` | ~2 lines |
| Add `readOnly` prop to `SupplierMasterPanel` | `frontend/src/components/SupplierMasterPanel.jsx` | ~2 lines |
| Add `readOnly` prop to `EquipmentMasterPanel` (skip 2 × `/admin/equipment-master/*` calls, hide write UI) | `frontend/src/components/EquipmentMasterPanel.jsx` | ~24 lines net |
| Trim PM section wrappers — drop `EquipmentStatusBoard`, `AdminJobMasterPanel`, `TrainingStatsStripe`, `AutoEmailRoutingPanel`, `ComplianceExportPanel`; pass `readOnly` where retained | `frontend/src/pages/pm/PmSections.jsx` | rewrite (75 → 75 LOC) |
| Drop `/pm/jobs`, `/pm/routing`, `/pm/compliance-export` routes | `frontend/src/App.js` | ~10 lines |
| Drop matching entries from PM Sidebar V1 (`SECTIONS`) | `frontend/src/components/PmShell.jsx` | ~3 lines |
| Drop matching entries from PM Sidebar V2 (`DOMAINS_V2`) | `frontend/src/components/pm/sidebar/domainMap.js` | ~6 lines |

The fix is live for **every PM user**, not behind any feature flag,
per the user's explicit directive ("this is a platform auth/session
correctness fix, not a visual or UX experiment").

## 5. Regression coverage shipped

1. **Playwright test** `backend/tests/pw_suite/test_portal_token_routing.py`:
   - Logs in as PM via API, seeds `masci.pm.token` into localStorage
   - Visits each remaining PM sidebar entry
   - Records every network response with `/api/admin/` in the URL
   - Asserts ZERO admin-namespace calls fire
   - Asserts page body does NOT contain "Admin login required"
2. **Pre-deploy gate** `scripts/pre_deploy_check.sh` gains a new
   `auth-routing` stage that runs the test above and the existing
   iter179 access-control gate.

## 6. Doctrine reaffirmed

- ✅ NO backend rewrites
- ✅ NO destructive schema migrations
- ✅ NO production touches
- ✅ Additive, reversible, minimal LOC (≈140 lines net across 7 files)
- ✅ Shared auth/session behavior remains uniform (no per-portal hacks)
- ✅ No `if PM then bypass` logic
- ✅ Cross-portal mental model preserved (Admin Hub keeps full write
  surface; PM gets calm read-only views of the same masters)

## 7. Future follow-ups (P2 · NOT this iteration)

- Move `/api/admin/projects/list`, `/api/admin/projects/pnl`,
  `/api/admin/qaqc-inspections/export.csv` to `/api/projects/*` /
  `/api/qaqc-inspections/*` (non-admin namespace) so the `AP`-gated
  `/admin/pnl` and `/admin/qaqc` pages function correctly for PMs.
- Decide whether to widen `EquipmentStatusBoard` to PM tokens; if yes,
  re-introduce it to PM Fleet behind a new `require_admin_or_pm` gate
  on the listing endpoint.
- Consider a calm read-only `PmJobsRead` view backed by the public
  `/jobs` endpoint (PM-scoped) so PMs have a dedicated jobs surface
  again without re-introducing AdminJobMasterPanel.
