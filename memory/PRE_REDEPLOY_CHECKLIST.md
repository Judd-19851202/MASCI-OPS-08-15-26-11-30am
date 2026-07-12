# PRE-REDEPLOY CHECKLIST · iter330 → iter353c Stack
**Purpose:** 5-minute, operator-runnable smoke that validates the production redeploy unlocked every iter currently trapped in preview.
**Audience:** Jaymn / non-engineer can run this from any laptop with `curl` + a browser.
**Estimated time:** 5 minutes manual · 1 minute scripted.

---

## Phase A · BEFORE you click "Deploy"
### A1 · Confirm preview health
```bash
curl -s https://backup-forensics.preview.emergentagent.com/api/health
# Expect: {"ok":true,"service":"masci-hub","ts":"..."}
```

### A2 · Confirm cumulative regression is green
```bash
cd /app/backend && python -m pytest tests/test_iter35*.py 2>&1 | tail -3
# Expect: "123 passed" (or higher if new iters landed)
```

### A3 · Snapshot the production endpoint state (proves drift is real)
```bash
# These MUST return 404 in prod BEFORE deploy:
for ep in \
  "/api/hr/employees/test/accountability/timeline" \
  "/api/hr/employees/test/accountability/brief.pdf" \
  "/api/dispatch/driver-qualification" \
  "/api/hr/driver-qualification/import/apply" ; do
  echo "$ep → $(curl -sw '%{http_code}' -o /dev/null https://mascidocs.com$ep -H 'X-Admin-Token: any')"
done
# Expect: 404 · 404 · 404 · 404
```
If ANY of these returns 401/405 already, the deploy is partial or already happened — STOP and investigate before clicking Deploy.

---

## Phase B · DEPLOY
Click "Deploy" in the Emergent dashboard. Watch for completion.

---

## Phase C · IMMEDIATELY AFTER (smoke validation · 60 seconds)
### C1 · Endpoint existence flip (404 → 401)
```bash
for ep in \
  "/api/hr/employees/test/accountability/timeline" \
  "/api/hr/employees/test/accountability/brief.pdf" \
  "/api/dispatch/driver-qualification" \
  "/api/field-leadership/portal/driver-qualification" \
  "/api/hr/driver-qualification/import/apply" ; do
  echo "$ep → $(curl -sw '%{http_code}' -o /dev/null https://mascidocs.com$ep -H 'X-Admin-Token: any')"
done
# Expect: 401 · 401 · 401 · 401 · 405
# (405 on import/apply is correct — anonymous can't even GET the POST endpoint)
```
If ANY still returns 404, deploy did not include the iter — escalate.

### C2 · FL DQ payload shape (slim iter314 → rich iter353b)
```bash
# Mint FL token
FL=$(curl -s -X POST https://mascidocs.com/api/field-leadership/portal/login \
  -H "Content-Type: application/json" \
  -d '{"email":"fieldleader@mascigc.com","password":"FieldLead2026!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
curl -s "https://mascidocs.com/api/field-leadership/portal/driver-qualification" \
  -H "X-FL-Token: $FL" -H "X-Admin-Token: " \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('summary keys:',list(d.get('summary',{}).keys()))"
# Expect: ['cdl_expiring_30d', 'medical_card_expiring_30d', 'restricted', 'suspended',
#          'tanker_capable', 'available_now', 'available_now_cdl', 'available_now_non_cdl']
# 8 keys = iter353b + iter353b-availability landed.
# Only 0-3 keys = old iter314 shape still deployed.
```

### C3 · Multi-portal login smoke
| Portal | URL | Expected |
|---|---|---|
| HR | `mascidocs.com/hr/login` | hrmanager@mascigc.com / `HRTesting2026!` → dashboard loads |
| Safety | `mascidocs.com/safety/login` | safety-portal credentials → safety hub loads |
| PM | `mascidocs.com/pm/login` | chriswright@mascigc.com / `ChrisRocksThis2026` → PM hub |
| FL | `mascidocs.com/field-leadership/login` | fieldleader@mascigc.com / `FieldLead2026!` → FL dashboard |
| Dispatch | `mascidocs.com/dispatch-portal/login` | dispatch credentials → dispatch hub |
| Shop | `mascidocs.com/shop-portal/login` | shop credentials → shop hub |
| Admin (multi) | `mascidocs.com/login` (super-admin) | jaymn.judd@mascigc.com / `Maddix123!` → multi-portal directory |

---

