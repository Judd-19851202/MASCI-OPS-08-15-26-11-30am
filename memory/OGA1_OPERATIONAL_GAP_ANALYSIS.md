# OGA-1 · MASCI Docs Operational Gap Analysis Audit

**Date:** 2026-06-08
**Author:** Main agent · OMEGA-disciplined audit
**Scope:** Identify operational questions MASCI Docs still cannot answer.
**Status:** ✅ AUDIT COMPLETE · zero code · zero UI · zero architecture

---

## Methodology

For every role we list:

1. **Questions Answered Today** — anchored on shipped sprints: M-1, M-1R, P1, P1.5, P1.6, OIS-1, MCC-1, MCC-1 HR, DCP-1, DSI-1 (per `/app/memory/*_CERTIFICATION.md` and `PRD.md`).
2. **Questions NOT Answered Today** — gaps observed by tracing each daily question to its current source system (Motive · FleetWatcher · MaintainX · Outlook · phone · text · spreadsheets · paper).

**Scoring** — five ForgedOps pillars per gap, 1–10:
- **Powerful** — how much operational power is unlocked by closing the gap
- **Simple** — how straightforward is the gap to close (high = easy)
- **Beautiful** — how cleanly does the closure fit existing surfaces (high = no portal sprawl)
- **Trusted** — quality / latency of the data source available
- **Proven** — how validated the underlying integration path is

Composite is informational only. Ranking is by **operational value**, not technical interest.

---

# 1 · DISPATCH

## Questions Answered Today (post-DSI-1)

- ✅ Where is the truck right now?
- ✅ Who is driving it?
- ✅ Is it moving / idle / not reporting?
- ✅ Is the Motive gateway online?
- ✅ Did DVIR fail?
- ✅ Is there an open critical fault?
- ✅ When was the last Motive event?
- ✅ What is the current assignment / state?
- ✅ Trust pill on the Live Operations Snapshot

## Questions NOT Answered Today

| # | Question | Current Workaround | System Holding Answer | Frequency | Business Impact | Effort | Dependencies |
|---|----------|---------------------|----------------------|-----------|-----------------|--------|--------------|
| D1 | What load number / ticket # is on the truck right now? | Phone call to driver or plant; open FleetWatcher | FleetWatcher | every load · 50–200/day | HIGH — reconciliation, billing, project tracking | M | FW-1 license confirmation |
| D2 | What plant / yard did the truck load from this trip? | Driver radio · paper ticket | FleetWatcher / paper | every load | HIGH | M | FW-1 |
| D3 | Has the truck arrived at the dump site? (vs Motive geofence which is imprecise) | OnStation app / driver call | FleetWatcher cycle state | every load | HIGH | M | FW-1 |
| D4 | How many tons has each project received so far today? | Spreadsheet · phone | FleetWatcher production rollup | hourly | HIGH | M | FW-1 (aggregate over D1) |
| D5 | Which driver is on break vs available right now? | Phone · text · Motive HOS screen | Motive (raw HOS clock) — not yet decorated for MASCI | per-shift | MEDIUM | S | DCP-1 extension only |
| D6 | What ETA does each truck have to its current jobsite? | Driver call · operator instinct | Motive raw vehicle ETA — not surfaced | every trip | HIGH | M | needs Motive ETA endpoint surfaced |
| D7 | Which trucks are scheduled tomorrow vs unassigned? | Spreadsheet · whiteboard | MASCI dispatch_assignments (partially) + phone | nightly | HIGH | S | dispatch board future-day filter (does not exist yet) |
| D8 | Which drivers are at risk of an HOS violation today? | Open Motive · text driver | Motive HOS clock | per-shift | HIGH (regulatory) | M | needs HOS clock surfaced in DSI-1 |
| D9 | Which truck has an open MaintainX work order limiting its dispatch? | Open MaintainX | MaintainX (already partially wired) | nightly | HIGH | S | extend ShopMaintainxReadinessTile to Dispatch |

---

# 2 · SHOP MANAGER

## Questions Answered Today

- ✅ Critical fault list across the fleet (DSI-1 / Shop intel panel)
- ✅ Gateway-offline list
- ✅ DVIR defects (high / critical)
- ✅ Equipment not reporting (>24h) + assigned operator + last known location
- ✅ Live Motive timeline per asset
- ✅ MaintainX readiness queue (existing iter511 tile)

## Questions NOT Answered Today

