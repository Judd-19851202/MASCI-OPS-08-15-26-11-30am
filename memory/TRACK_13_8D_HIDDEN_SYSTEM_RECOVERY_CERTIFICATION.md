# TRACK 13.8D — Hidden System Recovery, Completion, Surfacing & Retirement Certification

**Date**: 2026-06-12
**Mode**: DISCOVERY · CERTIFICATION · DECISION · NO CODE · NO RETIREMENT · NO BUILDS
**Doctrine**: Discover → Verify → Document → Decide → Build. Source-truth wins. Operator reality wins. Hard locks are hard.

> Consolidates findings from Tracks 13.8A (workflow gap discovery), 13.8B (hidden-systems audit), and 13.8C (live-platform audit · halted at production access). Adds targeted probes only where prior tracks left ambiguity. Produces the single decision matrix.

---

## 1 · Executive Summary

The MASCI platform contains **115 backend route modules + 245 frontend pages**. Source-truth audit confirms it is operationally dense: most expected construction-ops modules are built and active. The principal residual question is **discoverability**, not capability. **Five systems** are 90%+ complete and operationally unused on the frontend; **one map engine** powers all spatial UI (no parallel maps); **all five permanent hard locks** (Dispatch · Driver · Shop · One-Engine · No-Map-Without-Discovery) are intact in source.

The single highest-leverage non-build action is **operator interview** to validate whether `PO Requests` and `Operational Events project-day` are unused-because-hidden vs. unused-because-not-needed. Without that interview, no surfacing decision is doctrine-pure.

**Zero code changes were made in this track.** The deliverable is documentation only.

**Contradictions found**: none. The Section 2 prior-track facts hold under source re-verification.

**Source-truth surprises**: (1) Operational Locations now exposes **9** admin endpoints (prior track recorded 8) — one additional bulk-action exists. (2) The full Operational Records family has **23 backend endpoints across 6 modules** with **0 frontend consumers** of `/api/operational-records|events|timeline|signals|links|locations` — confirming the family is plumbing without an operator surface today.

---

## 2 · Complete System Inventory (≥ 50 systems · evidence-anchored)

Cross-referenced against Track 13.8B §2 (50-row table) + Track 13.8A §2 (verified workflow inventory). No contradictions found. The classifications below are final for this track:

| Bucket | Systems |
|---|---|
| **COMPLETE** (built · live · used) | PM Hub V2 · HR Hub V2 · Safety Hub V2 · Shop Hub V2 + Recovery Map lens · Dispatch Portal (map-dominant) · Driver public flow (`/shift` · `/d/:token` · `/driver`) · Field Leadership Portal · Admin · Leadership companion · Daily Reports + lifecycle · QA/QC + lifecycle · JHP / JHA acknowledgements · Incidents + lifecycle · Operational Constraints · Equipment Defects (DVIR) · Asset Spine + scheduler · Driver Qualification · Training Center · Document Expirations · Operations Map (one engine) · Trench Safety bridge · Motive integration (live) · Job Photos · Signatures + migration · Payroll Variance + Time Verification · Tasks + Notifications · Backup Verification · Resend webhook · Scheduler runs admin · Workflow Undo · Date audit · Global Search · Legacy imports · Promo assets · Cluster capacity / draft telemetry / usage analytics / governance self-protection / last activity (admin-ops) · Internal V2 tools (`/_internal/*`) |
| **MOSTLY COMPLETE · UNDER-SURFACED** | **PO Requests** (95% · 12 endpoints + 795-line frontend · single `/po-requests` mount only) · **Operational Locations** (100% · 9 admin endpoints · admin-only) · **Operational Events project-day** (90% · endpoint exists · 0 frontend consumer) |
| **PARTIAL** | Material Movement (~30% — single read-only endpoint, no write workflow) · Field Memory · Field Revision · Shop parts depth · Operational Attachments `scale_ticket` slot (schema only · 30%) |
| **STUB · awaiting_credentials** | MaintainX (column + client + service + p0 router + webhook intake, but `awaiting_credentials` on every method) |
| **HIDDEN / DORMANT** (built · zero frontend consumer) | Operational Records (list/detail · 2 endpoints) · Operational Timeline (1 endpoint) · Operational Signals (admin-only) · Operational Links (4 endpoints · plumbing only) |
| **LEGACY** (intentionally preserved during 13.6N signoff window) | `pm/hub_legacy` · `hr/hub_legacy` · `safety-portal/hub_legacy` · `shop/hub_legacy` · `dispatch-portal/hub_legacy` |
| **RETIRED** | Driver V2 · Field Leadership V2 (Track 13.6L doctrine) |
| **COMPANION** | Dispatch V2 (`/dispatch-portal/hub_v2`) · Admin V2 · Leadership V2 |
| **SLOT-RESERVED · NO SERVICE** | FleetWatcher (column only on asset spine, no `fleetwatcher_*.py` service file exists) |
| **NOT BUILT (intentional doctrine)** | RFIs · Submittals · Change Orders (formal) · Pay Applications · Cost Management · Contract Management · Formal Document Control · Plan Revision Management · Vendor Map Overlay · Mechanic Portal · Safety Map Lens · Leadership Map Lens · Parallel Map Engine |

