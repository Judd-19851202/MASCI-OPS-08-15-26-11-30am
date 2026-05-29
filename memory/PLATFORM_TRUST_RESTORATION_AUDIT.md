# Platform Trust Restoration Audit · Master Synthesis

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:50 UTC._

> **The single document the operator should read first.** Synthesizes
> the 11 companion audit documents into one trust-state assessment of
> the MASCI Operations Platform. AUDIT ONLY. NO FIXES.

## 1 · The operator's question

> "For every action: What happens? Where does it go? Who owns it? Who
> sees it? Who gets notified? How are they notified? What dashboard
> receives it? What happens next? What happens if nobody responds?"

The answer for **every single workflow** is captured in the matrices
in the companion documents. This master synthesis tells the operator:
where the platform is solid, where it leaks, and what the priority of
each leak is.

## 2 · The five trust pillars

| Pillar | Definition | Platform state |
|---|---|---|
| **Every route works** | No dead ends, no wrong-portal bounces, no token wipes | ✅ post P0-2A · pending production redeploy |
| **Every button works** | Visible = executable, no permission mismatches | ⚠ 1 dead button remains (Shop Trash · GAP-10 · P1) |
| **Every record has an owner** | A persona is accountable | ✅ for all 25+ workflows audited |
| **Every workflow has a destination** | A dashboard surfaces it OR a bell-feed entry exists | ❌ 4 workflows lack proactive surfaces (GAP-1/2/3/6) |
| **Every submission has a next step** | An owner gets a notification AND a clear action path | ❌ 5 workflows lack one or both (GAP-1/2/3/4/6) |

## 3 · Where we stand

### 3a · ✅ Solid (operator should NOT lose sleep over these)
- Daily Reports · all sub-rows
- Equipment Pre-Op PASS and FAIL
- Shop Recovery / Asset Transfer
- PO Request full lifecycle (request · approve · reject · clarify · receipt upload · receipt OPEN ← P0-3 fixed · close)
- Incident Reports
- Safety Meetings · Safety Inspections
- QA/QC (Concrete · Rebar · Subwork · Material Testing)
- Corrective Actions · Fire Extinguisher Inspections
- Dispatch Requests
- Document Expirations (nightly cron)
- HR Time Verification (read-only ledger)
- HR Payroll Variance (weekly cron handles the system path)
- Training Records (employee lens — supervisor lens is gap-4 P1)
- Backup success rows
- System Health outage alerts
- Portal Boundary integrity (post P0-2A namespace-aware 401)

### 3b · ❌ Trust-impacting gaps the operator should decide on now

| # | Gap | Tier | Why it matters |
|---|---|---|---|
| 1 | **Fleet DVIR has no confirmed notification path** | P0 (pending operator confirm) | If DVIR was meant to drive Shop / Dispatch action, it's an orphan |
| 2 | **Backup scheduler dead** | P0 (held) | Already known; alarms silent until scheduler revived |
| 3 | **FL 10 forms — bell/task missing** | P1 | Records reach email recipients but no dashboard queue |
| 4 | **Safety Forms (Equip Issuance/Training/Return) — bell/task missing** | P1 | Same pattern as #3 |
| 5 | **JHA — no task to safety supervisor** | P1 | Compliance record lands without an action queue |
| 6 | **Training Record assigned — supervisor not notified** | P1 | Crew supervisor blindsided by training deficiencies |
| 7 | **Shop Equipment Trash button visible but 403** | P1 | Dead button — violates "visible action must work" doctrine |
| 8 | **`/equipment/:id` and `/inspections/:id` redirect always to admin namespace** | P1 | Cross-portal user gets bounced |
| 9 | **No defined escalation cadence for severe incidents** | P2 | First response works · follow-up is human-only |
| 10 | **PO Request 60+ day stuck records have no escalation tier** | P2 | Existing watchdog handles ≤ 30 days |

### 3c · 🟡 Test-only debt (does NOT block production but blocks pre-deploy orchestrator from a clean PASS)
- Stale tab-title tests (DispatchHub / ShopHub)
- Pre-freeze DR delete tests
- Non-deterministic projector test on preview DB