| # | Question | Workaround | Source System | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|---------------|-----------|--------|--------|--------------|
| S1 | What is the OPEN work-order list per asset (not just readiness)? | Open MaintainX | MaintainX API | daily | HIGH | S | extend MaintainX surface in shop intel panel |
| S2 | When is the next scheduled PM per asset? | MaintainX | MaintainX API | weekly | MEDIUM | S | MaintainX schedule field |
| S3 | What's the lifetime parts cost per asset? | MaintainX + Excel | MaintainX cost field | monthly | MEDIUM | M | MaintainX cost rollup |
| S4 | Engine hours / mileage trend per asset? | Motive raw screen | Motive (raw odometer/engine-hour stream) | weekly | MEDIUM | M | extend asset_mappings to capture odom/engine_hours |
| S5 | DVIR defect categorisation (brakes vs lights vs tires)? | Open Motive DVIR | Motive raw DVIR payload | per inspection | MEDIUM | M | decorate dvir family with defect_type |
| S6 | Which assets are deployed vs in-yard vs in-shop? | Phone / whiteboard | dispatch_assignments + MaintainX status | daily | HIGH | S | already in data; not surfaced as one view |
| S7 | Predictive: which assets have rising fault frequency? | Manual scan | derive from motive_events | weekly | LOW-MED (forward-looking) | M | aggregation only |

---

# 3 · HR MANAGER

## Questions Answered Today

- ✅ Motive driver mapping cleanup (MCC-1 HR Extension)
- ✅ Driver Command Profile (identity + ops + safety + training counts)
- ✅ Training / certification expirations (Current / Expiring 30d / Expired)
- ✅ Open corrective actions per driver
- ✅ Lifecycle status, hire date, supervisor

## Questions NOT Answered Today

| # | Question | Workaround | Source System | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|---------------|-----------|--------|--------|--------------|
| H1 | Who is currently working overtime / who's projected to? | Payroll spreadsheet · phone | Payroll system + dispatch hours | weekly | HIGH | M | needs hours-worked rollup |
| H2 | Who is approaching CDL / Med-Card / endorsement expiration in the next 60 days? | Existing document_expirations partial — but UI only shows 30d window | document_expirations (already exists) | weekly | HIGH (regulatory) | S | extend DCP-1 expirations widget 30→60→90 |
| H3 | Cross-driver scorecard (best/worst HOS, harsh, DVIR)? | Manual scan of driver profiles one-by-one | Motive aggregated | monthly | MEDIUM | M | new "Driver Scorecard" derived view |
| H4 | Onboarding checklist completion per new hire? | Spreadsheet | OneDrive + DocumentVault | per hire | HIGH | M | onboarding tracker module |
| H5 | Who has filed PTO / has scheduled time off this week? | Outlook calendar / text | Email / spreadsheet | weekly | HIGH | M | PTO request module |
| H6 | Which driver is currently on light-duty / restricted-work? | Phone · spreadsheet | Spreadsheet | weekly | HIGH (claims) | M | restriction flag on employees |
| H7 | Disciplinary action history per driver? | Files / paper | Paper / OneDrive | quarterly | MEDIUM | M | disciplinary log module |

---

# 4 · SAFETY MANAGER

## Questions Answered Today

- ✅ Per-driver harsh event count (30d)
- ✅ Per-driver HOS violation count (30d)
- ✅ HOS status pill (DSI-1)
- ✅ Driver incidents (365d) on DCP-1
- ✅ Open corrective actions
- ✅ DVIR critical/high defects across fleet
- ✅ Last Motive event timeline per driver

## Questions NOT Answered Today

| # | Question | Workaround | Source System | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|---------------|-----------|--------|--------|--------------|
| SF1 | Trend: are harsh events rising / falling fleet-wide this month vs last? | Manual export | derive from motive_events | weekly | HIGH | M | trend chart |
| SF2 | Which jobsites have the highest incident rate? | Spreadsheet | incidents + sites | monthly | HIGH | M | incident-by-site aggregation |
| SF3 | Daily toolbox-talk completion log? | Paper / SignWith | Paper / Document Vault | daily | HIGH (OSHA) | M | toolbox-talk tracker |
| SF4 | Open near-misses awaiting review? | Email | Email | daily | HIGH | M | near-miss intake form |
| SF5 | OSHA 300 / 301 form completion per incident? | Paper / Word doc | Paper | monthly | HIGH (regulatory) | M | OSHA form generator |
| SF6 | Drug & alcohol test schedule / completion? | Spreadsheet | Spreadsheet | monthly | HIGH (DOT) | M | D&A tracker |
| SF7 | Has the operator of [equipment] been certified for that equipment type? | Manual cross-check | training records vs assignment | per shift | HIGH | S | join dispatch_assignments.truck × employee training |
| SF8 | AI Coach trend per driver | DCP-1 placeholder; Motive AI Coach not yet decorated | Motive AI Coach API | weekly | MEDIUM | M | needs Motive AI Coach feed activation |

