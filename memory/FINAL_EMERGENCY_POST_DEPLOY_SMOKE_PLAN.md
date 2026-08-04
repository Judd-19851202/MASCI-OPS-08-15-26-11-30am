# Final Emergency Post-Deploy Smoke Plan

1. `GET /api/version` and `GET /api/platform/data-truth`
   - expect deployed commit/source hash to equal saved workspace bundle
2. Super Admin multi-login
   - expect success with session + portal tokens
3. PM multi-login
   - expect success
4. `/daily/submit`
   - expect `Submit Daily Report` label, clear readiness text, no lowercase Executive Summary label
5. Controlled Daily Report submission
   - expect clear `Submitting Daily Report…`, saved report reference, no duplicate
6. Controlled Daily Report email
   - expect branded content, no OPPC jargon, valid PDF, correct To/CC/BCC
7. Daily Report forensics
   - expect explicit end-state, no silent stop after record creation
8. Backup checks
   - expect fresh recoverable point and integrity PASS
9. Budget / Schedule / OI spot checks
   - expect core pages load for intended roles
10. Atlas targeting alert check
   - expect no materially worse condition