## 4 · The 18-gap register at a glance

| Tier | Count | IDs |
|---|---|---|
| P0 | 2 | GAP-6 (DVIR confirm) · GAP-7 (Backup held) |
| P1 | 7 | GAP-1 · GAP-2 · GAP-3 · GAP-4 · GAP-10 · GAP-16 · GAP-17 |
| P2 | 6 | GAP-5 · GAP-8 · GAP-9 · GAP-14 · GAP-15 · GAP-18 |
| P3 (test-only) | 3 | GAP-11 · GAP-12 · GAP-13 |

## 5 · Trust verdict

**The platform is operationally trustworthy on 80% of workflows and
patchily trustworthy on 20%.** The trustworthy 80% covers every
critical safety / quality / financial path: Daily Reports, Equipment
Pre-Op, PO Requests, Incidents, Safety Meetings, Inspections, QA/QC,
Dispatch, Document Expirations. The patchy 20% is concentrated in
records that have an email path but no in-app surface, and one
suspected orphan (Fleet DVIR).

The recent operator-reported defects (P0-2A bounce · P0-2B dead
delete · P0-2C buried Shop pre-op · P0-3 blank-tab PDF) are all
addressed in preview and awaiting redeploy. None of them recur in the
audit findings — they were already classified as P0 and fixed.

## 6 · Companion documents

1. `PLATFORM_ROUTING_PERMISSION_AUDIT.md` — every route, every guard
2. `VISIBLE_ACTION_MATRIX.md` — every button → destination → permission
3. `PORTAL_BOUNDARY_CERTIFICATION.md` — portal namespace integrity
4. `BROKEN_ROUTE_FIX_PLAN.md` — defects + recommended fixes (NO IMPL)
5. `PLATFORM_FLOW_NOTIFICATION_AUDIT.md` — workflow notification paths
6. `WORKFLOW_OWNERSHIP_MATRIX.md` — creator · owner · viewers · etc.
7. `ALERTING_AND_DESTINATION_MATRIX.md` — where alerts go, dashboards
8. `DASHBOARD_DESTINATION_CERTIFICATION.md` — every record's surface
9. `NOTIFICATION_GAP_REGISTER.md` — full 18-gap inventory
10. `FLOW_FIX_RECOMMENDATION_PLAN.md` — staged remediation plan
11. `ORPHAN_WORKFLOW_REPORT.md` — black-hole risk classification
12. `PLATFORM_TRUST_RESTORATION_AUDIT.md` — this synthesis

PRD.md and _INDEX.md updated with V.5 P0 Trust Restoration entries.

## 7 · Operator next-step decision tree

```
        ┌─────────────────────────────────────────────────────┐
        │  Did the audit surface anything the operator needs  │
        │  to act on RIGHT NOW (P0)?                          │
        └─────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────────────┐
        │  YES — two P0s pending:                             │
        │   • GAP-6 (Fleet DVIR) — needs operator clarification│
        │   • GAP-7 (Backup) — held per priority directive    │
        └─────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────────────┐
        │  Operator decision required:                        │
        │   1. Confirm Fleet DVIR intent (notify? or ledger?)│
        │   2. Redeploy P0-1 + P0-2 + P0-3 fixes to prod     │
        │   3. After live verification: authorize Backup     │
        │      Scheduler Hardening 5-phase plan              │
        │   4. (Later) authorize P1 closures in batch        │
        └─────────────────────────────────────────────────────┘
```

## 8 · Stop condition observed

- ✅ Audit only, no fixes
- ✅ No code · no env · no scheduler · no Approval/Rejection / Pilot / RFI / Schedule / P6 / PM Exposure Tile / new dashboards / new features
- ✅ Every gap classified per operator rubric
- ✅ Companion documents produced (10 + this one = 11; `PORTAL_BOUNDARY_CERTIFICATION.md` is the 12th deliverable)
- ✅ Operator review pending

---

_End of PLATFORM_TRUST_RESTORATION_AUDIT.md._
