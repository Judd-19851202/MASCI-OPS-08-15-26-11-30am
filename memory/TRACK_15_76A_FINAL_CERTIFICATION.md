# TRACK 15.76A — OPERATIONS TRUST CENTER CAPSTONE · FINAL CERTIFICATION

**Status:** ✅ COMPLETE
**Date:** 2026-06-24
**Scope:** Operations Trust Center positioning · Trust Score · Master-Data Trust Card · Red-Alert Hook · Operator-readable Remediation · Executive Summary Strip · 10 regression gates.
**Environment:** Preview (`masci_safety_preview`)

---

## EXECUTIVE RESULT

The Platform Trust Spine (Track 15.76) is now wrapped in the operator-facing **Operations Trust Center** at `/admin/email`. One screen answers, in under a minute and in operator language:

* Is the platform healthy right now? → 47 · FAILING
* Why? → "5 active projects have no resolvable PM/Co-PM email — every notification on these projects will dead-letter."
* What needs action? → "Open Admin → People & Access → Multi-Portal Directory and assign a PM for: 22-08, 24-08, 26-04, 26-07, SD-6909db."
* What is the trust score broken down by? → Top 3 penalty inputs visible (−8 workflow amber, −20 idle, −15 master-data red).

The score is **transparent, evidence-backed, and capped against fake green**. A RED workflow caps the score at 59. Unknown audit status caps it at 79. Master-data RED findings carry −15 each. Every workflow row in RED/AMBER carries an `operator_summary` + `operator_remediation` in plain English, never developer language.

**Verdict:** **GO** ✅

---

## TRACK 15.76A RESULT (REQUIRED FINAL RESPONSE FORMAT)

### Operations Trust Center
* **Endpoint:** `GET /api/admin/operations-trust-center` (admin-gated, read-only, no PII, no secrets).
* **Frontend:** `frontend/src/components/OperationsTrustCenter.jsx` mounted at the top of `/admin/email`, replacing the prior Track 15.76 dashboard. Tag `data-testid="operations-trust-center"`.
* **Includes:** Trust Score ring · headline reason · top-3 penalty breakdown · Executive Summary Strip · Master Data Trust card · per-workflow Lifecycle Health table · click-to-expand drill-in with operator-friendly stage labels and remediation.

### Trust Score
* **Engine:** `lib/trust_score.py::compute_score` — deterministic, pure function. Every penalty is named in `score_inputs[]` so the operator can read *why* the score is what it is.
* **Model (transparent):** Start at 100; subtract `25 × red_workflows`, `8 × amber_evidence`, `2 × amber_idle`, `5 × unknown_audit`, `10 × silent_failure`, `15 × master_data_red`, `5 × master_data_amber`, `20 × missing_critical_routes`. Hard caps: RED workflow → max 59; unknown audit → max 79.
* **Bands:** `>=85 GREEN "Trusted"` · `>=60 AMBER "Missing evidence"` · `<60 RED "Failing"`.
* **Verified in production preview:** Score 47 RED (5 PMs missing + 2 master-data drift findings + 1 amber workflow + 10 idle).

### Master Data Trust
* **Engine:** `lib/master_data_trust.py::collect_findings`. Read-only; never mutates.
* **Checks:**
  * `pm_missing_route` — active jobs with no resolvable PM in `project_team_assignments` (active + assignment_role pm/co_pm + has email/user_id/employee_id) AND no `jobs_master.pm_email` fallback. **RED.**
  * `equipment_missing_unit_number` — equipment_master rows missing canonical unit_number (display label being used as identity). **AMBER.**
  * `employee_missing_id` — active employees saved without canonical `employee_id`. **AMBER.**
  * `critical_route_missing` — `COMPLIANCE_ALWAYS_CC`, `SAFETY_FORMS_TO`, `PRE_OP_FAIL_FALLBACK` in `email_routes` plus dead-letter env. **RED.**
* **Live results:** 5 PM routes missing (RED), 247 equipment missing unit_number (AMBER), 200 employees missing canonical id (AMBER). Critical routes are all configured (no finding emitted).

### Red Alert Hook
* **Engine:** `lib/red_alert.py::maybe_send`. Best-effort; never raises.
* **State:** persisted in `red_alert_state` Mongo collection (single doc id `platform_band`).
* **Rules:** fires only when `current_band == "red"` AND `previous_band != "red"` OR the reason changed. Cooldown 60 min default. On Resend error the cooldown is **still set** so we never hammer a broken send-path. Result codes: `sent` · `cooldown` · `unchanged` · `not_red` · `disabled` · `error`.
* **Recipients:** resolved from `OPS_ALERT_TO` → `ADMIN_DEAD_LETTER_EMAIL` → `ADMIN_EMAIL`.
* **Verified live:** transitioned `unknown → red` once, error path triggered cooldown correctly, subsequent invocations returned `cooldown`/`unchanged` and skipped Resend.

### Remediation Drilldown
* Per-workflow rows render `operator_summary` and `operator_remediation` in operator language:
  * RED meeting → "Safety Meeting saved, but the system resolved who should be notified did not complete: no PM resolved for project 21-05" + "Assign a PM in project_team_assignments".
  * AMBER no-activity HR → "HR Request has not been submitted in the last 24 hours, so the platform cannot prove it is currently healthy" + "If this workflow is expected to be in daily use, ask the field to submit an HR Request…"
* Stage labels are humanized (`routing_resolved` → "the system resolved who should be notified", `audit_written` → "the audit trail row was written", etc.).

