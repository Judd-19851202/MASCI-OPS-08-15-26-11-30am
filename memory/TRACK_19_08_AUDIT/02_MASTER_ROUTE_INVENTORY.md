# TRACK 19.08 · Master Route Inventory

* **846** unique route paths across `backend/server.py` + `backend/routes/*.py`.
* **~200** frontend `Route path=` entries in `frontend/src/App.js`.
* Snapshot: `/tmp/all_routes.txt` (backend), `App.js` extraction (frontend).

---

## 1 · Backend route roots (families)

Grouped by root segment. Counts are unique paths.

| Root | Count | Family | Owner |
| --- | ---: | --- | --- |
| `/daily-reports*` | ~18 | Daily Report | Field |
| `/incidents*` | ~14 | Incident / Injury / Accident / Near-Miss | Safety |
| `/equipment-inspections*` | ~10 | Equipment Pre-Op | Field / Shop |
| `/fleet/inspections*` · `/fleet/defects*` · `/fleet/units*` · `/fleet/_meta` | ~22 | DVIR + Fleet | Field / Shop / Dispatch |
| `/meetings*` | ~6 | Safety Meeting / Toolbox | Safety |
| `/jhas*` · `/jha-acknowledgements*` | ~10 | JHA | Safety |
| `/trench-safety/*` · `/excavation*` | ~18 | Trench / Excavation | Safety |
| `/qaqc-inspections*` · `/admin/qaqc-inspections*` | ~10 | QA-QC | PM / Admin |
| `/corrective-actions*` · `/hr/corrective-actions*` | ~6 | Corrective Action | Safety / HR |
| `/equipment-issuances*` · `/equipment-trainings*` | ~14 | Safety Equipment | Safety |
| `/employee-requests*` · `/hr/*` | 40+ | HR ops | HR |
| `/pm/*` · `/admin/pm-*` | 30+ | PM ops | PM |
| `/shop/fleet/*` · `/shop/*` | 20+ | Shop | Shop |
| `/dispatch/*` · `/admin/transportation/*` | 40+ | Dispatch / Transportation | Dispatch |
| `/employees*` · `/hr/employee-roster` | 15+ | HR / Employee canon | HR |
| `/jobs*` · `/admin/jobs*` | 15+ | Job master | Admin |
| `/photos*` · `/job-photos*` · `/photo-storage*` | 15+ | Photo / attachment | Cross |
| `/attachments*` · `/operational-attachments*` · `/daily-reports/attachments/upload` | 8 | Attachment | Cross |
| `/notifications*` · `/email-routes*` · `/email-routing*` | 20+ | Notification / Email | Cross |
| `/audit*` · `/audit-events*` | 8 | Audit spine | Cross |
| `/admin/*` (health / stability / trust / production / drift / etc.) | 100+ | Admin | Admin |
| `/dev/*` · `/version` · `/health*` | 10 | Ops | Cross |

Full snapshot: `/tmp/all_routes.txt` (846 lines).

---

## 2 · Frontend `Route path=` inventory (App.js extraction)

**Category A · Public / Field entry points** — no auth gate

