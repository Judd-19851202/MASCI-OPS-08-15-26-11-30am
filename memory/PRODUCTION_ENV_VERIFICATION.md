# PRODUCTION ENV VERIFICATION

**Date**: 2026-02-12 · **Mode**: closure

---

## AGENT BOUNDARY

**Cannot**: Read production env from the preview pod. Production env is managed by the operator in the Emergent deployment dashboard.
**Can**: Define exact required values, exact operator commands to verify them, and exact mechanical PASS/FAIL rules.

---

## REQUIRED PRODUCTION ENV VALUES

```
APP_ENV=production
ENVIRONMENT=production
DB_NAME=masci_safety           ← must NOT equal "masci_safety_preview"
MONGO_URL=mongodb+srv://<user>:<pwd>@<host>/?retryWrites=true&w=majority
                               ← Atlas cluster may be same as preview; DB_NAME is the separator
REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host  (or operator-confirmed prod hostname)
                               ← must NOT equal the preview URL
RATE_LIMITING=on
SCHEDULER_ENABLED=true
```

---

## OPERATOR VERIFICATION COMMANDS (from production pod terminal)

```bash
# Block 1 — env snapshot (mask secrets):
python3 -c "
import os
keys = ['APP_ENV','ENVIRONMENT','DB_NAME','RATE_LIMITING','SCHEDULER_ENABLED']
for k in keys:
    print(f'{k}={os.environ.get(k, \"<UNSET>\")}')
print('MONGO_host=', (os.environ.get('MONGO_URL','')[:30] + '...') if os.environ.get('MONGO_URL') else '<UNSET>')
print('REACT_APP_BACKEND_URL=', os.environ.get('REACT_APP_BACKEND_URL', '<UNSET>'))
"
```

**Expected output**:
```
APP_ENV=production
ENVIRONMENT=production
DB_NAME=masci_safety
RATE_LIMITING=on
SCHEDULER_ENABLED=true
MONGO_host=mongodb+srv://<user>:<pwd>@masci-pr...
REACT_APP_BACKEND_URL=https://<production-host>
```

```bash
# Block 2 — Mongo ping + DB name confirm:
python3 -c "
import os
from pymongo import MongoClient
client = MongoClient(os.environ['MONGO_URL'])
print('Ping:', client.admin.command('ping'))
print('Default DB targeted:', os.environ['DB_NAME'])
print('Collections in target DB:', sorted(client[os.environ['DB_NAME']].list_collection_names()))
"
```
**Expected**: `Ping: {'ok': 1.0}` · `Default DB targeted: masci_safety` (NOT `masci_safety_preview`) · collections list shows production seed state.

```bash
# Block 3 — preview URL check:
echo "$REACT_APP_BACKEND_URL" | grep -i "preview" && echo "FAIL: preview substring in prod URL" || echo "PASS: production URL"
```
**Expected**: `PASS: production URL`.

---

## MECHANICAL PASS RULES

| Rule | Pass condition |
|---|---|
| R1 | `APP_ENV == "production"` |
| R2 | `ENVIRONMENT == "production"` |
| R3 | `DB_NAME != "masci_safety_preview"` |
| R4 | `MONGO_URL` host parses successfully · ping returns `{'ok': 1.0}` |
| R5 | `REACT_APP_BACKEND_URL` does NOT contain substring `preview` |
| R6 | `RATE_LIMITING == "on"` |
| R7 | `SCHEDULER_ENABLED == "true"` |

If all 7 rules PASS → **PASS**. Any rule fails → **FAIL** and production is held.

---

## EVIDENCE BLOCK (operator paste-in)

```
APP_ENV               : __________________________
ENVIRONMENT           : __________________________
DB_NAME               : __________________________
Mongo ping result     : __________________________
REACT_APP_BACKEND_URL : __________________________
RATE_LIMITING         : __________________________
SCHEDULER_ENABLED     : __________________________

R1 (APP_ENV)          : [ ] PASS · [ ] FAIL
R2 (ENVIRONMENT)      : [ ] PASS · [ ] FAIL
R3 (DB_NAME)          : [ ] PASS · [ ] FAIL
R4 (Mongo ping)       : [ ] PASS · [ ] FAIL
R5 (URL ≠ preview)    : [ ] PASS · [ ] FAIL
R6 (RATE_LIMITING)    : [ ] PASS · [ ] FAIL
R7 (SCHEDULER_ENABLED): [ ] PASS · [ ] FAIL

Date verified  : __________________________
Operator sig   : __________________________
```

---

## VERDICT

* **Code layer**: ✅ all values are env-driven · no hardcoded production constants.
* **Operator action**: ⏳ paste values + run verification commands.

Until operator paste-in shows all 7 rules PASS: **FAIL**.

After paste-in passes: **PASS**.
