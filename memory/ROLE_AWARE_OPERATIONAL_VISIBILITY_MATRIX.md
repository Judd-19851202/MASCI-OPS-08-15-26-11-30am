# ROLE-AWARE OPERATIONAL VISIBILITY MATRIX

_Phase ODR-Governance Extension · Companion Artifact · 2026-05-29_

This artifact provides the **per-system × per-FLL** detailed
visibility matrix described in
`FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md § 3` — with the operational
rationale behind each cell.

**Architecture only. No implementation.**

Verb legend: **FULL** · **LIMITED** · **SUMMARY** · **NONE**.

---

## 1 · System inventory (17 systems audited)

ODR · Constraints · Operational Timeline · Photos · Daily Reports
(legacy) · Safety · Fleet · Dispatch · Meetings · Inspections ·
Incidents · Training · Readiness · Future RFI · Future Schedule ·
Operational Search · Field Memory.

---

## 2 · Master matrix (compact)

| System | FLL-1 Foreman | FLL-2 GF | FLL-3 Super | FLL-4 Sr Super | FLL-5 PM | FLL-6 Ops Leader |
|---|---|---|---|---|---|---|
| **ODR (own)** | FULL | FULL (own crews) | FULL (project) | FULL (region) | LIMITED (read-only consumption) | SUMMARY |
| **Constraints** | LIMITED (own work) | LIMITED (own crews) | FULL (project) | FULL (region) | FULL (cost/contract lens) | SUMMARY |
| **Operational Timeline** | LIMITED (own crew events) | LIMITED (own crews) | FULL (project) | FULL (region) | LIMITED (PM-relevant events) | SUMMARY |
| **Photos** | LIMITED (own ODR) | LIMITED (own crews' photos) | FULL (project) | FULL (region) | LIMITED (evidence-tagged: delay/extra-work/safety) | SUMMARY |
| **Daily Reports (legacy)** | LIMITED (own) | LIMITED (own crews) | FULL (project) | FULL (region) | LIMITED (consumption) | SUMMARY |
| **Safety** | LIMITED (own crew · today) | LIMITED (own crews) | FULL (project) | FULL (region) | LIMITED (incident + claims lens) | SUMMARY |
| **Fleet** | LIMITED (today's assets) | LIMITED (own crews' assets) | FULL (project) | FULL (region) | LIMITED (cost lens) | SUMMARY |
| **Dispatch** | LIMITED (today + tomorrow) | LIMITED (3-day) | FULL (project) | FULL (region) | LIMITED (consumption) | SUMMARY |
| **Meetings** | LIMITED (own meetings) | LIMITED (own crews) | FULL (project) | FULL (region) | LIMITED (PM-attended) | SUMMARY |
| **Inspections** | LIMITED (own work areas) | LIMITED (own crews' areas) | FULL (project) | FULL (region) | LIMITED (quality + cost lens) | SUMMARY |
| **Incidents** | SUMMARY (today's events) | LIMITED (own crews) | FULL (project) | FULL (region) | LIMITED (claims + contract lens) | SUMMARY |
| **Training** | LIMITED (own certs · today's required topics) | LIMITED (own crews' certs) | FULL (project) | FULL (region) | NONE (HR-adjacent) | SUMMARY (compliance health) |
| **Readiness** | LIMITED (own ODR coaching) | LIMITED (own crews' coaching · aggregated) | FULL (project) | FULL (region) | SUMMARY (project trend) | SUMMARY (org trend) |
| **Future RFI** | NONE | LIMITED (related-to-own-work RFIs) | FULL (project) | LIMITED (regional cross-project RFI exposure) | FULL (PM owns response) | SUMMARY |
| **Future Schedule** | LIMITED (today/tomorrow) | LIMITED (3-day lookahead) | FULL (project lookahead) | FULL (regional resource conflicts) | FULL (critical path · contract milestones) | SUMMARY |
| **Operational Search** | LIMITED (own scope) | LIMITED (own crews' scope) | FULL (project) | FULL (region) | FULL (PM-relevant scopes) | SUMMARY |
| **Field Memory** | LIMITED (own crew · own project) | LIMITED (own crews · own project) | FULL (project history) | FULL (regional history) | LIMITED (PM-relevant patterns) | SUMMARY |

---

## 3 · Cell-by-cell rationale (highlights)

The full rationale per cell is too long for this document; the
following are the **operational thesis statements** behind each
verb assignment for the most-asked systems.

### 3.1 ODR

- **FLL-1 FULL on own ODR** — the foreman owns their crew's daily
  record. They see everything they entered + readiness coaching for
  their own report. They never see other foremen's reports.
- **FLL-2 FULL on own crews** — coordination requires seeing all
  the day's ODRs across the crews they manage.
- **FLL-3 FULL on project** — the Superintendent is the project
  command center; they need full ODR visibility to amend, return,
  approve.
- **FLL-4 FULL on region** — Senior Super needs cross-project
  visibility, but their default landing page is still aggregated.
- **FLL-5 LIMITED (read-only consumption)** — PM is a consumer per
  O22; they search, export, view trends. They do not see edit /
  amend / approve affordances. They do not see per-foreman readiness
  coaching.
- **FLL-6 SUMMARY** — Operations Leadership reads org-wide trends:
  completion rate · readiness rate · constraint frequency. They do
  not browse individual ODRs by default.

### 3.2 Constraints

- **FLL-1 LIMITED** — only constraints attached to the foreman's
  own work area / crew. A utility conflict at a distant phase of
  the project is noise.
- **FLL-2 LIMITED** — own crews' constraints + immediate adjacent
  work.
- **FLL-3 FULL** — Superintendent owns project-wide constraint
  management.
- **FLL-5 FULL with cost/contract lens** — PM owns constraint cost
  exposure + contract documentation; they see the same constraints
  Super sees but with cost/contract overlays.
- **FLL-6 SUMMARY** — top recurring constraint patterns across the
  company; not individual constraint rows.

### 3.3 Operational Timeline

- **FLL-1 LIMITED** — only events involving the foreman's own crew.
- **FLL-3 FULL** — Superintendent reads the entire project
  timeline.
- **FLL-5 LIMITED** — PM sees the events that affect their
  contractual / cost concerns (delays, extra work, key inspections,
  RFI events). The PM does not see crew-level chatter (e.g., "JHA
  signed at 06:14").
- **FLL-6 SUMMARY** — timeline volume by project, not raw events.

### 3.4 Safety

- **FLL-1 LIMITED** — own crew · today's events · toolbox topics
  required today.
- **FLL-3 FULL** — Super sees all project safety events,
  incidents, observations, near-misses.
- **FLL-5 LIMITED (claims lens)** — PM sees incidents with claims
  / contractual implications + their photo evidence. PM does not
  see near-miss observation noise.

### 3.5 Future RFI

- **FLL-1 NONE** — foreman does not see RFIs by default. The
  foreman submitted the underlying ODR that may have surfaced the
  question; the RFI lifecycle is owned upstream.
- **FLL-2 LIMITED** — only RFIs related to work in the GF's
  current coordination window.
- **FLL-3 FULL** — Super manages RFI lifecycle from project side.
- **FLL-4 LIMITED** — cross-project RFI exposure for resource /
  schedule conflict detection.
- **FLL-5 FULL** — PM owns RFI response, status, contractual
  consequence.
- **FLL-6 SUMMARY** — RFI volume / age / cycle-time trends.

### 3.6 Future Schedule

- **FLL-1 today + tomorrow** — operationally that is the only
  horizon the foreman needs.
- **FLL-2 3-day lookahead** — coordination horizon.
- **FLL-3 project lookahead** — Super owns the operational lookahead.
- **FLL-4 regional resource conflicts** — Senior Super arbitrates
  when projects compete for the same crew / equipment.
- **FLL-5 critical path + contract milestones** — PM owns
  schedule-as-contract.
- **FLL-6 SUMMARY** — schedule health trends.

### 3.7 Field Memory

- Mirror visibility of the records Memory stores. Memory cannot
  escalate visibility (V12). A pattern detected from data that
  FLL-1 cannot see in raw form must not surface a FULL-detail
  pattern to FLL-1 either.

---

## 4 · Mid-tier rules (interpretive)

- **LIMITED ≠ partial-field.** LIMITED means scoped rows (e.g.,
  "only this crew's constraints"), not a partial view of every
  row in the system. Field-level redaction within a row is rare
  and handled case-by-case.
- **SUMMARY is never per-foreman.** Per V11, every SUMMARY view is
  aggregated. A FLL-6 leader sees "constraint frequency by
  category", not "Carlos Reyes has 3 constraint rows."
- **NONE is total.** A FLL-N surface that has NONE for a system
  shows zero affordance, zero search hits, zero deep-link results
  for that system. The role does not learn that data exists.
- **Cross-system queries inherit the strictest visibility.** A
  combined search across ODR + Safety must apply the role's
  visibility for both systems and surface only the intersection
  the role is permitted to see.

---

## 5 · Doctrine anchors (V1–V20 in this matrix)

| Doctrine | Anchor |
|---|---|
| V2 four verbs labeled | every cell labeled |
| V5 no cross-role leakage | § 4 cross-system inheritance rule |
| V6 PM ≠ more, ≠ MORE | § 3.1 ODR + § 3.2 Constraints (PM cost/contract lens vs Super operational lens) |
| V8 foreman today + tomorrow | § 3.6 Schedule |
| V9 timeline 3 failures prevented | dedicated artifact `TIMELINE_ROLE_VISIBILITY_STANDARD.md` |
| V11 SUMMARY never per-foreman | § 4 mid-tier rule |
| V12 Memory cannot escalate | § 3.7 |
| V13 RFI tracks the work | § 3.5 |
| V14 Schedule by horizon | § 3.6 |
| V16 Senior Super = regional optimization | § 3 multiple |

_End of Role-Aware Operational Visibility Matrix._
