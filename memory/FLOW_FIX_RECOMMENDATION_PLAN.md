# Flow Fix Recommendation Plan

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:46 UTC._

> **AUDIT ONLY — NO IMPLEMENTATIONS IN THIS DOCUMENT.**
> This plan stages how each gap COULD be addressed if and when the
> operator authorizes a hardening pass. Estimated effort sizes are best-
> effort for planning, not commitments.

## 1 · Sequence rationale

Operator's stop-list (Backup Hardening · Approval/Rejection · Pilot ·
RFI · Schedule · P6 · PM Exposure Tile · New Dashboards · New
Features) constrains what can be touched. The gaps below are ordered
by:

1. **Trust impact** (does it cause operator-perceived "trust-killing black hole"?)
2. **Operational risk** (does the workflow go unnoticed?)
3. **Effort:risk ratio** (cheap, safe fixes first)

## 2 · Recommended fix plan

### Phase α · CONFIRM scope with operator (≤ 1 day)

| Gap | Operator question |
|---|---|
| GAP-6 (Fleet DVIR) | Is Fleet DVIR intended to drive Shop / Dispatch action? If yes, we wire the notification + task pipeline. If no, document as "informational ledger only" and close. |
| GAP-7 (Backup) | Authorize Phase 1 of the previously-approved 5-phase scheduler hardening? (Currently held per operator's "verify P0-2/P0-3 live first" directive.) |
| GAP-18 (PM Exposure Tile sidebar) | Hide the sidebar entry now (cosmetic) or keep it visible as a forward-pointer for when PM Exposure Tile is authorized? |

### Phase β · P1 visibility closures (≤ 1 day)

**β-1 · FL 10 forms bell/task fan-out (GAP-1)**
- File: `backend/routes/field_leadership.py`
- Edit: after each `await send_email_async(recipients, ...)` add `emit_task_and_notification(db, role="safety", kind="fl_form", record_id=doc["id"], cc_roles=["admin"])`
- Test: existing FL submit tests + new bell-feed assertion
- Effort: S

**β-2 · Safety Forms bell/task fan-out (GAP-2)**
- File: `backend/routes/safety_forms.py`
- Edit: after `_dispatch_email(...)` add parallel `emit_task_and_notification(db, role="safety", kind="safety_form", record_id=...)`
- Effort: S

**β-3 · JHA safety-supervisor task (GAP-3)**
- File: `backend/routes/safety.py`
- Edit: in JHA POST handler add `emit_task_and_notification(db, role="safety", kind="jha")` parallel to existing email
- Effort: XS

**β-4 · Training supervisor notification (GAP-4)**
- File: `backend/routes/training_center.py`
- Edit: when an assignment is created, additionally `emit_notification(db, role="safety", kind="training_assigned", title=...)` for the supervisor lookup (best-effort)
- Effort: M (supervisor lookup is intermittent — may need a `linked_supervisor_email` field on the assignment doc)

**β-5 · Shop Trash dead button (GAP-10)**
- File: `frontend/src/pages/EquipmentDashboard.jsx`
- Edit: extend `isPmContext` gate to also hide Trash in Shop context (`!isPmContext && !isShopContext &&`)
- Effort: XS

**β-6 · Cross-portal redirect cleanup (GAP-16/17)**
- File: `frontend/src/App.js`
- Edit: replace `RedirectWithId base="/admin/..."` with `PortalAwareRedirectWithId` that reads any present portal token and routes accordingly
- Effort: S

### Phase γ · P2 escalation paths (≤ 2 days, requires policy decisions)

**γ-1 · Severe Incident no-response escalation (GAP-14)**
- Define policy: after N hours without acknowledgment, escalate to which role?
- Implementation: nightly cron checks Incidents with `severity=severe AND acknowledged_at IS NULL AND created_at < now-NhrThreshold`
- Effort: M (depends on acknowledgment-tracking field which may not yet exist)

**γ-2 · PO no-receipt 30-day escalation (GAP-15)**
- Existing receipt-missing watchdog handles up to ~30 days. Extension: after 60 days send a SEVERE escalation to admin + requester's manager.
- Effort: S

**γ-3 · Payroll Variance manual fan-out (GAP-5)**
- File: `backend/routes/payroll_variance.py`
- Edit: when a manual batch is committed, also email PAYROLL_VARIANCE_EMAIL_TO env list (parallel to weekly cron) AND emit a HR task
- Effort: XS

**γ-4 · DR Equipment-Issue YES auto-link (GAP-9)**
- File: `backend/routes/daily_reports.py`
- Edit: when DR has equipment_issue=true, optionally create a draft "shop attention" task (low priority)
- Effort: M (UX flow needs operator design)

### Phase δ · P3 test cleanup (≤ 0.5 day)

**δ-1 · Update stale tab-title tests (GAP-11)**
- File: `backend/tests/test_iter219_portal_titles_and_discoverability.py`
- Edit: bump `EXPECTED_TITLES["DispatchHub.jsx"] = "Dispatch Command · MASCI"` and `EXPECTED_TITLES["ShopHub.jsx"] = "Shop Recovery · MASCI"`
- Effort: XS

**δ-2 · Retire post-freeze DR delete tests (GAP-12)**
- File: `backend/tests/test_daily_reports.py`
- Edit: mark `test_delete_and_verify_removed` and `test_delete_404_for_unknown` with `pytest.mark.skip("Pre-freeze contract; DELETE returns 410 by V.5 doctrine")`
- Effort: XS

**δ-3 · Unified projector test determinism (GAP-13)**
- File: `backend/tests/odr/test_wave_1a.py`
- Edit: filter by the test's own `project_number` so saturation doesn't affect assertion
- Effort: XS

## 3 · Held items (operator stop-list)

These remain explicitly NOT in the plan:

- Backup Scheduler Hardening (held until P0-2/P0-3 verified live)
- Approval/Rejection workflow architecture (architecture exists; no implementation)
- Pilot Rollout
- RFI integration
- Schedule integration
- P6 integration
- PM Exposure Tile routing
- New Dashboards or New Features

## 4 · Estimated total

| Phase | Effort | Operator decision required |
|---|---|---|
| α (scope confirmation) | < 1 day | ✅ yes |
| β (P1 closures) | ≤ 1 day | implicit on operator approval |
| γ (P2 escalation paths) | ≤ 2 days | ✅ policy decisions needed |
| δ (P3 test cleanup) | ≤ 0.5 day | implicit |

**Total**: ≤ 4.5 days of focused engineering after operator authorization.

## 5 · Stop condition

This plan is documentation only. No code changes. No env changes. No
testing agent runs. The operator owns the call on which (if any) of
these phases proceeds.

---

_End of FLOW_FIX_RECOMMENDATION_PLAN.md._