## Phase D · OPERATOR WORKFLOW VERIFICATION (4 minutes · BROWSER)
### D1 · iter353c Accountability Timeline (HR portal)
1. Log in as HR (`/hr/login`)
2. Navigate to `/hr/employees`
3. **Verify** every row shows an `Accountability` link in the new column
4. Click the link for **Alec Perkins** (employee id `250d2712-6be3-440e-9de9-1941c5a735d6`)
5. **Verify** page loads with employee header · 6 status tiles · 7 tabs · Compliance Brief PDF button
6. Click **Compliance Brief PDF** → download starts → open PDF → verify "HR Compliance Brief" title + employee name

### D2 · iter353b Dispatch Driver Readiness
1. Log in as Dispatch (or super-admin → use multi-portal Dispatch token)
2. Navigate to `/dispatch-portal/driver-qualification`
3. **Verify** emerald "Drivers Available Right Now" hero tile renders at the top
4. **Verify** 5 summary tiles below (Drivers in scope · CDL ≤30d · Medical ≤30d · Restricted · Suspended)
5. Click the hero tile → table filters to dispatchable drivers only → tile inverts to solid emerald
6. Click again → filter clears

### D3 · iter353b FL Driver Readiness
1. Log in as FL
2. From dashboard, click the **Driver Qualification** card
3. **Verify** new page at `/field-leadership/portal/driver-qualification` renders with red accent + same tiles/filters as Dispatch view
4. **Verify** the availability tile shows the same `available_now` count as Dispatch (parity).

### D4 · iter352 CDL Roster Importer
1. Log in as HR
2. Navigate to `/hr/driver-qualification/import`
3. **Verify** importer page loads with file-drop zone + preview step
4. **DO NOT** apply unless intentionally re-running the iter351 bulk load (see D5)

### D5 · iter351 CDL Bulk Load (DATA RE-RUN · only after step D1-D4 pass)
The 82-driver bulk load was applied to preview's `employees` collection, not production. After deploy:
1. Export the preview CDL roster: hit `/api/hr/driver-qualification/dashboard?limit=2000` with HR token, save items.
2. Re-import into prod via the iter352 importer (`/hr/driver-qualification/import` page).
3. Verify: `curl https://mascidocs.com/api/hr/driver-qualification/dashboard?limit=2000 -H "X-HR-Token: $HR" | python3 -c "import sys,json;print(json.load(sys.stdin)['count'])"` ≈ 82–86 drivers.

---

## Phase E · MOBILE + ES PARITY (1 minute)
1. Open `https://mascidocs.com/hr/employees/{id}/accountability` on a phone (or 390-width browser)
2. Verify event rows render as cards, no horizontal scroll
3. Toggle language to ES → verify status tile labels render in Spanish
4. Verify Compliance Brief PDF download still works from mobile

---

## Phase F · POST-DEPLOY SIGNOFF
- [ ] All Phase C probes returned correct codes
- [ ] D1 timeline page loaded + PDF downloaded
- [ ] D2 Dispatch DQ tile clickable + filter works
- [ ] D3 FL DQ parity confirmed
- [ ] D5 CDL roster re-loaded (if needed)
- [ ] E1 mobile + ES verified

Sign and date below when complete:
```
Verified by: ____________________
Date:        ____________________
Production version: iter353c · iter353b · iter353b-availability
```

---

## Rollback procedure (if any step fails)
1. From Emergent dashboard → Deployments → previous successful deployment → **Rollback**.
2. Re-run Phase A3 — endpoints should return to 404.
3. Notify Jaymn with the specific failing step + error message.
4. File a ticket: which iter is failing on prod that worked on preview?

---

## Reference: iters being deployed in this batch
- iter330 → iter349 (per handoff history · 20 bounded iters)
- **iter350** — HR Safety + CDL + Certificate Visibility Convergence
- **iter351** — PROD CDL Bulk Load (data layer · re-run via importer)
- **iter352** — Self-Service CDL Roster Importer
- **iter353** — Platform Governance Audit (markdown only)
- **iter353a** — Shared Employee Accountability backend
- **iter353a-UI** — HR Safety Records write surfaces
- **iter353b** — Dispatch + FL Read-Only Driver Qualification
- **iter353b-availability** — Drivers Available Right Now tile
- **iter353c** — Unified Accountability Timeline + HR Compliance Brief PDF

Total: **24 bounded iters · 123 regression-locked pytest items · zero drift** between preview and the iter353c HEAD.