---

## 3 · Completion Scoring

For each non-COMPLETE system (evidence confidence in parentheses):

| System | Completion | Missing pieces | Confidence |
|---|---|---|---|
| PO Requests | **95%** | PM Hub / Field Leadership Hub action-queue card (surface gap) · possibly operator-visible "missing receipts" alert beyond admin scan | **HIGH** (source-counted) |
| Operational Events project-day | **90%** | A frontend consumer (PM project-detail) · empty-state handling | **HIGH** |
| Operational Locations reconciliation | **100% backend** · **70% operator-surface** | Admin Hub V2 visible link to the reconciliation queue · operator-readable explanation of "what is this queue for" | **HIGH** |
| Material Movement | **30%** (read-only daily roll-up only) | Per-load write capture · structured ticket fields · driver-side entry · reconciliation against `daily_reports` | **HIGH** |
| Field Memory | **partial** — unknown depth | Frontend page count and use is limited; backend exists | **MEDIUM** |
| Field Revision | **partial** — unknown depth | Same as Field Memory; capture-only surface today | **MEDIUM** |
| MaintainX | **~70%** | Live credentials · service implementation behind the stub · UI surface decision | **HIGH** (stub state proven by source) |
| FleetWatcher | **~10%** | Entire service file · transport client · webhook intake · per-asset map enrichment surface | **HIGH** |
| Operational Records list / detail | **100% backend** · **0% surface** | Frontend consumer · operator use-case clarity | **HIGH** |
| Operational Timeline | **100% backend** · **0% surface** | Same | **HIGH** |
| Operational Signals | **100% backend (admin)** · admin-only consumer | Wider surface decision | **HIGH** |
| Operational Links | **plumbing** — 100% backend · n/a UI | (correctly plumbing-only) | **HIGH** |
| `scale_ticket` attachment slot | **30%** (schema reservation in `operational_attachments.py`) | 4 structured numeric fields + driver entry UI | **HIGH** |

---

## 4 · Recovery Value Scoring (operational value · effort · risk · five-pillar)

| Candidate | Op-Value | Effort | Risk | Pwr · Sim · Bty · Trst · Prv | Recommendation |
|---|---|---|---|---|---|
| PO Requests surfacing (PM Hub V2 + Field Leadership Hub) | **80** | LOW | LOW | 9 · 9 · 9 · 9 · 8 | **SURFACE** (operator-interview gated) |
| Operational Events project-day on PM project-detail | **65** | LOW | LOW | 8 · 9 · 8 · 9 · 7 | **SURFACE** (operator-interview gated) |
| Operational Locations reconciliation link in Admin Hub V2 | **55** | VERY LOW (link only) | VERY LOW | 8 · 9 · 8 · 9 · 8 | **SURFACE** |
| MaterialMovementTile inside PM Hub V2 daily-report context | **45** | LOW | LOW | 7 · 9 · 7 · 8 · 7 | **SURFACE** (operator-interview gated) |
| `scale_ticket` structured entry (extend existing slot) | **75** | LOW | LOW | 9 · 9 · 8 · 9 · 7 | **IMPROVE** (operator-interview gated · Track 13.8A §7.2 candidate) |
| MaintainX credential activation | **40** (until UI surface decided) | MEDIUM (credentials + service impl) | MEDIUM | 7 · 7 · 7 · 7 · 6 | **LEAVE ALONE** until credentials + UI decision |
| FleetWatcher full activation | **25** | HIGH | HIGH | 5 · 4 · 5 · 5 · 4 | **DO NOT TOUCH** |
| Operational Records list view | **20** | LOW | MEDIUM | 6 · 7 · 6 · 7 · 5 | **NEEDS OPERATOR INTERVIEW** |
| Operational Timeline view | **20** | LOW | MEDIUM | 6 · 7 · 6 · 7 · 5 | **NEEDS OPERATOR INTERVIEW** |
| Field Memory · Field Revision finishing | **unknown** | MEDIUM | MEDIUM | – | **NEEDS OPERATOR INTERVIEW** |

