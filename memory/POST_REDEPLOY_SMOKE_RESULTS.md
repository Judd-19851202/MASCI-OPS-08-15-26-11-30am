# POST-REDEPLOY SMOKE RESULTS
**Phase 3A · Iter367 · Operator Worksheet**
**To be filled in by the operator AFTER clicking Deploy in the Emergent dashboard.**

This template captures the actual results of running the parity playbook against production. **It is intentionally empty** — fill it in as you run each probe, then sign at the bottom. Compare each row to the preview baseline in `PRODUCTION_PARITY_EXECUTION_REPORT.md`.

---

## 0 · Deploy metadata

| Field | Value |
|---|---|
| Production URL | `https://mascidocs.com` |
| Deploy clicked at | `___________________` |
| Deploy completed at | `___________________` |
| Operator | `___________________` |
| Iter range deployed | iter354 → iter367 inclusive |

---

## 1 · Endpoint smoke (60 seconds)

```bash
PROD=https://mascidocs.com
TOK=$(curl -s -X POST "$PROD/api/admin/login" -H "Content-Type: application/json" -d '{"password":"REDACTED"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
SAFE=$(curl -s -X POST "$PROD/api/safety-forms/login" -H "Content-Type: application/json" -d '{"password":"REDACTED"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
```

| Endpoint | Preview baseline | Production result | Match? |
|---|---|---|---|
| `GET /api/health` | 200 | `___` | `_` |
| `GET /api/admin/governance/summary` | 200 (`convergence_score`, `rule_counts`, EMP_LINK_* present) | `___` | `_` |
| `GET /api/admin/compliance/findings?limit=5` | 200 | `___` | `_` |
| `GET /api/master-lookup/employees?q=a&limit=3` | 200 + items[0].name populated | `___` | `_` |
| `GET /api/incidents` | 200 | `___` | `_` |
| `GET /api/daily-reports` | 200 | `___` | `_` |
| `GET /api/equipment-inspections` | 200 | `___` | `_` |
| `GET /api/meetings` | 200 | `___` | `_` |
| `GET /api/qaqc-inspections` | 200 | `___` | `_` |
| `GET /api/safety-forms/equipment-issuances` | 200 (with X-Safety-Forms-Token) | `___` | `_` |
| `GET /api/safety-forms/equipment-trainings` | 200 (with X-Safety-Forms-Token) | `___` | `_` |
| `GET /api/admin/notifications/digest` | 200 | `___` | `_` |
| `GET /api/safety/notifications/digest` | 200 | `___` | `_` |
| `GET /api/hr/notifications/digest` | 200 | `___` | `_` |
| `GET /api/pm/notifications/digest` | 200 | `___` | `_` |
| `GET /api/dispatch/notifications/digest` | 200 | `___` | `_` |
| `GET /api/fl/notifications/digest` | 200 | `___` | `_` |

---

## 2 · Critical fix verification (the iter363 dropdown bug must NOT regress)

```bash
curl -s "$PROD/api/master-lookup/employees?q=a&limit=1" -H "X-Admin-Token: $TOK" | python3 -c "
import sys, json
items = json.load(sys.stdin).get('items') or []
name = items[0].get('name') if items else None
print('items[0].name =', repr(name))
"
```

| Probe | Expected | Production result |
|---|---|---|
| `items[0].name` | non-empty string like `'Alec Perkins'` | `__________________________` |

If `name` is `None` or `''`, the iter363 fix did not deploy and the EmployeeRosterField dropdown will be **visually blank** in production. **DO NOT proceed with field training until this is resolved.**

---

## 3 · Linkage lifecycle (pytest pointed at production)

```bash
cd /app/backend
BASE_URL=https://mascidocs.com python -m pytest tests/test_iter363_employee_linkage_persistence.py tests/test_iter364_p1_linkage_persistence.py -v 2>&1 | tail -30
```

| Suite | Preview baseline | Production result |
|---|---|---|
| `test_iter363_employee_linkage_persistence.py` | 11 passed | `___ passed / ___ failed / ___ skipped` |
| `test_iter364_p1_linkage_persistence.py` | 6 passed | `___ passed / ___ failed / ___ skipped` |

---

## 4 · Frontend coaching parity (browser · 5 minutes)

For each, open the URL on a mobile-width browser (390px) **with `localStorage.masci.lang = 'es'`** and check the LifecycleGuide:

| URL | Expected ES heading | Production result |
|---|---|---|
| `/admin/incidents/{any_id}` | "Ciclo de vida del incidente" | `___` |
| `/hr/employees/{any_id}/accountability` | "Cómo funciona esta línea de tiempo" | `___` |
| `/pm/crew-compliance` | "Cómo funciona tu vista de cumplimiento de cuadrilla" | `___` |
| `/dispatch-portal/driver-qualification` | "Cómo funciona la disponibilidad del conductor" | `___` |
| `/field-leadership/portal/driver-qualification` | same as above | `___` |
| `/hr/incidents` | "Cómo ve RR. HH. los incidentes" | `___` |
| `/admin/compliance-findings` (desktop, EN-only) | "How findings work" | `___` |
| `/admin/governance` (desktop) | Linkage Health pill visible with live N count | `___` |

---

## 5 · Mobile FL Dashboard overflow (iter365 regression lock)

```bash
# Or open in a mobile browser at 390px
curl -sI "$PROD/field-leadership/portal" | head -3
```

| Probe | Expected | Production result |
|---|---|---|
| Page loads | 200 | `___` |
| Horizontal scroll at 390px | none | `___` |

---

## 6 · Signoff

```
Section 1 (endpoint smoke):     PASS / FAIL    Operator initials: ____
Section 2 (iter363 dropdown):   PASS / FAIL    Operator initials: ____
Section 3 (linkage lifecycle):  PASS / FAIL    Operator initials: ____
Section 4 (coaching parity):    PASS / FAIL    Operator initials: ____
Section 5 (mobile FL):          PASS / FAIL    Operator initials: ____

Overall deploy verdict: GREEN  / YELLOW (notes below) / RED (ROLLBACK)

Notes / surprises:
______________________________________________________________________________
______________________________________________________________________________
______________________________________________________________________________

Signed:   ____________________________
Date:     ____________________________
Iter HEAD on prod: iter367
```

---

## 7 · Rollback procedure (if Section 1, 2, or 3 fails)

1. Emergent dashboard → **Deployments** → previous successful deploy → **Rollback**.
2. Re-run Section 1 above — endpoint codes should match the *pre-deploy* baseline.
3. File a ticket noting: (a) which probe failed, (b) the production error response, (c) preview baseline for the same probe.
4. **Do not retry the deploy** until the failing iter is reproducible on preview.