---

# 5 · SUPERINTENDENT

## Questions Answered Today

- ✅ Active assignments on Dispatch board
- ✅ Per-driver profile lookup
- ✅ GPS / DVIR / fault status per assigned asset

## Questions NOT Answered Today

| # | Question | Workaround | Source | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|--------|-----------|--------|--------|--------------|
| SU1 | What crew is on which jobsite today? | Phone · text | Spreadsheet / Outlook | daily | HIGH | S | crew-by-site rollup (employees.crew × dispatch) |
| SU2 | Daily production for my project (tons / loads)? | FleetWatcher | FleetWatcher | hourly | HIGH | M | FW-1 |
| SU3 | Are we ahead or behind plan today? | Spreadsheet | Smartsheet / FleetWatcher | daily | HIGH | M | plan vs actual rollup |
| SU4 | Which subcontractors are on site? | Sign-in sheet | Paper / Procore | daily | HIGH | M | sub sign-in module |
| SU5 | Daily report for the project (manhours · weather · activities)? | Daily Reports module (exists) | MASCI Docs | daily | MEDIUM | S | already partially shipped — UX gap |
| SU6 | Photo / progress documentation log? | Phone gallery · text | Phone / Drive | daily | MEDIUM | M | photo capture module |

---

# 6 · PROJECT MANAGER

## Questions Answered Today

- ✅ Driver profile lookups
- ✅ Asset profile lookups
- ✅ Document expirations
- ✅ MaintainX readiness (asset-side)

## Questions NOT Answered Today

| # | Question | Workaround | Source | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|--------|-----------|--------|--------|--------------|
| P1 | Daily tons / loads / yield for my project? | FleetWatcher | FleetWatcher | daily | HIGH | M | FW-1 |
| P2 | Material mix breakdown (asphalt grade · concrete mix · aggregate)? | FleetWatcher | FleetWatcher | daily | HIGH | M | FW-1 + Command Cloud Mix Design |
| P3 | Cycle-time outliers (trucks running long)? | FleetWatcher | FleetWatcher | hourly | HIGH | M | FW-1 |
| P4 | Plant production rate for the day? | Phone to plant · FleetWatcher | FleetWatcher | hourly | HIGH | M | FW-1 |
| P5 | Cost-per-ton for the project right now? | Excel | FleetWatcher + Vista | weekly | HIGH | L | FW-1 + Vista bridge |
| P6 | Manhours burned vs budget? | Vista | Vista | weekly | HIGH | L | Vista bridge |
| P7 | Which subs have outstanding compliance docs? | Procore · phone | Procore | weekly | MEDIUM | M | sub-compliance module |
| P8 | Change-order log? | Smartsheet | Smartsheet | weekly | MEDIUM | L | CO module (out of scope for OMEGA) |
| P9 | Equipment scheduled to my project tomorrow? | Spreadsheet | MASCI dispatch (partial) | nightly | HIGH | S | dispatch future-day filter |

---

# 7 · OPERATIONS MANAGER

## Questions Answered Today

- ✅ Fleet-wide Live Operations Snapshot (158 GPS-enabled · 94 not reporting · 53 active drivers · 1 critical fault · etc.)
- ✅ Dispatch strip (216 active assignments · 16 active drivers · 121 active equipment)
- ✅ Motive Mapping Health / Trust Score (70.2%)
- ✅ Recent high-priority events feed

## Questions NOT Answered Today