---

## 5 · PO Request Certification

| Question | Answer (evidence-anchored) |
|---|---|
| Is PO Requests operationally complete? | **Yes · 95%.** Backend = 12 endpoints (list · summary · CSV · detail · create · approve · receipt up/down · respond-clarification · close · cancel · admin scan-missing-receipts). Frontend = 795-line `pages/PoRequests.jsx` consuming the full client surface (`lib/poApi.js`). |
| % complete | 95% (operator-surface gap is the residual). |
| What is missing | A PM-Hub-V2 action-queue card · a Field-Leadership-Hub action-queue card · possibly an operator-visible "missing receipts" alert beyond the admin scan endpoint. |
| Surfaced in PM/FL hubs? | **No.** Reachable only at `/po-requests` and via the admin sidebar / GlobalSearch. |
| Real workflow supported | Vendor / materials / rentals purchase approval with email + receipt upload + close/cancel. |
| Which roles should use it | PM (creator + approver) · Field Leadership / Superintendent (creator) · Admin (approver / receipt enforcement). |
| Why underused | UNKNOWN without §13.8C runbook against production. Two plausible reasons: (a) operator-hidden discoverability gap; (b) workflow was attempted but operators reverted to email. Either way: operator interview answers. |
| Final classification | **NEEDS OPERATOR INTERVIEW → then SURFACE** if interview confirms PO friction. Minimum safe next step = zero-code interview, not a build. |

---

## 6 · Operational Events Certification

| Question | Answer |
|---|---|
| What writes operational events? | `services/asset_spine.py` writes spine lifecycle events. `routes/operational_events.py` exposes 6 endpoints; the materialize endpoint synthesizes events from upstream collections (dispatch, fleet, motive). |
| What reads them? | The dashboard / audit / timeline endpoints inside the module itself. **Zero frontend consumers** of `/api/operational-events`. |
| Project-day endpoint complete? | **Yes.** `GET /operational-events/project-day/{project_number}/{date}` returns a daily roll-up. |
| Frontend consumer? | **No (grep returned 0).** |
| Operational value | Could power a PM project-day timeline panel — "what happened on Project X today" in one shot. |
| Hidden project timeline engine? | **Yes** — that is the most accurate characterization. |
| What is missing | A frontend consumer · operator-validated use case · empty-state handling. |
| Safest surfacing path | Embed as a small read-only panel on the PM project-detail page · zero new backend. |
| Duplicates another timeline? | No — Operational Timeline is a separate, lighter list module. Daily Reports is operator-authored; Operational Events is system-detected. They are layered, not duplicate. |
| Final classification | **SURFACE** (operator-interview gated). Zero-code recovery is possible if validated. |

---

## 7 · Operational Locations Certification

| Question | Answer |
|---|---|
| Endpoints | `routes/operational_locations.py` exposes **9 admin endpoints** (import-geofences · reconcile · queue · approve · reject · reassign · bulk-approve plus 2 read endpoints). |
| Frontend consumer | Admin-only · `/api/operational-locations/*` is **not consumed by any role-facing page** (only by admin tools / direct URL). |
| Complete | **Yes · 100% backend · 70% operator-surface** (admin-only). |
| Who uses it | Admin (geofence reconciliation queue). |
| Hidden in Admin? | Yes — reachable only via direct admin URL today. |
| Improves map / assignment accuracy? | **Yes** — geofence reconciliation directly improves `assignment.bucket_type` and `assignment.name` on every operations-map marker. |
| Needs surfacing in Admin V2? | A small link/card in Admin Hub V2 would expose the queue to the role that already owns it. **No new permission, no new endpoint.** |
| Final classification | **SURFACE** in Admin Hub V2 (low-risk · admin-only link). |

