# DEPLOY-CERT-001 · Risk Register

**Sprint:** DEPLOY-CERT-001 · 2026-06-09

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|-----------|-------|
| R-01 · Operator clicks "Run Backup Now" via gateway → orphan `.tmp` files fill disk → next scheduled backup silently fails | MEDIUM (operator-triggered) | HIGH (silent loss of new backups until disk is cleared) | Pre-deploy: add ops runbook step "after manual backup, verify disk usage". Post-deploy: implement P1-01 fix. | Backend |
| R-02 · `usage_events` collection grows past Mongo's 33 MB in-memory sort limit during complete-r2 backup | LOW (already known; scheduled runs use a different code path that succeeds) | MEDIUM (only affects manual `run-now`; scheduled scope unaffected) | Add `allow_disk_use=True` to the `usage_events` aggregation; or skip telemetry collections from manual r2 runs. | Backend |
| R-03 · Stale pytest fixtures fail in CI and block automated regression gating | LOW (CI not currently gating PRs) | LOW (cosmetic / dev-velocity) | Update fixtures in a maintenance sprint. | Backend |
| R-04 · MaintainX + Motive integrations are MOCKED — features that depend on them appear "live" but never receive real telemetry | KNOWN | KNOWN (intentional design: read-only telemetry surface only when API keys configured) | Already surfaced in admin Integration Health page. No change required. | Operator |
| R-05 · Project Identity Governance queue (1,243 items in preview) overwhelms admin on first prod scan | MEDIUM | LOW (ID-006 prioritization sorts cert/test to tier 8) | Admin uses Top-10 cleanup list + filter by tier 1-4 for high-impact items first. Bulk-dismiss UX could be added in ID-007 (proposed). | Operator |
| R-06 · Email sending is OFF by default (`auto_email_enabled=false`) — operator-triggered only | INTENTIONAL | LOW (operator control prevents runaway notifications) | Documented in Integration Health probe. No action. | Operator |
| R-07 · No fresh restore drill since BACKUP-FIX-001 — archives exist but actual restore path not re-verified this sprint | LOW (archives are validated structurally on every scheduled run) | HIGH if restore is ever needed and fails | Owner may authorize DEPLOY-CERT-002 with explicit DR scope before deploy. | Operator |
| R-08 · Mobile re-test not executed this fork (inherited certifications stand) | LOW (last cert ≤ 30 days old) | LOW | Optional re-test sprint. | Operator |
| R-09 · 295 frontend routes — high surface area for hidden dead routes | LOW (smoke screenshot showed nav working) | LOW | Periodic Lighthouse / route-walker sprint. | Frontend |
| R-10 · Resend key present, auto-email OFF — first real send may surprise recipients | INTENTIONAL | LOW (operator-initiated) | Communicate first-send plan to recipients. | Operator |

---

## Residual Risks Accepted (if proceeding under CONDITIONAL PASS)

If owner accepts the §3 conditions without remediation:

- **R-01** stays open until P1-01 ships.
- **R-03** stays open until maintenance sprint.
- **R-07** stays open until DR drill authorized.

All other risks are either intentional (R-04, R-06, R-10), already mitigated (R-05), or low-likelihood (R-02, R-08, R-09).