| # | Question | Workaround | Source | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|--------|-----------|--------|--------|--------------|
| O1 | Fleet utilization % (active hours / available hours)? | Spreadsheet | Motive + dispatch_assignments | daily | HIGH | M | aggregation only |
| O2 | Top-10 trucks by tonnage today? | FleetWatcher | FleetWatcher | daily | HIGH | M | FW-1 |
| O3 | Plant comparison (tons / cost / yield by plant)? | FleetWatcher + Excel | FleetWatcher + Vista | weekly | HIGH | M | FW-1 + Vista |
| O4 | Fleet KPI: avg cycle time / cost per ton? | FleetWatcher | FleetWatcher | weekly | HIGH | M | FW-1 |
| O5 | Driver KPI scorecard (loads, tons, harsh, cost per ton)? | Multi-system manual export | Motive + FleetWatcher | monthly | HIGH | M | FW-1 + DCP-1 production tab |
| O6 | Real-time fleet "Where is everyone?" map view? | Open Motive | Motive (already wired) | daily | HIGH | S | map-centric dashboard layer over fleet-gps |
| O7 | Idle truck cost rollup? | Excel | Motive idle minutes + cost model | weekly | MEDIUM | M | idle-cost rollup |
| O8 | Cross-system trust dashboard (Motive · MaintainX · FleetWatcher health)? | Phone calls to IT | Each system separately | weekly | MEDIUM | S | extend existing trust pill to multi-system |

---

# 8 · EXECUTIVE LEADERSHIP

## Questions Answered Today

- ✅ Motive integration trust score (MCC-1D)
- ✅ Operations Center high-level rollup
- ✅ Outstanding mapping gaps

## Questions NOT Answered Today

| # | Question | Workaround | Source | Frequency | Impact | Effort | Dependencies |
|---|----------|-----------|--------|-----------|--------|--------|--------------|
| E1 | Revenue per truck per day? | Excel | Vista + FleetWatcher | weekly | HIGH | L | FW-1 + Vista |
| E2 | Active vs idle asset count fleetwide? | Phone | Motive (already wired — needs simple count) | daily | HIGH | S | derive from existing data |
| E3 | YTD safety incident trend? | Quarterly meeting deck | incidents + spreadsheet | quarterly | HIGH | M | trend aggregation |
| E4 | Workforce headcount / turnover trend? | HR spreadsheet | employees collection + history | monthly | HIGH | M | employee history rollup |
| E5 | Project profitability snapshot? | Vista | Vista | weekly | HIGH | L | Vista bridge |
| E6 | Cross-job equipment allocation balance? | PM phone calls | dispatch + jobs | weekly | MEDIUM | M | allocation matrix |
| E7 | "How is the company doing today?" single-screen exec summary? | Weekly Monday meeting | All systems | daily | HIGH | M | exec dashboard layer over existing data |

---

# CROSS-ROLE GAP MATRIX

Same data signal · how many roles want it:

| Signal                           | Dispatch | Shop | HR | Safety | Super | PM | Ops | Exec | Roles |
|---------------------------------|:--------:|:----:|:--:|:------:|:-----:|:--:|:---:|:----:|:-----:|
| FleetWatcher load tickets       |    ✅    |  —   | —  |   —    |  ✅   | ✅ | ✅  |  —   |   4   |
| Per-project daily production    |    —     |  —   | —  |   —    |  ✅   | ✅ | ✅  |  ✅  |   4   |
| HOS clock / break status        |    ✅    |  —   | ✅ |   ✅   |  ✅   | —  | —   |  —   |   4   |
| Open MaintainX work orders      |    ✅    |  ✅  | —  |   —    |  —    | ✅ | ✅  |  —   |   4   |
| Fleet utilization / idle stats  |    ✅    |  ✅  | —  |   —    |  —    | —  | ✅  |  ✅  |   4   |
| Future-day dispatch view        |    ✅    |  ✅  | —  |   —    |  ✅   | ✅ | —   |  —   |   4   |
| Daily report / project status   |    —     |  —   | —  |   —    |  ✅   | ✅ | ✅  |  ✅  |   4   |
| Driver scorecard / KPI          |    —     |  —   | ✅ |   ✅   |  —    | —  | ✅  |  ✅  |   4   |
| Document expirations 60–90d     |    —     |  —   | ✅ |   ✅   |  —    | —  | —   |  —   |   2   |
| Plant production / yield        |    —     |  —   | —  |   —    |  —    | ✅ | ✅  |  ✅  |   3   |
| Vista cost / profitability      |    —     |  —   | —  |   —    |  —    | ✅ | ✅  |  ✅  |   3   |

Multi-role signals get priority. **FleetWatcher tickets**, **HOS clock**, **MaintainX work orders**, **Future-day dispatch**, and **Daily project production** each serve 4 roles — these are the highest-leverage gaps.

---

# TOP 25 OPERATIONAL GAPS · OMEGA RANKED