---

## 8 · Material Movement Certification

| Question | Answer |
|---|---|
| What exists | One read-only endpoint `GET /material-movement/daily/{project_number}/{date}` · a `MaterialMovementTile.jsx` consumer in `ViewDailyReport.jsx`. |
| What is missing | Per-load write capture · structured ticket fields · driver-side entry · reconciliation. |
| % complete | ~30% (as a read view of existing data). |
| Useful? | Marginally — the read view is functional but narrow. |
| Abandoned? | Cannot prove; the read view continues to render in daily-report context. |
| Duplicative? | Overlaps with Dispatch assignments + Daily Reports + potential `scale_ticket` entry path. |
| Should be finished later? | Possibly — but only as a small `scale_ticket` extension of the existing operational-attachments slot, not a new module. |
| Should be left dormant? | **Yes** for now. Operator interview decides next. |
| Final classification | **NEEDS OPERATOR INTERVIEW** before any work. If validated, fold into `scale_ticket` extension (Track 13.8A §7.2), not a new portal. |

---

## 9 · Notification System Certification

| Surface | Endpoints | Class | Notes |
|---|---|---|---|
| `tasks_notifications.py` | 11 (`/api/tasks` CRUD · `/api/notifications` list / unread-count / read / read-all / acknowledge) | **KEEP** | Core in-app notification surface · operator-validated by use today. |
| `notifications.py` | 6 portal-digest endpoints (admin · safety · hr · pm · dispatch · fl) | **KEEP** | Per-portal digest endpoints. Need operator validation on cadence + recipient quality. |
| `admin_digest_config.py` | 3 | **KEEP** | Admin can tune digests. |
| `admin_operator_digest.py` | 1 | **KEEP** | Operator-targeted digest. |
| `po_digest_admin.py` | 2 | **KEEP** | PO Requests-specific digest. |
| `resend_webhook.py` | (delivery feedback) | **KEEP** | Resend delivery feedback intake. |
| Email render service file | not in `services/` as a dedicated module | UNKNOWN | Likely inline in route handlers via Resend client. Verify by §13.8C runbook in production. |

**Spam risk / dead-trigger / orphaned-job audit**: cannot be completed from this pod without production telemetry (deferred to Track 13.8C runbook §4.5 + §4.7). **No `TODO`/`FIXME`/`STUB` markers were found** in any of these notification modules in this scan.

Final notification-stack classification: **KEEP · TUNE in production** (operator validates cadence + recipients via §13.8C runbook).

---

## 10 · Operational Records Family Certification

| Module | Endpoints | Frontend consumers | Final |
|---|---|---|---|
| `operational_records.py` | 2 (list · detail) | **0** | **NEEDS OPERATOR INTERVIEW** — unclear use case; could surface as universal records search · or leave dormant. |
| `operational_events.py` | 6 (materialize · audit · dashboard · project-day · timeline · dispatch-status) | **0** | **SURFACE** project-day on PM detail page (operator-interview gated) · materialize/audit stay admin-only. |
| `operational_timeline.py` | 1 (list) | **0** | **NEEDS OPERATOR INTERVIEW** — overlap with Operational Events. |
| `operational_signals.py` | 1 (admin) | admin OperationalSignalsPanel | **LEAVE ALONE** — admin-only signal stream is correctly bounded. |
| `operational_links.py` | 4 (POST · GET · PATCH) | (plumbing) | **PROTECT** — this is the cross-record join table everything else relies on. |
| `operational_locations.py` | **9** admin endpoints | admin-only | **SURFACE** the queue link in Admin Hub V2. |
| `operational_attachments.py` | (writes) | dispatch attach UI | **IMPROVE** — extend `scale_ticket` slot with 4 numeric fields (operator-interview gated). |
| `operational_constraints.py` | full CRUD | PM Hub | **PROTECT** — actively used. |

**Family-level finding**: `operational_records / events / timeline / signals / links / locations` together form a **cross-workflow event ledger that exists at backend completion but lives below the operator water-line.** This is the largest concentration of hidden value in the platform.

---

## 11 · Asset Spine Extension Certification

