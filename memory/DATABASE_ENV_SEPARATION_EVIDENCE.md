# DATABASE / ENVIRONMENT SEPARATION EVIDENCE

**Date**: 2026-02-12 · **Mode**: closure (evidence-based)

---

## EVIDENCE — PREVIEW (directly observed)

```
MONGO_URL  host  : masci-prod.1nduwmg.mongodb.net      (Atlas cluster)
DB_NAME           : masci_safety_preview              ← verified in /app/backend/.env line 2
APP_ENV           : preview                            ← verified in /app/backend/.env line 3
PUBLIC_BASE_URL   : https://safety-audit-mobile-1.preview.emergentagent.com
                       (resolved via REACT_APP_BACKEND_URL · frontend/.env line 1)
```

---

## EVIDENCE — PRODUCTION (operator-managed · not visible from preview)

Production env is managed in the Emergent platform's deployment dashboard, not in this preview pod. Operator must execute the following commands on the production pod (or in the Emergent dashboard secrets panel) and paste the results below to complete this evidence file.

### Operator commands to gather production evidence

```bash
# In the production pod terminal:
echo "MONGO host : $(echo "$MONGO_URL" | sed -E 's|.*@([^/]+)/.*|\1|')"
echo "DB_NAME    : $DB_NAME"
echo "APP_ENV    : $APP_ENV"
# Frontend production URL is build-time injected:
grep REACT_APP_BACKEND_URL /app/frontend/.env || true
```

### Required PASS values (the only acceptable production state)

```
MONGO host     : masci-prod.1nduwmg.mongodb.net          ← may be SAME cluster as preview (acceptable per Atlas pattern)
DB_NAME        : <anything except "masci_safety_preview"> ← MUST differ from preview
APP_ENV        : production                              ← exact string
REACT_APP_BACKEND_URL : https://<production-host>.emergent.host
                                                          OR https://mascidocs.com
                                                          MUST not equal the preview URL above
```

### Operator paste-in block (operator fills after running the commands)

```
PRODUCTION MONGO host     : __________________________
PRODUCTION DB_NAME        : __________________________
PRODUCTION APP_ENV        : __________________________
PRODUCTION PUBLIC_BASE_URL: __________________________

Date verified             : __________________________
Operator signature        : __________________________
```

---

## VERIFICATION RULES (executed against the paste-in block)

* Production `DB_NAME` MUST NOT equal `masci_safety_preview` → PASS
* Production `PUBLIC_BASE_URL` MUST NOT equal the preview URL → PASS
* Production `APP_ENV` MUST equal exactly `production` → PASS
* If production secrets list `MONGO_URL` ≠ preview `MONGO_URL` → bonus PASS
* If any rule fails → FAIL

---

## VERDICT

| Side | Verdict | Notes |
|---|---|---|
| Preview side | **PASS** | DB_NAME `masci_safety_preview` · APP_ENV `preview` · public URL `*.preview.emergentagent.com` — verified in this pod's `.env`. |
| Production side | **OPERATOR-PENDING** | Block left for operator paste-in. Rules above mechanically determine PASS/FAIL once filled. |

**Net verdict**: PASS (preview) · OPERATOR-PENDING (production). Until operator paste-in confirms production values comply with the rules, this control is unverified.