| Path | Component | Purpose |
| --- | --- | --- |
| `/` | Home hub | Landing |
| `/daily/new` · `/daily/submit` · `/reports/daily/new` | `NewDailyReport` | Daily Report form |
| `/incidents/new` · `/incidents/submit` | `NewIncident` | Incident form |
| `/equipment/new` · `/equipment/submit` · `/equipment/:id` | `NewEquipmentInspection` · `ViewEquipmentInspection` | Equipment Pre-Op |
| `/fleet/dvir/new` · `/fleet/dvir/submit` · `/fleet/dvir/submitted/:id` | `NewFleetDVIR` · `FleetDVIRConfirmation` | DVIR |
| `/fleet/weekly-lead/new` · `/fleet/weekly-emergency/new` | `NewFleetDVIR` (variants) | Weekly fleet forms |
| `/meetings/new` · `/meetings/submit` | `NewMeeting` | Safety Meeting / Toolbox |
| `/inspections/new` · `/inspections/submit` · `/inspect/new` | `NewInspection` | Generic inspection |
| `/jha` · `/jha/new` · `/jha/submit` | `NewInspection` (JHA subtype) · `JhaPlansHub` | JHA |
| `/qaqc` · `/qa-qc` · `/qaqc/:slug/new` · `/qaqc/:id` | `NewQaqcInspection` | QA-QC |
| `/constraints` · `/constraints/new` · `/constraints/:id` | `Constraints` · `ConstraintDetail` | Constraints |
| `/trench-safety*` · `/trench-boxes` · `/trench-safety/excavation/new` | (trench components) | Trench Safety |
| `/leadership/*` · `/leadership/:kind/new` | `FieldLeadershipHub` · `FieldLeadershipFormPage` | Field Leadership dynamic forms |
| `/thank-you` | `ThankYou` | Post-submit landing |
| `/revise/:token` | `FieldRevision` | Revision link (public token) |
| `/submit` | (generic submit landing) | |
| `/field` · `/field/calculators` | `FieldSection` · calculators | Field hub |
| `/safety` · `/safety/inspections/new` · `/safety/cards` · `/safety/jha` · etc. | Safety-portal roots | Safety-portal (login-gated for most) |
| `/safety/forms/*` (equipment-issuance / equipment-training) | `NewSafetyEquipmentIssuance` etc. | Safety Equipment |
| `/transport-invite/:token` · `/transport-verify/:cnum` | Transportation orientation flow | |
| `/cheatsheet` · `/cheat-sheet` | `CheatSheet` | Field reference |

**Category B · Portal-gated routes** — require login token

* `/safety/*` (Safety portal) — Safety token
* `/hr/*` (HR portal) — HR token
* `/pm/*` (PM portal) — PM token
* `/shop/*` (Shop portal) — Shop token
* `/dispatch/*` (Dispatch portal) — Dispatch token
* `/leadership/*` (Field Leadership portal) — FL token
* `/admin/*` — Admin token
* `/sign-in` · `/admin/login` · `/dispatch/login` · `/hr/login` · `/safety/login` · `/safety/forms/login` · `/dispatch/*/change-password` etc. — Auth entry

**Category C · Preview / V2 dual-run**

* `SafetyHubV2` · `HrHubV2` · `HrV2Preview` · `DispatchHubV2` · `ShopHubV2` · `AdminHubV2` — new UI parallel to `SafetyHub` / `HrHub` / etc.
* Both remain mounted; user chooses via nav.

**Category D · Retired / Compat**

* `/api/admin/login` (POST) — returns 410 (retired Track 15.32).
* `DELETE /api/daily-reports/{id}` — returns 410 (historical DR immutable).
* Legacy `dvir` collection reads still supported for very old records.

---

## 3 · Feature flags

Detected env / config variables that gate route or behaviour visibility:

| Flag | Effect | Source |
| --- | --- | --- |
| `CREW_HUB_ENABLED` | Enables Crew Hub projects seeding | server.py boot |
| `SCHEDULER_ENABLED` | Enables cron schedulers (safety-digest, verify, transport-automation, dispatch-reminders, backup-scheduler, po-digest, operator-digest) | `lib/singleton_scheduler.py` |
| `APP_ENV` / `DB_NAME` guards | Refuse destructive seed against production | `scripts/seed_*` |
| `HUB_V2_ENABLED` | (implicit — controls Hub V2 default) | `Hub*V2` pages |

---

## 4 · Hidden / non-`Route`-mounted routes

* Admin routes referenced only via direct link (not in top nav) — e.g., `/admin/deploy-readiness`, `/admin/persistence-health`, `/admin/trust-spine`.
* `/qaqc/:slug/new` — dynamic route; `slug` derived from `pm_templates` collection.
* `/leadership/:kind/new` — dynamic route; `kind` derived from `field_leadership_equipment_catalog` and template catalog.
* Preview surfaces bound to specific admin pages via feature-flagged UI toggles (e.g., `HrV2Preview`).