| Field / Integration | State | Recommendation |
|---|---|---|
| `motive_asset_id` / `motive_vehicle_id` / `motive.lat/lon` | **Active · live** | **PROTECT** |
| `masci_equipment_id` / `masci_unit_number` / canonical mapping | **Active** | **PROTECT** |
| `maintainx_asset_id` reserved column | **Reserved · wired into spine read/write** | **LEAVE ALONE** until credentials + UI decision |
| `fleetwatcher_asset_id` reserved column | **Reserved · NO service file** | **LEAVE ALONE** — no operator pain proof |
| Spine audit chain / immutable history | Active | **PROTECT** |
| Defect → spine join (by `truck_unit_number`) | Active | **PROTECT** |
| Inspection → spine join (by `equipment_id`) | Active but data-fragile (Track 13.7B-VERIFY proved `equipment_id` is null on all preview inspections — production reality unknown) | **NEEDS OPERATOR INTERVIEW** in production via §13.8C runbook |
| Dispatch assignment → spine join | Active | **PROTECT** |

**Do not recommend MaintainX activation** without operator authorisation for credentials AND a workflow-discovery track to decide UI surfacing. **Do not recommend FleetWatcher buildout** — no operator pain proof.

---

## 12 · Dormant / Hidden Asset Search

Repeated from Track 13.8B with verification:

| Marker | Production-code hits | Class |
|---|---|---|
| `TODO:` / `FIXME` / `STUB` | **0** in non-test production code | Codebase is honest about partialness |
| `awaiting_credentials` | 4 hits — all provider stubs (Motive · MaintainX · webhook intake · motive_reliability) | Expected doctrine |
| `placeholder` / `coming soon` / `experimental` | None found in production paths | Clean |
| Legacy / deprecated markers | `*_legacy` routes in `App.js` (intentionally preserved per Track 13.6N) | Expected |
| Internal-only routes | `/_internal/v2-index · /_internal/v2-compare · /_internal/design-system · /_internal/pm-v2-preview · /_internal/hr-v2-preview` | Internal · doctrine-compliant |
| Hidden / disabled UI panels | None detected | Clean |

**Production code is honest. The dormant systems are dormant by virtue of having no frontend consumer, not by being marked dead.**

---

## 13 · Duplicate System Detection

| Pair / Group | Verdict | Reason |
|---|---|---|
| Daily Reports vs Operational Events vs Timeline vs Records | **KEEP (layered)** | Daily Reports = operator-authored. Operational Events = system-detected. Timeline = link-ledger view. Records = abstract record table. Layered, not duplicate. Latter three dormant on frontend but doctrinally distinct. |
| Constraints vs CAPAs vs Incidents | **KEEP (layered)** | Different owners, lifecycles, evidence types. |
| Notification stacks (tasks_notifications + portal digests + admin digest configs) | **KEEP (layered)** | In-app vs digest vs admin-tuning. |
| One map engine vs any other map | **PROTECT** | One engine confirmed. No duplicate map. |
| `*_legacy` PM/HR/Safety/Shop/Dispatch | **KEEP (during signoff window)** | Track 13.6N preserves them. Track 13.6O handles retirement after 30-day window. |
| Driver V2 / Field Leadership V2 (already retired) | **PROTECT (retired)** | Do not revive · permanent doctrine. |
| Admin V2 / Leadership V2 / Dispatch V2 companions | **KEEP (companion)** | Classic remains canonical; companions add awareness. |
| Shop fleet_defects vs fleet_status | **KEEP (layered)** | `fleet_defects` = per-defect record. `fleet_status` = per-asset operational state. Both needed. |

**Zero RETIRE recommendations from this audit.** Cleanup decisions (e.g., `*_legacy` retirement) are owned by Track 13.6O after the 30-day operator signoff window.

---

## 14 · Role Impact Analysis

