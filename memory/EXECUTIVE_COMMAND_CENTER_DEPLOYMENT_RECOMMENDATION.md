# Executive Command Center — Production Deployment Recommendation

**Classification:** OMEGA Pillar 2 · Phase A · GO/NO-GO Decision Document
**Generated:** 2026-05-31 UTC
**Author:** E1
**Companion doc:** `EXECUTIVE_COMMAND_CENTER_CERTIFICATION.md`

---

## 1 · Headline

🟡 **CONDITIONAL GO** — recommended deployment path is one small defect-remediation patch (≤ 100 LOC), then production redeploy.

The slim Phase A delivers single-glass operational visibility today. **Without the patch, deployment is acceptable but the dashboard ships with two known false-positive classes and one silent false-negative class.** With the patch, the dashboard ships clean.

---

## 2 · Three deployment paths

The operator has three defensible choices. The agent's read-only assessment of each:

### Path A · 🟢 Deploy as-is

| Pros | Cons |
|---|---|
| Fastest to production · zero further code · already evidence-tested | Aged safety incidents stay RED forever (D1/D2) · Approvals card silently under-reports (D5) · Pulse strip count inflated · Trust risk if leadership notices stale signals |

**When this is right:** if the operator is comfortable that Phase A is a **pilot surface**, and intends to accept the false-positive rate for the first 2-4 weeks while gathering live telemetry. Defects can be fixed in Phase B alongside other planned work.

### Path B · 🟡 Deploy after a minimal patch (RECOMMENDED)

Fix only the three medium/high-impact defects:
- **D1** (~15 LOC): SAF-CRITICAL-UNRESOLVED — exclude incidents with linked `corrective_actions.status="Closed"` or with `corrected_on_site="Yes"`.
- **D2** (~10 LOC): SAF-OSHA-OPEN — same closure-state check.
- **D5** (~20 LOC): coerce `created_at` comparison to handle both ISO strings and BSON datetime objects via a single helper used by all `count_documents` calls.

Total: ~45 LOC. Patch is well-contained to `routes/command_center.py`. No schema changes. No new collections. No new endpoints.

| Pros | Cons |
|---|---|
| Removes the two FP classes leadership is most likely to notice · Approvals card produces reliable RAG · Pulse strip count becomes accurate · No new scope · Same OMEGA discipline maintained | One additional batch before production · ~2-3 hour patch + retest cycle |

**When this is right:** if the operator wants a clean, defensible Phase A in production from day 1.

### Path C · 🟢 Deploy after a comprehensive patch

Fix all 7 defects (D1-D7) at once. Add the working-day calendar evaluation (D3), convert N+1 queries to aggregations (D4), align item severity with card pill (D6).

Total: ~100 LOC. Largest patch but still well within Phase A scope.

| Pros | Cons |
|---|---|
| Most polished surface · best performance at scale · cleanest pre-Phase-B starting point | More change in one batch · slightly larger risk surface for review |

**When this is right:** if the operator prefers a single comprehensive cleanup over two small patches over time.

---

## 3 · Recommendation

🟡 **Path B (minimal patch · D1+D2+D5)** is the recommendation, on these grounds:

1. **D1 and D2 are visibility risks the operator will see first.** A Safety card stuck RED on an incident that was investigated 3 weeks ago undermines the dashboard's credibility within the first week of use.
2. **D5 causes silent false negatives** on the Approvals card — leadership cannot detect what they cannot see. This is the most dangerous failure mode in an executive dashboard.
3. **D3, D4, D6, D7 are deferred** to Phase B because they're noise/perf/cosmetic — they don't change leadership decisions and can be fixed alongside the Recommender / Document Expirations work without bundling risk.
4. **Patch scope is small and well-contained.** All three fixes live in `/app/backend/routes/command_center.py`. No frontend changes. No collection changes. Pytest expansion: 3 new tests confirming the closure-check + a tighter datetime-handling test.

---

## 4 · Deployment readiness checklist (post-patch state)

| Item | Status (current) | Status (after Path B patch) |
|---|---|---|
| Live snapshot endpoint reachable | 🟢 | 🟢 |
| Auth gate enforced | 🟢 | 🟢 |
| Pytest 14/14 PASS | 🟢 | 🟢 (+3 new = 17/17) |
| Ruff clean | 🟢 | 🟢 |
| Backup-freeze respected | 🟢 | 🟢 |
| No notifications emitted | 🟢 | 🟢 |
| All RED items answer 5 questions | 🟢 | 🟢 |
| FP class: stale critical incidents | 🔴 | 🟢 (D1+D2 fixed) |
| FN class: silent approvals/OOS counts | 🔴 | 🟢 (D5 fixed) |
| FP class: weekend DR-missing | 🔴 | 🔴 (D3 deferred · operator can mitigate by raising thresholds in `command_center_thresholds`) |
| Performance at scale | 🟡 | 🟡 (D4 deferred · acceptable for preview ≤ 100 jobs) |

---

## 5 · Pre-deployment gate

If Path B is authorized, the implementation batch must:

1. Modify **only** `/app/backend/routes/command_center.py` + `/app/backend/tests/test_command_center_phase_a.py`. No frontend changes.
2. Pass all 17 pytest cases (14 existing + 3 new).
3. Re-run the live snapshot probe and confirm:
   - Approvals card with aged pending POs now flips from GREEN to AMBER/RED appropriately.
   - Safety card no longer flags incidents whose linked CA is `status=Closed`.
   - Pulse Strip `amber_items` and `red_items` counts match the union of warnings.
4. Produce a closeout report `PILLAR_2_PHASE_A_DEFECT_FIX_REPORT.md` with before/after snapshots.
5. Then operator reruns the OMEGA pre-deployment gate from `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` and only redeploys if 12/12 gates pass.

---

## 6 · Risk if deployed as-is (Path A)

| Risk | Likelihood | Severity | Cumulative effect |
|---|---|---|---|
| Operator sees a "stuck RED" on Safety for an incident known to be resolved | HIGH (within first week) | MEDIUM | Trust erosion |
| Approvals card stays GREEN while a real $50,000 PO ages to day 6 unnoticed | MEDIUM | HIGH | Missed approval triggers an avoidable project delay |
| Equipment card shows backlog count but no specific aged-OOS examples | MEDIUM | LOW | Backlog signal alone is still actionable |
| Pulse Strip says "X RED · 10 AMBER" but no AMBER warning text exists | HIGH | LOW | Cosmetic confusion; no decision impact |

If Path A is chosen, operator should communicate to pilot users that *"a stuck-RED on Safety may represent an incident that was investigated but not formally closed in the system — verify in the source record"* and *"the Approvals card may temporarily under-report; cross-check with `/admin/po-requests` weekly until fix."*

---

## 7 · Operator decision required

| Path | Authorize? |
|---|---|
| A · Deploy as-is | (operator choice) |
| B · Minimal patch first **(recommended)** | (operator choice) |
| C · Comprehensive patch first | (operator choice) |
| Defer · Pilot in preview for 2-4 weeks, then re-certify | (operator choice) |

The agent stops here. No code change. No deployment. Awaiting operator's explicit path authorization.
