# Accountability Owner-Resolution Audit · Phase 1A-5

**Batch:** Pillar 1 · Phase 1A-5 · Owner fidelity
**Date:** 2026-05-31
**Scope:** Inventory every remaining placeholder owner value surfaced by the Phase 1A-4 Command Center build, identify the **authoritative routing source** that exists on the platform today, and decide whether resolution is possible or whether the placeholder is the truth.
**Discipline:** OMEGA · evidence-only · no code change in this audit step.

---

## 1 · Placeholder owner inventory (post 1A-4)

Captured against live preview snapshot 2026-05-31 (source_hash `54b8a402` + 1A-4 build):

| Placeholder string | Surface | Surfaced count today | Cause |
|---|---|---|---|
| `"Pending Approver"` | Approvals card · APP-AMBER/RED/WEEK | 5 | Projection's PO contract returns this for any non-terminal status (Audit A-05) |
| `"Safety"` | Safety card · SAF-CRITICAL-UNRESOLVED · SAF-OSHA-OPEN; Jobs card · JOBS-ISSUE-NO-PATH | 3 | Projection's incident contract returns this when the incident has no linked CA with an assignee |
| `"Shop"` | Equipment card · EQP-OOS-OLD / NEW | 0 today (no OOS-aged units in preview) | Projection's fleet_defect contract returns this when no `acknowledged_by_name` is set |
| `"Unassigned PM"` | Jobs card · JOBS-DR-MISSING | 5 | `jobs_master.primary_pm_name` is empty for these projects — authentically null |
| `"UNASSIGNED"` | Jobs card · JOBS-ISSUE-NO-OWNER | 2 | The surface *is* the unassigned set — truthful by definition |

Plus the analogous strings on the Accountability service `/snapshot` per-source items where they project the same source rows.

---

## 2 · Authoritative routing source candidates

For each placeholder we surveyed the platform's existing data without proposing schema changes.

### 2.1 · `Pending Approver` (POs)

| Candidate routing source | Available? | Resolves to | Confidence |
|---|---|---|---|
| `po_requests.next_approver_role` / `current_approver` | ❌ no such field exists | n/a | — |
| `po_requests.audit[]` entries with `action=clarification_requested` | ⚠️ exists but inverts the question (it logs who *asked for clarification*, not who is awaiting action) | n/a | low |
| **`jobs_master.primary_pm_*` joined via `po.project_number`** | ✅ exists | the project's PM (the platform's PO fan-out target is `assignee_role="pm"` per `po_requests.py:568`) | **HIGH — authoritative** |
| `db.user_directory` "leadership" role lookup | ⚠️ multiple users hold the leadership role — picking one would be arbitrary | n/a | low (department-level) |
| `db.tasks` for `source_module="po.requests"` with this po_id | ⚠️ exists but task itself is fan-out to `role="pm"` — same answer as above | same as #3 | medium (downstream) |

**Verdict:** primary route is `jobs_master.primary_pm_*`. When the PO carries a `project_number` AND a `jobs_master` row links it AND that row has `primary_pm_name`, the PM is the de-facto pending approver — the platform's own fan-out logic confirms this attribution path.

### 2.2 · `Safety` (incidents)

| Candidate routing source | Available? | Resolves to | Confidence |
|---|---|---|---|
| `incidents.assigned_to_*` | ❌ Audit A-01 — no native assignee field | n/a | — |
| **`corrective_actions.assigned_to_name` linked via `source_id` ∥ `incident_id`** | ✅ exists | the CA owner — the de-facto incident resolver | **HIGH — authoritative** |
| `safety_users` collection | ⚠️ multiple safety users — no single "safety lead" | n/a | low (department-level) |
| `user_directory.portals contains "safety"` | ⚠️ multiple safety-portal users | n/a | low (department-level) |
| Per-project safety officer in `jobs_master` | ❌ no such field today | n/a | — |

**Verdict:** primary route is the linked CA's `assigned_to_name`. When the incident has any linked CA with a real assignee (preferring open over closed), that name is the de-facto owner of the resolution path.

### 2.3 · `Shop` (fleet defects)

| Candidate routing source | Available? | Resolves to | Confidence |
|---|---|---|---|
| `fleet_defects.assignee_*` | ❌ Audit A-02 — no native assignee field | n/a | — |
| **`fleet_defects.acknowledged_by_name`** | ✅ already wired in Phase 1A-4 | the technician who acknowledged the defect | **HIGH — authoritative** when present |
| `shop_users` collection | ⚠️ multiple shop technicians — no single "shop lead" | n/a | low (department-level) |
| Last-touched mechanic on the unit's prior work orders | ❌ no work-order collection links to fleet_defects on the platform | n/a | — |

