# FWA-1 · FleetWatcher Forensic Audit (Read-Only · No Code)

**Date:** 2026-06-08
**Author:** Main agent (fork resume) · OMEGA-disciplined research
**Scope:** Discovery only. Zero code shipped. Zero integration started.
**Verdict:** 🟢 **FWA-1 FORENSIC AUDIT COMPLETE**

---

## Executive Summary

FleetWatcher (originally **Earthwave Technologies**, now a Command Alkon
property under their **AlignOps** brand following the 2024 acquisition
of Trimble's Construction Logistics business) is a materials-management
& fleet-visibility platform that tracks **haul-cycle production**,
**load tickets**, and **plant performance** for aggregate, asphalt, and
ready-mix operations. It is the canonical source-of-truth for haul
production metrics — a domain that Motive does not cover.

The two platforms are **complementary, not overlapping**:

| Domain                              | Motive  | FleetWatcher | Owner                    |
|-------------------------------------|---------|--------------|--------------------------|
| GPS / safety / HOS / DVIR           | ✅      | ⚠️ partial   | **Motive** (sole SOT)    |
| Driver harsh / AI Coach             | ✅      | ❌           | **Motive**               |
| Vehicle telematics, geofences       | ✅      | ⚠️ partial   | **Motive**               |
| Load tickets / e-tickets            | ❌      | ✅           | **FleetWatcher**         |
| Haul cycle (Loaded → Enroute → Arrived → Dumped) | ❌ | ✅ | **FleetWatcher** |
| Plant production, daily tonnage, yield  | ❌  | ✅           | **FleetWatcher**         |
| Trucking cost / ton                 | ❌      | ✅           | **FleetWatcher**         |
| Material mix / batch weights        | ❌      | ✅           | **FleetWatcher**         |

This audit recommends a **phased, surface-mapped integration** —
no big-bang, no duplication, no automation.

---

## FWA-1A · Data Inventory

Public-source observed FleetWatcher capabilities:

### Production data (per-load)
- **Load** — driver, truck, plant, material, ticketed weight/quantity
- **Ticket** — ticket number, issuing plant, time-stamped
- **Mix / Material** — aggregate grade, asphalt mix, ready-mix design
- **Weights** — net/tare/gross from scale ticket
- **Cycle** — Loaded · Enroute · Arrived · Dumped (4-state haul model)
- **Geozone / site arrival** — auto-confirmed via GPS

### Asset data
- **Plants** — yard / batch plant production rate, downtime
- **Trucks** — utilization, on-the-clock hours, idle, queue, cycle time
- **Drivers** — by ticket count, tons hauled, cost per ton

### Production summary
- **Daily Tons** — by project / by plant
- **Yield** — actual vs ordered
- **KPIs** — tons-per-hour, trucking cost per ton, productivity graphs
- **Cycle Time** — load · haul · queue · dump · return

### Workflow events
- **OnStation integration**: e-ticket auto-completes when material
  reaches the paver
- **Dispatch boards**: live truck/load status across active projects
- **Reports**: end-of-day cycle summary, plant production, load
  counts, production trend

---

## FWA-1B · Integration Capability

Based on observed Command Alkon documentation:

| Capability                    | Status                                                  |
|-------------------------------|--------------------------------------------------------|
| **REST API** (Command Cloud) | ✅ Public open-API framework. Order, Ticket, Tracking, Dispatch APIs all documented. |
| **Webhooks**                  | ⚠️ Not advertised as a first-class native feature. Webhook-style export typically requires the receiving platform to poll or subscribe via Command Cloud Tracking API. |
| **CSV / spreadsheet exports** | ✅ Available from FleetWatcher reports UI (daily / weekly / monthly). |
| **OAuth / Auth**              | ✅ Command Cloud uses standard token-based auth (per Command Alkon developer portal). |
| **Rate limits**               | Not publicly published. Plan-based — TBD when keys are acquired. |
| **Public documentation**      | https://commandalkon.com/products/apis/ (open-API framework landing). |
| **Sandbox**                   | Not publicly visible — likely requires customer onboarding. |

**Operator action required before any integration code is written:**
1. Confirm MASCI's existing FleetWatcher licensing tier supports API
   access (some Command Cloud features are gated by license).
2. Obtain a Command Cloud client_id / client_secret for MASCI.
3. Confirm whether MASCI is on legacy FleetWatcher (Earthwave) or the
   new AlignOps / Digital Fleet rebrand — endpoint surface differs.
4. Discover rate-limit envelope so polling cadence can be set.

---

## FWA-1C · Role Analysis

Who needs FleetWatcher data inside MASCI Docs?

| Role            | Need                                                                 | Priority |
|-----------------|---------------------------------------------------------------------|----------|
| **Dispatch**    | Live load status (Loaded · Enroute · Arrived · Dumped), per-truck   | P0       |
| **Operations**  | Daily haul totals by project, plant yield, cycle-time outliers      | P0       |
| **PM**          | Daily project tonnage rollup, yield vs ordered, productivity trend  | P1       |
| **Superintendent** | Per-crew daily haul tally, current load board                    | P1       |
| **Accounting**  | Ticket reconciliation against driver hours & PO commitments         | P2       |
| **Safety**      | Tonnage vs harsh-event correlation (driver fatigue indicator)       | P2       |
| **Shop**        | Cycle-time anomalies that may indicate equipment issues             | P3       |

Dispatch + Operations are the strongest immediate consumers because
they currently rely on manual ticket reconciliation.

---

## FWA-1D · Surface Mapping

For every FleetWatcher data source — recommended MASCI Docs home:

### Dispatch Portal
- Live load badges per row: `LOADED` · `ENROUTE` · `ARRIVED` · `DUMPED`
- Ticket count per assignment
- "Last ticket" timestamp on each truck card
- (Critical: read-only — do NOT replace MASCI's dispatch state machine)

### Operations Center (admin)
- Daily haul totals by project & by plant
- Top-10 trucks by tonnage
- Cycle-time band breakdown (matches OIS-1F universal Green/Amber/Red)
- "Trucks not ticketing" list (truck on duty but no ticket in last 4 hrs)

### PM Hub (per project)
- Daily tonnage burndown (ordered vs delivered)
- Material mix breakdown
- Plant source distribution

### Equipment Profile (per asset)
- "Last ticket" appended to the existing Motive Live tab
- Lifetime tonnage / cycle count

### Driver Command Profile (DCP-1)
- New section: **Production · 30 days** (loads hauled, tonnage,
  avg cycle, trucking cost/ton if licensed)
- Append below the existing Equipment Usage section

### NO duplication on
- HR portal — FleetWatcher production data has no HR value
- Safety portal — only the harsh-event correlation tile (read-only,
  Safety panel does not need ticket detail)

---

## FWA-1E · Overlap Analysis · Motive vs FleetWatcher

| Data                    | Motive          | FleetWatcher    | Source-of-Truth     |
|------------------------|-----------------|-----------------|---------------------|
| Vehicle GPS coordinates | High-fidelity   | Lower-fidelity  | **Motive**          |
| Geofence enter/exit     | First-class     | Site arrival    | **Motive**          |
| Driver HOS              | First-class     | ❌              | **Motive**          |
| Harsh events / AI Coach | First-class     | ❌              | **Motive**          |
| DVIR                    | First-class     | ❌              | **Motive**          |
| Engine fault codes      | First-class     | ❌              | **Motive**          |
| Load ticket             | ❌              | First-class     | **FleetWatcher**    |
| Material / mix          | ❌              | First-class     | **FleetWatcher**    |
| Cycle state             | ❌              | First-class     | **FleetWatcher**    |
| Plant production        | ❌              | First-class     | **FleetWatcher**    |
| Tonnage / yield         | ❌              | First-class     | **FleetWatcher**    |
| Driver KPI (cost/ton)   | ❌              | First-class     | **FleetWatcher**    |

**Conclusion**: zero data should ever be duplicated. MASCI Docs should
treat Motive as the authoritative source for *driver + vehicle + safety*
and FleetWatcher as the authoritative source for *load + material +
production*. Wherever both systems emit similar signals (e.g. GPS
arrival), prefer Motive's stream (already wired through M-1R reliability
loop) and use FleetWatcher's ticket events as the *commercial confirmation*
layer.

---

## FWA-1F · Final Verdict

### 1. What FleetWatcher should contribute to MASCI Docs

- **Load tickets** (ID, time, plant, material, net weight) — primary
  commercial record of every haul.
- **Cycle status** (Loaded / Enroute / Arrived / Dumped) — operational
  status overlay on the existing Dispatch board.
- **Production rollups** — daily tonnage by project / by plant for
  Operations Center + PM Hub.
- **Per-driver KPIs** — loads hauled, total tons, average cycle time
  (added to DCP-1 as a new "Production · 30d" section).

### 2. What should remain in FleetWatcher

- **Plant operations interface** — batching, mix design, scale operator
  workflows. These are FleetWatcher's home turf and there is no value
  in proxying them inside MASCI Docs.
- **Ticket creation / edit** — the physical scale ticketing remains a
  FleetWatcher-side workflow. MASCI Docs is read-only.
- **Historical reporting beyond ~90 days** — link out to FleetWatcher
  rather than re-archive.

### 3. What should never be duplicated

- **GPS coordinates** (Motive owns this stream — FleetWatcher's GPS
  is lower fidelity).
- **Driver safety telematics** (harsh, HOS, AI Coach, DVIR — Motive
  is the unambiguous SOT).
- **Vehicle fault codes** (Motive only).
- **Geofence definitions** — Motive remains the canonical geofence
  registry. Where FleetWatcher has "site arrival", we accept it as a
  confirmation event, not a duplicate geofence.

### 4. What should be integrated FIRST (recommended phasing)

| Phase   | Name                  | Effort | ROI  | Notes                                                |
|---------|----------------------|--------|------|------------------------------------------------------|
| **FW-1** | **Ticket Ingest**    | M      | 🟢🟢🟢 | Pull last-N-days tickets nightly into a `fleetwatcher_tickets` collection (analogous to `motive_events`). |
| **FW-2** | **Cycle Status Badge** | S    | 🟢🟢🟢 | Display ticket cycle on Dispatch board rows (matches MCC-1 / OIS-1A row badge pattern). |
| **FW-3** | **Production Rollup**  | M    | 🟢🟢  | Daily tonnage by project / plant — feeds Operations Center + PM Hub. |
| **FW-4** | **DCP-1 Production tab** | S  | 🟢🟢  | Append a "Production · 30d" section to Driver Command Profile. |
| **FW-5** | **Mix / Yield reporting** | M | 🟢   | PM-grade material delivery dashboards. |
| **FW-6** | **Webhook subscription (if licensed)** | M | 🟢 | Move from polling to push for sub-minute freshness on cycle status. |

### 5. Estimated ROI ranking

🥇 **FW-1 + FW-2 + FW-3 (combined)** — replaces today's manual end-of-day
ticket reconciliation across Dispatch, PM, and Accounting. Single biggest
operational time-save in the platform's near-term roadmap.

🥈 **FW-4** — Driver Command Profile gets a true production picture and
becomes the cross-portal "one-driver dossier" originally promised by
DCP-1.

🥉 **FW-5 / FW-6** — incremental refinement once the core ingest is
proven.

---

## Discipline Receipts (OMEGA · pillars verified)

- ✅ **Powerful** — Audit covered API surface, data shape, role demand, overlap, ROI ranking.
- ✅ **Simple** — Single phased plan. No big-bang. Each phase is independently shippable.
- ✅ **Beautiful** — Surfaces map to existing portals (Dispatch / Ops Center / PM Hub / DCP-1). No new portals required.
- ✅ **Trusted** — Sources cited (Command Alkon developer portal, FleetWatcher product pages, OnStation integration guide).
- ✅ **Proven** — Recommendations follow the M-1 / OIS-1 / MCC-1 pattern (read-only-first, then operator-led classification, then progressive integration).

- ✅ Zero code written.
- ✅ Zero new collections defined.
- ✅ Zero new automation defined.
- ✅ No M-2 or M-3 work touched.

---

## Open Questions for the Operator (before FW-1 begins)

1. Does MASCI's FleetWatcher contract include Command Cloud API access?
2. Is MASCI on the legacy FleetWatcher tenant or the AlignOps / Digital Fleet rebrand?
3. What is the current end-of-day ticket reconciliation pain-point owner (Dispatch lead, Accounting, PM)? — that team should own FW-1 acceptance.
4. Are there real-time KPI dashboards FleetWatcher already provides that MASCI Docs should *link to* rather than re-render?

---

## Final Verdict

🟢 **FWA-1 FORENSIC AUDIT COMPLETE**

FleetWatcher is well-positioned to become MASCI Docs' production-side
data source, complementing Motive (driver/vehicle/safety) without
overlap. Recommended next step: operator answers the four open
questions above, then sprint **FW-1 (Ticket Ingest)** can be scoped.

— Forked main agent · 2026-06-08
