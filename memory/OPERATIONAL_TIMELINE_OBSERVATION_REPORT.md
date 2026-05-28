# Operational Timeline — Observation Report

**Phase V-Prelude · Wave 1.1**
**Window:** 24-hour observation from 2026-05-28.
**Status:** 🟡 **WINDOW OPEN.**

This document is the structured handoff for the observation window
following Wave 1.1. It captures what the sidecar makes observable,
what to monitor, and what would trigger a freeze.

---

## What the sidecar exposes

For the first time, real operators can:
- See a calm chronological record of what happened on ONE project,
  in one place, across constraints + cross-artifact links.
- Validate operational rhythm and language ("does this read like
  field reality?").
- Spot whether the role-visibility filter actually feels right —
  is the PM seeing TOO MUCH? TOO LITTLE? Is the FL operator getting
  enough operational context to act?

The sidecar is the **first contextually-rich operational chronology
surface** in the platform. Everything before this was per-artifact
history (a single daily report, a single incident). The sidecar is
the **project-rhythm view.**

---

## Observation instrumentation

### Live probes (every deploy)
```
authority_mismatch_probe         · scripts/authority_mismatch_probe.py
timestamp_doctrine_probe         · scripts/timestamp_doctrine_probe.py
operational_links_doctrine_probe · scripts/operational_links_doctrine_probe.py
```
All three are wired into `pre_deploy_check.sh`. Any new violation
blocks the next deploy.

### Regression tests (run on every PR)
```
backend/tests/test_v_prelude_wave1_substrate.py            (19 tests)
backend/tests/test_v_prelude_wave1_1_sidecar.py            (8 tests)
backend/tests/pw_suite/test_v_prelude_wave1_1_sidecar_calmness.py
                                                            (10 PW tests)
```

### Manual heartbeat (daily, ≤ 60 seconds)
```bash
URL=$(grep ^REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2 | tr -d '"')
TOKEN=$(curl -s -X POST "$URL/api/admin/login" -H "Content-Type: application/json" \
  -d "{\"password\":\"$(grep ^ADMIN_PASSWORD /app/backend/.env | cut -d= -f2 | tr -d '\"')\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s "$URL/api/timeline?project_id=ANY" -H "X-Admin-Token: $TOKEN" \
  | python3 -m json.tool | head -20
```

### Mongo health (one-shot during window)
```bash
python3 - <<'PY'
from pymongo import MongoClient; import json
m = MongoClient(open('/app/backend/.env').read().split('MONGO_URL="')[1].split('"')[0])
db = m['masci_safety_preview']
print(json.dumps({
  'constraints': db.operational_constraints.estimated_document_count(),
  'links': db.operational_links.estimated_document_count(),
  'links_active': db.operational_links.count_documents({'status': 'active'}),
  'links_voided': db.operational_links.count_documents({'status': 'voided'}),
  'links_audit_only': db.operational_links.count_documents({'visibility': 'audit-only'}),
}, indent=2))
PY
```

---

## Freeze triggers

If any of the following appears during the observation window, **stop
adoption and triage immediately**:

1. **`operational_links` doctrine probe** reports a new violation.
2. **Audit-only link** surfaces in a non-admin actor's `/api/timeline`
   response (this would be a §5 doctrine breach).
3. **`_id` leak** in any timeline / constraint / link response.
4. **Naive `datetime`** appears in any new code touching the substrate
   (TRUST-TIME-1B probe will catch).
5. **Mobile body overflow** on `/pm/projects/:projectNumber` at iPhone
   13 viewport (Playwright sweep will catch).
6. **Loud color accent** introduced in the sidecar chrome (loud-badge
   sweep will catch).
7. **Notification fan-out** triggered by a link create or status flip
   (Wave 1.1 rule #9: no notification expansion).

Each trigger has a corresponding pytest + probe pair. Do NOT advance
to Wave 2 with any open freeze trigger.

---

## What to listen for (operator feedback)

The observation window's qualitative signals matter more than the
quantitative ones at this stage:

| Question | What "yes" would mean |
|---|---|
| Does the chronology read like field reality? | Operators recognize their language. |
| Is the row density right? | Neither too sparse to be useful nor too dense to scan. |
| Is the empty state encouraging? | Doesn't shame operators into filing noise. |
| Are voided links truly invisible? | No "phantom rows" persist after a link is voided. |
| Does the sidecar feel passive enough? | No one is asking "how do I add an event from here?". |
| Is mobile readable in sunlight? | Slate text on white passes outdoor visibility. |

If even ONE answer drifts to "no" during the window, log it in this
file before opening Wave 2 — Wave 2 will inherit any unaddressed
Wave 1.1 friction.

---

## Wave 2 readiness gate

Wave 2 (Operational Search + Field Memory) is LOCKED until ALL of the
following hold:
- [ ] No freeze trigger fired during the 24-hour window.
- [ ] No new doctrine probe violations.
- [ ] Mobile + desktop sidecar Playwright sweep stays green.
- [ ] Operator explicitly issues "start V-Prelude Wave 2".

---

— issued by E1 · V-Prelude Wave 1.1 · 2026-05-28