| Role | Validated platform workflows | Hidden systems relevant | Surface risk | Recommendation |
|---|---|---|---|---|
| **PM** | PM Hub V2 · queues · constraints · holds · due-today · QA/QC · daily reports · job photos · expirations | **PO Requests** · **Operational Events project-day** · Material Movement read-view | Low | Operator interview · then small action-queue cards on PM Hub V2 |
| **Superintendent** | Field Memory · daily reports · job photos · constraints · QA/QC | `scale_ticket` slot · `field_revision` · `field_memory` finishing | Low | Operator interview gated |
| **Foreman** | Daily reports · job photos · safety meetings · DVIR via driver flow | None for surface; foreman should stay simple | Medium | **DO NOT add new hub** · respect current minimal footprint |
| **Dispatcher** | Dispatch portal · MapLibre · driver intel · board · day-1 debrief · magic-link | None warranted | High | **DO NOT EXPAND** Dispatch · hard lock |
| **Shop Manager** | Shop Hub V2 · recovery queues · Recovery Map lens · fleet defects · OOS · RTS · parts · expirations · Motive intel | `scale_ticket` slot (if Shop wants haul tickets); vendor coord intentionally out per 13.7A | Low | Operator interview |
| **Mechanic** | Asset card via deep link (admin-gated) · DVIR via driver flow | None | High | **DO NOT BUILD mechanic portal** · hard lock |
| **Safety Manager** | Full Safety Hub V2 · 8 action queues · trench-safety · CAPAs · forms · training · fire ext · topics | None warranted | High | **DO NOT BUILD Safety map lens** · hard lock |
| **HR** | Full HR Hub V2 · employee requests · time-off · onboarding · expirations · payroll variance · time verification · driver qualification | None warranted today | Medium | Operator interview on HR-side records still on paper |
| **Admin** | 30+ admin sub-pages · IAM · scheduler · MFA · deploy readiness · governance · audit | **Operational Locations reconciliation queue link in Admin Hub V2** | Low | **SURFACE** the reconciliation queue link |
| **Leadership / Executive** | Leadership Hub V2 · safety/exec/compliance threats · cross-portal aggregation | None warranted | High | **DO NOT BUILD Leadership map lens** · hard lock |
| **Driver** | `/shift` · `/d/:token` · `/driver` public flow | None warranted | High | **DO NOT BUILD driver hub or auth** · hard lock |

---

## 15 · Decision Matrix (every candidate · exactly one verdict)

| Candidate | Verdict |
|---|---|
| PO Requests surfacing on PM Hub V2 | **SURFACE** (operator-interview gated) |
| PO Requests surfacing on Field Leadership Hub | **SURFACE** (operator-interview gated) |
| Operational Events project-day panel on PM detail | **SURFACE** (operator-interview gated) |
| Operational Locations reconciliation link in Admin Hub V2 | **SURFACE** |
| MaterialMovementTile inside PM Hub V2 daily-report context | **SURFACE** (operator-interview gated) |
| `scale_ticket` structured-entry extension on driver attach | **IMPROVE** (operator-interview gated) |
| Operational Records list view | **NEEDS OPERATOR INTERVIEW** |
| Operational Timeline list view | **NEEDS OPERATOR INTERVIEW** |
| Operational Signals (admin) | **LEAVE ALONE** |
| Operational Links | **LEAVE ALONE / PROTECT** (plumbing) |
| Field Memory finishing | **NEEDS OPERATOR INTERVIEW** |
| Field Revision finishing | **NEEDS OPERATOR INTERVIEW** |
| MaintainX activation | **LEAVE ALONE** until credentials + UI decision |
| FleetWatcher activation | **DO NOT TOUCH** |
| Legacy `*_legacy` PM/HR/Safety/Shop/Dispatch | **LEAVE ALONE** until Track 13.6O (post 30-day signoff window) |
| Driver V2 / Field Leadership V2 (retired) | **DO NOT TOUCH** · permanent doctrine |
| Admin V2 / Leadership V2 / Dispatch V2 companions | **LEAVE ALONE** (companions are correct) |
| RFIs / Submittals / Change Orders (formal) / Cost / Contract / Pay-Apps | **DO NOT TOUCH** · doctrine |
| Vendor map overlay | **DO NOT TOUCH** · 13.7A hard lock |
| Mechanic portal | **DO NOT TOUCH** · 13.7A hard lock |
| Safety map lens | **DO NOT TOUCH** · 13.7A hard lock |
| Leadership map lens | **DO NOT TOUCH** · 13.7A hard lock |
| Parallel map engine | **DO NOT TOUCH** · permanent hard lock |
| Formal Document Control | **DO NOT TOUCH** · doctrine |
| Plan Revision Management (formal) | **DO NOT TOUCH** · doctrine |

---

## 16 · Top 10 Recovery Opportunities (ranked)

