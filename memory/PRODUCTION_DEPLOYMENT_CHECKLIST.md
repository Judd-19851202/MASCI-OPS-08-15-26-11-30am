PRODUCTION DEPLOYMENT CHECKLIST
================================

RELEASE: MASCI Operations Platform · Track 18 Production Cut
DATE   : 2026-02-15
OWNER  : jaymn.judd@mascigc.com

────────────────────────────────────────────────────────────────────────────
BEFORE DEPLOY
────────────────────────────────────────────────────────────────────────────
[ ] Scope frozen — see `PRE_DEPLOYMENT_RELEASE_FREEZE.md`
[ ] Backup complete — Atlas snapshot ID captured: __________________
[ ] R2 hourly backup timestamp confirmed < 1 hour old: __________________
[ ] Environment verified — see `PRE_DEPLOYMENT_ENVIRONMENT_CHECK.md`
    [ ] `MONGO_URL` swapped to production cluster
    [ ] `DB_NAME` swapped to production database name
    [ ] `APP_ENV` set to `production`
    [ ] Frontend `REACT_APP_BACKEND_URL` swapped to production backend
    [ ] All secrets present (verified via env check; values not printed)
    [ ] `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` allow production domains
[ ] Tests green — see `PRE_DEPLOYMENT_TEST_RESULTS.md`
    [ ] `python /app/scripts/deployment_gate.py` returns green
    [ ] `cd /app/backend && python -m pytest tests/test_track_18_* -q` green
    [ ] `cd /app/backend && python -m pytest tests/test_pre_deployment_release_safety.py -q` green
[ ] Role smoke green — see `PRE_DEPLOYMENT_ROLE_SMOKE_MATRIX.md`
[ ] Transportation acceptance green — see `PRE_DEPLOYMENT_TRANSPORTATION_ACCEPTANCE_GATE.md`
[ ] Release notes ready — see `RELEASE_NOTES_TRACK_18_PRODUCTION_CUT.md`
[ ] Rollback plan ready — see `PRE_DEPLOYMENT_DATA_SAFETY_CHECK.md`
[ ] Git SHA stamped: __________________ (`git log -1 --format=%H`)

────────────────────────────────────────────────────────────────────────────
DEPLOY
────────────────────────────────────────────────────────────────────────────
[ ] Build frontend                             `cd /app/frontend && yarn build`
[ ] Build/start backend                        `supervisorctl restart backend`
[ ] Confirm health endpoint                    `curl $PROD_URL/api/health` → 200
[ ] Confirm production URL resolves to new build
[ ] Confirm static assets loaded (HTTP 200 on `/static/js/*`)
[ ] Confirm API connectivity                   `curl $PROD_URL/api/health` from external client
[ ] Confirm version stamp                      `curl $PROD_URL/api/health/version` returns the captured SHA

────────────────────────────────────────────────────────────────────────────
AFTER DEPLOY (in order)
────────────────────────────────────────────────────────────────────────────
[ ] Public home smoke                          anonymous user opens `/` — hero copy = "MASCI Operations Platform"
[ ] Login smoke                                 `/admin/login` succeeds for Super Admin
[ ] Role smoke                                  Super Admin opens each portal (Administration · Transportation Operations · Project Management · Human Resources · Safety Operations · Shop Operations · Field Leadership · Operational Guidance Center)
[ ] Transportation smoke                        Dispatch user opens every visible /transportation-operations/* workspace (Mission Control · Drivers · Carriers · Trucks · Compliance · Orientation · Automation · Cleanup · Live Operations · Dispatch)
[ ] Dispatch smoke                              Dispatch board · Map · Haul ledger · Driver qualification · Fleet
[ ] Forms smoke                                 Safety forms · Field daily report · PO request · HR onboarding
[ ] Email / PDF smoke                            One canonical-name email triggered (e.g. orientation invite) — landing copy contains "Transportation Operations"
[ ] Logs check                                  Sentry shows no new unique errors in the 15 min post-deploy window
[ ] Error monitoring                            Backend supervisor + Sentry baseline rate within 2× pre-deploy
[ ] Backup / restore point confirmed             Snapshot ID captured pre-deploy still listed in Atlas console
[ ] Release note sent                            Internal release note emailed to ops mailing list

────────────────────────────────────────────────────────────────────────────
ROLLBACK TRIGGERS (any of these → rollback immediately)
────────────────────────────────────────────────────────────────────────────
- Login failure (`/admin/login`, `/sign-in`, `/dispatch-portal/login`)
- Production DB mismatch (count_documents on key collections deviates)
- Dispatch portal broken (drag/drop, map, ledger)
- Transportation core workspace broken (Drivers / Carriers / Trucks / Orientation / Mission Control)
- Red React runtime overlay surfaced to any role
- Auth / RBAC regression (admin endpoint accepting dispatch token unexpectedly OR vice versa)
- Missing critical env var (any item flagged BLOCKER in environment check)
- Data corruption risk (audit ledger non-monotonic, doc counts dropping)
- Deployment gate failure (`scripts/deployment_gate.py` returns non-zero)

ROLLBACK ACTIONS
  1. `git checkout <prev SHA> && supervisorctl restart backend`
  2. Redeploy previous frontend build artefact
  3. If data corruption: Atlas point-in-time restore from captured snapshot ID
  4. Notify operations channel

────────────────────────────────────────────────────────────────────────────
SIGN-OFF
────────────────────────────────────────────────────────────────────────────
Engineering: __________________________  Date: __________
Operations : __________________________  Date: __________
