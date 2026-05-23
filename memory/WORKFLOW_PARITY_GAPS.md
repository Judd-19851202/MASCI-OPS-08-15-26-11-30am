# WORKFLOW PARITY GAPS
**Phase 3A · Iter367 · Pre-Redeploy Survey**
**Generated:** 2026-05-23
**Scope:** Capture every parity gap discovered between (a) the iter354-iter367 documented behavior and (b) what the preview environment actually serves. These items would be carried into production if redeployed today.

---

## 1 · Resolved this iteration (was a gap, is now closed)

### G1 · EmployeeRosterField suggestion dropdown rendered blank rows
- **Surfaced:** iter363 (testing_agent_v3_fork iteration_363.json)
- **Cause:** Component read `item.label` / `item.raw.name`, but `/api/master-lookup/employees` returns flat `{id, name, ...}`.
- **Fix:** `/app/frontend/src/components/EmployeeRosterField.jsx` lines 98-103 + 137-156. Defensive ordering: `item.name || item.label || item.raw?.name`.
- **Lock:** `TestRosterApiUiContract` (in `test_iter363_employee_linkage_persistence.py`) asserts the API keeps returning a renderable name field on every item.
- **Status:** ✅ CLOSED.

### G2 · LifecycleGuide ES rendering fell back to English
- **Surfaced:** iter366 live mobile spot-check at 390 ES.
- **Cause:** 20+ new strings shipped in iter365 had no entries in `/app/frontend/src/lib/i18n.js`'s ES dictionary.
- **Fix:** Added 22 ES translations (iter366) + 4 more (iter367 for HR Incidents).
- **Status:** ✅ CLOSED.

### G3 · Duplicate coaching banners on retrofitted pages
- **Surfaced:** iter366 spot-check.
- **Cause:** iter365 added LifecycleGuide ON TOP of legacy intro paragraphs that already said the same thing.
- **Fix:** Removed legacy intros from PmCrewCompliance (PmShell.intro), HrEmployeeAccountabilityTimeline (purple Shared-authority band), DriverQualificationReadOnlyView (Read-only banner + orphaned `accentBar`).
- **Status:** ✅ CLOSED. Every retrofitted page now has exactly ONE coaching surface.

### G4 · Glossary deep-link anchor mismatch
- **Surfaced:** iter363 testing agent.
- **Cause:** EmployeeRosterField glossary link pointed to `#capa` instead of `#roster_backed_selector`.
- **Fix:** Anchor corrected.
- **Status:** ✅ CLOSED.

---

## 2 · Documentation drift (not deployment blockers, but worth fixing in the handoff)

### D1 · Handoff doc lists `GET /api/admin/governance/scan` which does not exist
- **Reality:** Detection runs lazily inside `/api/admin/governance/summary`. No separate scan endpoint shipped.
- **Action:** Update PRD / handoff summary to remove the bad URL. **Not a code change.**

### D2 · Handoff doc lists `GET /api/notifications/digest/{role}` — reversed
- **Reality:** Actual path is `/api/{role}/notifications/digest` for each of admin, safety, hr, pm, dispatch, fl.
- **Action:** Same — handoff doc fix only.

---

## 3 · Open observations (low-priority polish, NOT deployment blockers)

### O1 · `/admin/governance` Convergence Score reports 0 / "critical"
- **Cause:** 335 open compliance findings, dominated by 230 `PPE_MISSING` historical records and 73 `EMP_ARCHIVED_ACTIVE` records that pre-date the linkage program.
- **Operational interpretation:** the score is *correct* — there is real backlog work to do on legacy data. The score will rise as those findings are resolved or acknowledged.
- **Action:** Operator decision — either (a) bulk-acknowledge historical PPE_MISSING findings, (b) run a one-time backfill to true up archived/active employee state, or (c) leave as-is and watch the score climb organically. **No code change required.**

### O2 · `EMP_LINK_AMBIGUOUS` and `EMP_LINK_MISSING_ID` rules have 0 open findings
- This is actually a positive signal — the roster and existing records are not ambiguous in current preview data.
- **Action:** None. Keep the rules registered; they will fire if drift occurs later.

### O3 · `/admin/compliance-findings` uses English-only chrome
- Admin convention is English-only (looking at the file, no `useT` import, hardcoded strings throughout).
- The iter367 LifecycleGuide retrofit matches this convention — no ES strings.
- **Action:** If operator wants admin-side ES parity at some point, that's a larger sweep (~24 admin pages). **NOT in scope for this iteration.**

---

## 4 · Production redeploy parity probes (must be run by operator after Deploy)

After clicking Deploy, run each of these on `https://mascidocs.com` and compare to the preview baseline in `PRODUCTION_PARITY_EXECUTION_REPORT.md`:

```bash
# All assume PROD=https://mascidocs.com
PROD=https://mascidocs.com
TOK=$(curl -s -X POST "$PROD/api/admin/login" -H "Content-Type: application/json" -d '{"password":"REDACTED"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")

# 1. Roster API shape (iter363 fix)
curl -s "$PROD/api/master-lookup/employees?q=a&limit=1" -H "X-Admin-Token: $TOK" | python3 -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('items') or []
if items and items[0].get('name'):
    print('✅ iter363 fix DEPLOYED — roster returns flat {id,name,...}')
else:
    print('❌ iter363 fix NOT DEPLOYED — dropdown will be blank in prod')
"

# 2. Governance summary keys (iter354-iter358)
curl -s "$PROD/api/admin/governance/summary" -H "X-Admin-Token: $TOK" | python3 -c "
import sys, json
d = json.load(sys.stdin)
rc = d.get('rule_counts') or {}
emp_keys = [k for k in rc if k.startswith('EMP_LINK')]
score_key = 'convergence_score' in d
print(f'✅ EMP_LINK_* registered: {sorted(emp_keys)}')
print(f'✅ convergence_score key present: {score_key}')
"

# 3. Role-scoped digest endpoints (iter357-iter358)
for r in admin safety hr pm dispatch fl; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$PROD/api/$r/notifications/digest" -H "X-Admin-Token: $TOK")
    echo "$r digest: $code (expect 200)"
done

# 4. Linkage capture lifecycle (iter363 / iter364 pytest harness pointed at prod)
# Run from /app/backend:
# BASE_URL=https://mascidocs.com python -m pytest tests/test_iter363*.py tests/test_iter364*.py -v
```

If ANY of the above shows a regression vs preview baseline, **rollback to the previous deployment** before allowing field crews to use the system.

---

## 5 · Architectural drift watchlist (P5-P7 stabilization items NOT addressed this iteration)

Tracked for future iterations — not deployment blockers, but accumulating risk:

- `server.py` at 12k+ lines (P7 extraction queued).
- 18 RBAC patterns observed (P4 consolidation queued).
- No super-admin MFA yet (P5 queued).
- No portal-grant audit log yet (P5 queued).
- No automated preview→prod parity smoke job (would replace this manual playbook).

**Operator should triage which of these to take after the Phase 3A deploy is verified clean.**