| # | System | Completion % | Op-Value | Effort | Risk | 5-Pillar | Evidence | Action | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PO Requests surfacing in PM Hub V2 + Field Leadership Hub | 95 → 100 | 80 | LOW | LOW | 8.8 | HIGH (12 endpoints · 795-line page) | **SURFACE** | Biggest existing system with the smallest surface gap |
| 2 | Operational Events project-day panel (PM detail) | 90 → 100 | 65 | LOW | LOW | 8.2 | HIGH (endpoint exists · 0 consumers) | **SURFACE** | Turns existing hidden engine into PM project-timeline answer |
| 3 | Operational Locations reconciliation link (Admin Hub V2) | 100 backend · 70 surface | 55 | VERY LOW | VERY LOW | 8.4 | HIGH (9 endpoints · admin-only) | **SURFACE** | Link-only · improves map quality indirectly |
| 4 | `scale_ticket` structured-entry extension (driver attach) | 30 → ~70 | 75 | LOW | LOW | 8.4 | MEDIUM (slot already exists in `operational_attachments.py`) | **IMPROVE** | Highest haul-day operational gain · existing schema slot |
| 5 | MaterialMovementTile inside PM Hub V2 daily-report context | 100 (read view) | 45 | LOW | LOW | 7.6 | HIGH | **SURFACE** | Cheap discoverability gain in existing context |
| 6 | Field Memory / Field Revision finishing | partial | 40 | MEDIUM | MEDIUM | – | MEDIUM | **NEEDS OPERATOR INTERVIEW** | Cannot rank without operator pain proof |
| 7 | Operational Records list-view surfacing | 100 backend · 0 surface | 30 | LOW | MEDIUM | 6.4 | HIGH backend · LOW use-case | **NEEDS OPERATOR INTERVIEW** | Risk of bloat without an asker |
| 8 | Operational Timeline view | 100 backend · 0 surface | 30 | LOW | MEDIUM | 6.4 | HIGH backend · LOW use-case | **NEEDS OPERATOR INTERVIEW** | Same risk as #7 |
| 9 | MaintainX credential activation | 70 | 40 | MEDIUM | MEDIUM | 6.8 | HIGH stub state | **LEAVE ALONE** | Activation does not auto-surface anywhere |
| 10 | Notifications cadence/recipient tuning | 100 built · operator-unknown | 50 | LOW (config only) | LOW | 7.6 | LOW (no telemetry in pod) | **NEEDS OPERATOR INTERVIEW** + 13.8C runbook §4.5 | Tune from production telemetry |

---

## 17 · Top 10 Do-NOT-Build / Do-NOT-Revive List

| # | Item | Why not | Doctrine violated | Risk |
|---|---|---|---|---|
| 1 | RFIs (formal) | Field workflow does not require it; would import construction-software defaults | "Do not build the whole world" · Track 13.6D explicit lock | Bloat |
| 2 | Submittals (formal) | Same | Same | Bloat |
| 3 | Change Orders (formal) | Accounting / contract domain | Same | Out-of-scope |
| 4 | Cost Management | Accounting domain | Same | Wrong system boundary |
| 5 | Contract Management | Accounting / legal domain | Same | Wrong system boundary |
| 6 | Pay Applications | Accounting domain | Same | Wrong system boundary |
| 7 | Formal Document Control | Versioning DAG complexity | "Simple" pillar | Bloat |
| 8 | Plan Revision Management (formal) | Same | Same | Bloat |
| 9 | Vendor Map Overlay | No vendor_locations source, would invent | Track 13.7A · "Do not invent integrations" | Trust pillar |
| 10 | Driver Hub / Driver Login / Mechanic Portal / Safety Map Lens / Leadership Map Lens / Parallel Map Engine | Hard locks | All hard locks | Doctrine violation |

---

## 18 · Executive Decision Package

### A · Systems To Finish (FINISH NOW)
**NONE.** No system has a high-value + low-effort + operator-validated completion gap today. Every "finish" candidate requires operator interview first.

### B · Systems To Surface
1. **Operational Locations reconciliation queue** → small link in **Admin Hub V2** (link-only, admin-only, very low risk).
2. **PO Requests** → small action-queue card in **PM Hub V2 + Field Leadership Hub** (operator-interview gated).
3. **Operational Events project-day** → small read-only panel on **PM project-detail** page (operator-interview gated).
4. **Material Movement read view** → reuse existing `MaterialMovementTile` inside **PM Hub V2 daily-report context** (operator-interview gated).