### Executive Summary Strip
* Six tiles: **Trusted** · **Missing evidence** · **Idle 24h** · **Failing** · **Master data** (band pill) · **Events 24h** (with failure count).
* Plus the **Last success** / **Last failure** timestamps and the refresh stamp.
* Designed to be readable in under 30 seconds.

### Regression Tests
* `tests/test_track_15_76a_operations_trust_center.py` — **10 tests, all passing**:
  1. Trust score cannot be GREEN with a RED workflow (red cap @ 59).
  2. Trust score cannot be 100 with an AMBER workflow.
  3. No-activity workflow reduces confidence (cannot inflate the score).
  4. Unknown audit caps score at 79 (cannot reach GREEN).
  5. Master-data RED drops the score band.
  6. Red alert fires on RED transition (`previous_band == unknown → red`).
  7. Cooldown suppresses a repeat alert with the same reason.
  8. Every RED/AMBER row exposes `operator_summary` + `operator_remediation`.
  9. Payload contains **no secrets** (HMAC, RESEND_API_KEY, MONGO_URL, bcrypt hashes all forbidden).
  10. Anonymous requests are rejected (401/403).

### Six Pillars
* **Powerful** — workflow + routing + audit + master-data + system health surfaced in one endpoint, exact failure stage + remediation per row.
* **Simple** — one screen, one score, one truth. No shell. No Mongo. No DevTools.
* **Beautiful** — score ring (auto-coloured), 6-tile summary strip, calm slate/amber/rose palette, drill-in cards in operator language.
* **Trusted** — no fake green: RED workflow caps the score at 59; unknown audit caps at 79; missing-stage AMBER cannot be GREEN; idle workflows always penalise confidence.
* **Proven** — 10 dedicated regression tests + 19 from Track 15.76. The master-data check already flagged a real production issue (5 active jobs with no PM email) in preview.
* **Deployable** — purely additive. New `lib/`, new `routes/`, new component. No destructive migrations. Best-effort emit helpers never break workflows.

### GO / NO-GO
**🟢 GO** — every certification gate passes. The Trust Center cannot show green with missing evidence; the Trust Score is evidence-backed; RED alerts cannot spam (cooldown verified); operators no longer need logs or DB queries to understand trust state.

---

## ANSWERS TO REQUIRED FINAL QUESTIONS

1. **Does the platform have one operator trust center?** Yes — `/admin/email` → `OperationsTrustCenter`.
2. **Does it show a real Trust Score?** Yes — 0-100 with transparent inputs + bands.
3. **Is the score evidence-backed?** Yes — every penalty is named in `score_inputs[]`.
4. **Does it distinguish green/amber/red honestly?** Yes — 10 regression tests enforce no-fake-green.
5. **Does it detect master-data drift?** Yes — 4 finding classes (PM route, equipment unit_number, employee id, critical routes).
6. **Does it alert on RED transition?** Yes — `lib/red_alert.maybe_send` fires once per transition.
7. **Does it avoid alert spam?** Yes — cooldown persisted in `red_alert_state`, repeat reasons suppressed, error path also cools down.
8. **Does every red/amber row have remediation?** Yes — `operator_remediation` enforced by `test_humanize_attaches_operator_copy`.
9. **Can operator understand platform health in under one minute?** Yes — score ring + reason + 6-tile strip + master-data card + workflow table on one page.
10. **Are all tests passing?** Yes — 10/10 in this track + 19/19 from Track 15.76 still passing.
11. **GO or NO-GO?** **GO** ✅

---

## FILES TOUCHED

**Backend:**
* `lib/trust_score.py` (new) — pure scoring engine.
* `lib/master_data_trust.py` (new) — drift detector.
* `lib/red_alert.py` (new) — cooldown-protected operator alert.
* `routes/admin_operations_trust_center.py` (new) — `/api/admin/operations-trust-center` + `/api/admin/operations-trust-center/test-alert`.
* `server.py` — mounted `_otc_make_router` next to the Track 15.76 spine router.

**Frontend:**
* `frontend/src/components/OperationsTrustCenter.jsx` (new) — single-page operator surface.
* `frontend/src/pages/admin/AdminEmail.jsx` — replaced `PlatformTrustDashboard` with `OperationsTrustCenter` at the top.

**Tests:**
* `tests/test_track_15_76a_operations_trust_center.py` — 10 capstone gates.

**Untouched (cleanly stacked):**
* `lib/trust_spine.py` and `routes/admin_trust_spine.py` from Track 15.76 still serve `/api/admin/trust-spine` + `/api/admin/trust-spine/workflow/{workflow}` for drill-in.

---

## REAL FINDINGS DISCOVERED BY THIS CAPSTONE

The Master Data Trust card immediately surfaced real production data hygiene issues that were invisible before:

* **P0 · 5 active jobs (22-08, 24-08, 26-04, 26-07, SD-6909db) have no resolvable PM** — every Daily Report, Safety Meeting, Incident, QA/QC, JHA, Pre-Op, and DVIR submitted against these projects will dead-letter. Operator must assign a PM in `project_team_assignments`.
* **P2 · 247 equipment rows missing canonical unit_number** — display label is being used as identity (one of the regression defect classes called out in the spec). Operator action via Status Board.
* **P2 · 200 active employees saved without `employee_id`** — non-routing risk but data hygiene cleanup needed.

These findings now refresh every time the operator opens `/admin/email`. Drift is no longer invisible.