| Rank | Gap | Pwr | Spl | Beu | Trs | Prv | Comp | Tier |
|:----:|-----|:---:|:---:|:---:|:---:|:---:|:----:|:----:|
| 1    | D1 / P1 — FleetWatcher ticket data into MASCI Docs | 10 | 5 | 9 | 6 | 5 | 35 | **P0** |
| 2    | D9 / S1 — Open MaintainX work orders surfaced beyond readiness | 9 | 8 | 9 | 9 | 9 | 44 | **P0** |
| 3    | D7 / S6 / P9 — Future-day dispatch view (tomorrow / this week) | 9 | 9 | 9 | 9 | 9 | 45 | **P0** |
| 4    | D8 / H1 — HOS clock decorated for MASCI (break / on-duty / available) | 9 | 7 | 8 | 9 | 7 | 40 | **P0** |
| 5    | O6 — Fleet map view ("Where is everyone?") | 8 | 7 | 9 | 9 | 8 | 41 | **P0** |
| 6    | D6 — Vehicle ETA to current job | 8 | 6 | 8 | 7 | 6 | 35 | **P1** |
| 7    | H2 — Document expirations 60 / 90 day window | 8 | 10 | 9 | 10 | 10 | 47 | **P0** |
| 8    | SF7 — Operator certification × equipment assignment cross-check | 9 | 8 | 9 | 9 | 9 | 44 | **P0** |
| 9    | E2 — Exec single-screen summary (cross-portal rollup) | 8 | 8 | 9 | 8 | 8 | 41 | **P1** |
| 10   | O1 — Fleet utilization % rollup | 7 | 7 | 8 | 8 | 8 | 38 | **P1** |
| 11   | SF1 — Fleetwide harsh-event trend chart | 7 | 8 | 9 | 9 | 9 | 42 | **P1** |
| 12   | SU1 — Crew-by-site daily roster | 8 | 8 | 8 | 8 | 8 | 40 | **P1** |
| 13   | H3 — Cross-driver scorecard | 7 | 7 | 8 | 8 | 8 | 38 | **P1** |
| 14   | O8 — Multi-system trust pill (MaintainX + FleetWatcher health beside Motive) | 7 | 8 | 9 | 7 | 8 | 39 | **P1** |
| 15   | SF2 — Incident rate by jobsite | 7 | 7 | 8 | 8 | 8 | 38 | **P1** |
| 16   | D5 / H1 — HOS / break-status surfaced on dispatch row | 7 | 6 | 7 | 8 | 7 | 35 | **P1** |
| 17   | S2 / S3 — MaintainX next-PM date + lifetime cost | 7 | 6 | 7 | 7 | 7 | 34 | **P2** |
| 18   | H5 — PTO / scheduled time-off visibility | 7 | 6 | 7 | 6 | 6 | 32 | **P2** |
| 19   | H6 — Light-duty / restricted-work flag | 7 | 7 | 7 | 7 | 6 | 34 | **P2** |
| 20   | SF8 — Motive AI Coach decoration into DCP-1 | 6 | 5 | 7 | 7 | 6 | 31 | **P2** |
| 21   | P2 / O3 — Material mix + plant comparison (Command Cloud Mix Design) | 7 | 4 | 7 | 6 | 4 | 28 | **P2** |
| 22   | SF3 — Toolbox-talk completion log | 6 | 6 | 7 | 7 | 7 | 33 | **P2** |
| 23   | E1 / P5 / P6 — Vista revenue / profitability bridge | 9 | 3 | 6 | 5 | 3 | 26 | **P3** |
| 24   | SF5 — OSHA 300/301 generator | 7 | 4 | 6 | 6 | 5 | 28 | **P3** |
| 25   | P8 — Change-order log module | 7 | 3 | 5 | 4 | 3 | 22 | **P4** |

---

# P0 – P4 TIERS · OPERATIONAL VALUE ONLY

### P0 — Build next sprint (highest daily-pain reduction)
- **G7** Document expirations 60/90-day extension (1-line config change — 10/10 simplicity)
- **G3** Future-day dispatch view
- **G8** Operator-certification × equipment-assignment cross-check (Safety blocker)
- **G2** MaintainX open work-orders surfaced on Dispatch + Shop
- **G4** HOS clock decoration (D8 / H1)
- **G5** Fleet map view
- **G1** FleetWatcher Ticket Ingest (FW-1 — only after operator answers FWA-1 questions 1, 3, 4)

### P1 — Build in the 30-60 day window
- G6 Vehicle ETA, G9 Exec summary, G10 Fleet utilization, G11 Harsh-event trend, G12 Crew-by-site, G13 Driver scorecard, G14 Multi-system trust pill, G15 Incident rate by site, G16 Dispatch HOS row