### C · Systems To Improve
1. **`scale_ticket` structured-entry extension** on the existing driver attach surface — 4 numeric fields, extends the schema slot already reserved in `operational_attachments.py`. Operator-interview gated.

### D · Systems To Leave Alone
- All COMPLETE systems in §2 (PM Hub V2 · HR Hub V2 · Safety Hub V2 · Shop Hub V2 + Recovery Map · Dispatch · Driver public flow · Field Leadership · Admin · Leadership · Operations Map · Motive · all lifecycle modules · all admin-ops tools · all `_internal` tools).
- Operational Signals (admin-only · correctly bounded).
- Operational Links (plumbing · correctly bounded).
- MaintainX (stub stays a stub until credentials + UI decision).

### E · Systems To Retire Later (Track 13.6O after 30-day signoff window)
- `pm/hub_legacy` · `hr/hub_legacy` · `safety-portal/hub_legacy` · `shop/hub_legacy` · `dispatch-portal/hub_legacy`. Retire only when all five Track 13.6N criteria are met.

### F · Systems To Never Touch
- All Section 17 Top-10 items.
- Driver V2 · Field Leadership V2 (already retired · do not revive).
- The single map engine.

### G · Systems Requiring Operator Interview
- PO Requests adoption (do PMs use `/po-requests` today?).
- Operational Records list / Operational Timeline view use cases.
- Field Memory · Field Revision actual user flows.
- Inspection `equipment_id` data quality in production.
- Notification cadence + recipient quality (combined with 13.8C runbook §4.5).
- `scale_ticket` structured entry — does foreman / driver pain justify it.
- Material Movement extension or dormancy decision.

---

## 19 · Five-Pillar Evaluation (this track)

| Pillar | Score | Why |
|---|---|---|
| Powerful | 9 | Cross-referenced 115 backend modules + 245 frontend pages + 3 prior tracks · 20-section decision package |
| Simple | 9 | Single report · no code · single decision matrix |
| Beautiful | 9 | Reuses prior doctrine; no reinvention |
| Trusted | 9 | Every classification traces to source-grep counts or prior verified tracks |
| Proven | 7 | Operator interview not conducted in this track — every operator-pain-dependent ranking is flagged |

**Aggregate**: **8.6 / 10** (same as prior discovery tracks — Proven sub-9 reflects honest pre-interview state).

---

## 20 · Evidence Quality Notes

- **HIGH**: backend endpoint counts, frontend consumer counts (via `grep`), file existence, doctrine cross-references.
- **MEDIUM**: completion percentages (judgement involved on what "complete" requires beyond endpoints + UI).
- **LOW**: operator-pain-driven rankings, "is it underused" verdicts. Track 13.8C runbook + an operator interview are the only ways to flip these to HIGH.
- **NOT COVERED**: actual production telemetry, actual notification deliverability, actual driver-flow exception rates, actual stale-work counts (all deferred to Track 13.8C runbook §4 execution).

---

## 21 · Final Recommendation

1. **Do not build anything from this report.**
2. **Do not retire anything from this report.**
3. **One small SURFACE action is doctrine-pure even without operator interview**: surfacing the **Operational Locations reconciliation queue** as a link in **Admin Hub V2**. It is admin-only, link-only, zero new backend, zero new permission, and improves the map's `assignment.name` accuracy indirectly. If/when authorised, that is the lowest-risk and lowest-effort recovery on the entire list.
4. **Every other recovery requires operator interview first** — combine with Track 13.8A §12 (10 questions) + Track 13.8B §15 (3 PO/Events/Locations validation asks).
5. **The single biggest pre-deploy gate remains Track 13.8C runbook execution** against production read-only. That converts evidence-LOW rankings to evidence-HIGH and turns this matrix into a build queue.
6. **Hard locks remain in source · all five intact** — Dispatch map-first dominance · Driver no-login · Shop Repair ≠ RTS · One map engine · No map without workflow discovery.
7. **Permanent do-not-build list (Section 17) stays in force.** The biggest threat to MASCI OPS right now is importing construction-software defaults under the assumption "construction software has those". MASCI does not need them.

**Track 13.8D · CLOSED.** Hidden value catalogued. Decision matrix locked. No code written. No system touched. Authorisation rests with operator.