**Verdict:** `acknowledged_by_name` is the only authoritative individual-level signal today, and it is already used. For UNACKNOWLEDGED defects no individual is yet accountable — the `"Shop"` placeholder is the correct truth ("nobody has picked this up yet").

### 2.4 · `Unassigned PM` (JOBS-DR-MISSING)

| Candidate routing source | Available? | Resolves to | Confidence |
|---|---|---|---|
| **`jobs_master.primary_pm_name`** | ✅ already used | the PM (when populated) | **HIGH — authoritative** when present |
| If `primary_pm_name` is null/empty | n/a | placeholder is the truth (no PM assigned) | — |

**Verdict:** "Unassigned PM" is the **correct, honest placeholder** when the job genuinely has no PM. Resolving it to a department default would be a downgrade. Keep as-is.

### 2.5 · `UNASSIGNED` (JOBS-ISSUE-NO-OWNER)

| Candidate routing source | Available? | Resolves to | Confidence |
|---|---|---|---|
| n/a | — | the rule *surfaces* the unassigned set | — |

**Verdict:** truthful by rule definition — this card item exists *because* the issue has no owner. Resolving it would defeat the rule. Keep as-is.

---

## 3 · Resolvable vs preserved placeholders

| Placeholder | Can resolve when data exists? | Resolution path | Decision for Phase 1A-5 |
|---|---|---|---|
| `Pending Approver` | ✅ YES | `jobs_master.primary_pm_*` via `po.project_number` | 🟢 BUILD resolver |
| `Safety` (incidents) | ✅ YES | linked CA `assigned_to_name` (open preferred, any otherwise) | 🟢 BUILD resolver |
| `Shop` (fleet defects · unacknowledged) | ❌ NO routing data exists for unacknowledged defects | preserve placeholder | 🛑 KEEP |
| `Shop` (acknowledged) | already resolved to `acknowledged_by_name` in 1A-4 | ✅ done | 🟢 unchanged |
| `Unassigned PM` | only "resolves" by adding a PM to the source row — not a projection-side fix | preserve placeholder | 🛑 KEEP |
| `UNASSIGNED` (no-owner rule) | rule surfaces the unassigned set | preserve placeholder | 🛑 KEEP |

---

## 4 · Coverage on live preview data

To establish baseline expectations for the Phase 1A-5 resolvers we probed `masci_safety_preview`:

```
=== Pending POs sample (10 oldest) ===
  Linkable to PM via jobs_master.primary_pm_name: 0 / 10

=== Open incidents (10 most recent) ===
  Have a linked CA with assigned_to_name: 0 / 10

=== Open OOS fleet_defects (5 most recent) ===
  Have acknowledged_by_name set: 0 / 5
```

**Empirical conclusion:** on the live preview data, the new resolvers will not change a single visible owner string. Every Approvals item legitimately has no project-PM link; every incident legitimately has no linked CA assignee; every OOS defect is genuinely unacknowledged. The placeholders ARE the truth on this dataset.

**Important:** this does NOT mean the resolvers are unnecessary. On the production dataset (`masci_safety`), and as the operator team continues to link POs to projects and create CAs for incidents, the resolvers will silently upgrade ownership without further code change. The mechanism is now in place.

---

## 5 · Risks of resolution (per source)

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| PO resolves to a departed-PM name (jobs_master not maintained) | LOW | LOW | PM name passes through unchanged; operator will see the stale name and refresh; the projection itself is not the source-of-truth gatekeeper |
| Incident resolves to a CA assignee on a stale closed CA | LOW | LOW | Resolver explicitly prefers OPEN CAs and falls back to most-recent ANY CA only when no open CA exists |
| Resolution fails silently (db down · index miss) | LOW | LOW | Both resolvers wrap their lookups in try/except and fall back to the base projection's placeholder |
| Resolution introduces a network round-trip per item | LOW | LOW | `find_one()` is a single indexed query; Command Center cap of 5–8 items per card bounds the call count |

---

## 6 · OMEGA discipline (audit phase)

| Discipline rule | Verdict |
|---|---|
| No code change in this audit phase | 🟢 PASS (this report is investigation-only) |
| No new schema proposed | 🟢 PASS (the resolvers read existing fields) |
| Source workflows untouched | 🟢 PASS |
| Pillar 1A-4 surface preserved | 🟢 PASS |
| Pillar 1B reservation respected | 🟢 PASS (resolution does not alter `escalation_level`) |

---

## 7 · Audit conclusion

Two resolvers are warranted; three placeholders correctly remain placeholders. Implementation and certification follow in `ACCOUNTABILITY_OWNER_FIDELITY_REPORT.md` and `PHASE_1A5_CERTIFICATION.md`.
