# Final Release Post-Deploy Smoke Plan

## Required immediate checks after user presses Deploy
1. **Identity** — `GET /api/version`, `GET /api/platform/data-truth`
   - expected: frontend/backend release match true; commit/source hash match deployed bundle
   - rollback trigger: mismatch or unknown release identity
2. **Login** — multi-login for Super Admin and PM
   - expected: success with usable session + portal tokens
   - rollback trigger: auth regression
3. **Daily Report submit** — `/daily/submit` and `POST /api/daily-reports`
   - expected: clear submit progress, success state, report reference shown, no duplicate
   - rollback trigger: save failure or ambiguous operator result
4. **Daily Report email** — controlled internal recipient
   - expected: branded Daily Report email, no OPPC jargon, valid PDF, correct To/CC/BCC
   - rollback trigger: generic email, missing PDF, no provider acceptance, duplicate send
5. **Notification truth** — admin Daily Report forensics + trust stages
   - expected: complete explicit outcome, no silent stop at `record_created`
   - rollback trigger: silent chain break or misleading admin evidence
6. **Backup health** — `/api/admin/backups-complete-r2-state`, `/api/admin/backups/integrity-check`
   - expected: fresh recoverable point still inside contract, integrity PASS
   - rollback trigger: freshness regression or integrity failure
7. **Operational Intelligence / schedule / budget**
   - expected: key admin/PM pages load without auth or console regressions
   - rollback trigger: high-severity role/workflow break
8. **Atlas alert check**
   - expected: no new pathological targeting introduced
   - rollback trigger: materially worse scan/latency condition
