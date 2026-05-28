# WAVE 1 — Observation Guide

**Phase V-Prelude · Wave 1**
**Status:** 🟡 **OBSERVATION WINDOW OPEN**
**Window:** 24 hours from preview deploy (start: 2026-05-28).
**Next:** Operator authorization required to start Wave 2.

---

## Why this window exists

Each wave is followed by a minimum 24-hr observation window before the
next wave begins. The window exists to surface **slow-burn** issues
(index pressure, telemetry drift, calmness regressions, role-leak edge
cases) that no test suite can reproduce.

**Do not start Wave 2 until this window closes AND the operator
explicitly authorizes it.**

---

## What to watch (cheap, daily-actionable)

### 1. Doctrine probes — every deploy
The pre-deploy gate now includes 3 substrate probes. None should
report a new violation:
```bash
python3 /app/scripts/authority_mismatch_probe.py --gate
python3 /app/scripts/timestamp_doctrine_probe.py --gate
python3 /app/scripts/operational_links_doctrine_probe.py --gate
```
All must exit 0. New violations indicate substrate drift.

### 2. Mongo health
Two new collections were added. Both are tiny; index pressure should
be nil. Sanity check on preview:
```bash
python3 - <<'PY'
from pymongo import MongoClient; import json
m = MongoClient(open('/app/backend/.env').read().split('MONGO_URL="')[1].split('"')[0])
db = m['masci_safety_preview']
print(json.dumps({
  'constraints': db.operational_constraints.estimated_document_count(),
  'links': db.operational_links.estimated_document_count(),
  'links_active': db.operational_links.count_documents({'status': 'active'}),
  'links_archived': db.operational_links.count_documents({'status': 'archived'}),
  'links_voided': db.operational_links.count_documents({'status': 'voided'}),
  'links_superseded': db.operational_links.count_documents({'status': 'superseded'}),
}, indent=2))
PY
```

### 3. Regression suite — every PR
```bash
cd /app/backend && python3 -m pytest tests/test_v_prelude_wave1_substrate.py -q
```
All 19 tests must remain green.

### 4. Visual calmness check (manual, daily)
Open `/constraints` on preview. Confirm:
- [ ] No red-overload — only `high` severity shows the rose pill.
- [ ] No charts, no gantt, no progress bars, no badges-of-engagement.
- [ ] Aging surfaces as `3d` / `8d` only after day 3 — never panic copy.
- [ ] Mobile (≤640 px): filters and form collapse to single column.
- [ ] Empty state copy is italic slate-500 — "No constraints recorded yet."

### 5. Role boundary check (manual, one-off)
Log into each portal and visit `/constraints`. Expected behaviour:

| Portal | Should see | Should NOT see |
|---|---|---|
| Admin | Everything · all controls | — |
| PM | List, file, edit, resolve | — |
| Safety | List, file, edit, resolve | — |
| Field Leadership | List, file, chronology-note | edit-fields · resolve buttons |
| HR | List only (view) | file · edit · resolve |
| Dispatch | Conservative fallback (view only) | mutate controls |

### 6. Telemetry — no new ingest fan-out
Wave 1 deliberately ships WITHOUT telemetry. Any draft.* /
operational_signal.* fan-out should be unaffected. Sanity check:
```bash
curl -s "$(grep ^REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2 | tr -d '"')/api/draft-telemetry/health" \
  -H "X-Admin-Token: $TOKEN" | python3 -m json.tool
```
Should still return `ok: true`.

---

## Failure protocols

| Failure | Action |
|---|---|
| Doctrine probe reports new violation | DO NOT advance to Wave 2. Triage immediately. |
| `operational_links` row leaks `_id` | Critical — patch `routes/operational_links.py` `_to_out` projection. |
| Constraint deletion appears anywhere | Critical doctrine breach — hard DELETE forbidden. Status `void` only. |
| Frontend renders a chart or gantt | Visual doctrine drift. Revert immediately. |
| Mongo index alert | Lower-priority — these collections will stay tiny pre-Wave-2. |

---

## What is locked until further authorization

- ❌ Wave 2 (Operational Search · Field Memory).
- ❌ Wave 3 (Offline draft extension · Mobile polish).
- ❌ Wave 4 (Self-healing doctrine probe expansion).
- ❌ Phase V.1 RFI MVP (gated behind Wave 4 + 72-hr observation).

---

## How Wave 2 starts

The operator's explicit command, in a fresh chat session:
> "start V-Prelude Wave 2"

No earlier. No implicit "we have time, let's start now" interpretation.
The observation window exists for a reason. Respect it.

— issued by E1 · V-Prelude Wave 1 · 2026-05-28