### P2 — 60-90 day window
- G17 PM date / cost, G18 PTO, G19 Light-duty, G20 AI Coach, G21 Mix / plant, G22 Toolbox-talk log

### P3 — Beyond 90 days
- G23 Vista bridge (largest enterprise-system integration — high value, very high effort)
- G24 OSHA form generator

### P4 — Backlog
- G25 Change-order module · workflow engines · M-2 / M-3

---

# RECOMMENDED NEXT SPRINT

Pick the **two highest-impact lowest-effort** gaps from P0:

1. **DocExp-60/90** (#7) — 10/10 Simple. Pure UI change on the existing
   DCP-1 + HR portal. No new collections, no schema. Closes a regulatory
   gap.
2. **Future-Day Dispatch View** (#3) — existing `dispatch_assignments`
   already carries `assigned_at`; the gap is a filter + viewport, not a
   data model.

Together these clear two top-10 gaps with the smallest possible diff.

Defer **FW-1** until the FleetWatcher operator-verification questions
(license tier · outbound mechanism · auth) are answered — see
`/app/memory/FWA1_CAPABILITY_MATRIX.md` §6.

---

# RECOMMENDED 90-DAY ROADMAP (OPERATIONAL VALUE ORDER, NOT TECHNICAL EASE)

**Days 1–14** (Sprint A — P0 quick-wins): DocExp-60/90 · Future-Day Dispatch · MaintainX open-WO surfacing.

**Days 15–35** (Sprint B — Safety / HR cross-cuts): Operator-cert × equipment cross-check · HOS clock decoration · Fleet map view.

**Days 36–60** (Sprint C — FleetWatcher gating): FW-1 Ticket Ingest (operator-verification gate must clear first).

**Days 61–90** (Sprint D — Executive surfacing): Exec single-screen rollup · Fleet utilization · Harsh-event trend.

---

# WHAT THE PLATFORM DOES WELL

- Single source of truth for **driver/vehicle/safety** telematics
  (Motive M-1 / M-1R · P1 · P1.5 · P1.6 · OIS-1 · DSI-1).
- Single Driver Command Profile (DCP-1) reused across four portals
  with server-side role redaction.
- Operational language only — zero raw payload exposure.
- Mapping cleanup workflow self-served by HR (MCC-1 + HR extension)
  without admin escalation.
- Universal Green / Amber / Red health language across GPS, Gateway,
  DVIR, Fault (DSI-1F).
- Read-only discipline preserved across every sprint — no automation,
  no workflow mutation, no portal sprawl.

# WHAT THE PLATFORM STILL CANNOT DO (PLAIN ENGLISH)

- Tell a dispatcher which load is on which truck right now.
- Tell a PM how many tons their project received today.
- Tell HR who's expiring in the next 60 days (only 30d is exposed).
- Tell a superintendent which crew is on which jobsite today.
- Tell an executive "how is the company doing today" in one screen.
- Show a live fleet map.
- Cross-check "is this operator certified for the equipment they're
  driving?"
- Show open MaintainX work orders alongside the readiness tile.
- Show tomorrow's dispatch.
- Decorate HOS clock state ("on-break" / "available" / "at-risk").

# WHAT SHOULD **NOT** BE BUILT NEXT

- Change-order module (P4 — out of scope for OMEGA discipline).
- Vista bridge (P3 — very large, multi-quarter undertaking).
- WhatsApp / Training Center / OCR (still backlog deferred under
  OMEGA — none of these close a top-10 gap).
- M-2 webhook router (still deferred — would introduce automation
  that OMEGA explicitly bans until visibility layer is fully proven).
- M-3 geocode (deferred — not a top-25 operational gap).
- Speculative architecture / new portals — every gap above can be
  closed inside an existing portal.

---

## Final Verdict

🟢 **OGA-1 OPERATIONAL GAP ANALYSIS COMPLETE**

Top operational pain that MASCI Docs still cannot relieve, in
operational-value order:

1. FleetWatcher tickets (gated on operator verification).
2. MaintainX work-order detail beyond readiness.
3. Future-day dispatch visibility.
4. HOS clock decoration.
5. Live fleet map view.
6. Document expiration windows 60/90.
7. Operator-certification × equipment cross-check.

Recommended Sprint A (next 14 days) — DocExp-60/90 + Future-Day
Dispatch + MaintainX-open-WO — delivers the three highest-leverage
lowest-effort gaps simultaneously with zero new collections and zero
new portals.

— Forked main agent · 2026-06-08
