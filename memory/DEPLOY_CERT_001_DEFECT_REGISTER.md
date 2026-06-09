# DEPLOY-CERT-001 · Defect Register

**Sprint:** DEPLOY-CERT-001 · 2026-06-09  
**Severity scale:** P0 deploy-blocker · P1 major operational · P2 non-blocking operational · P3 cosmetic

---

## P0 — deployment blockers

**None.**

---

## P1 — major operational issues

### P1-01 · Backup writer leaves orphan `.tmp.<hash>` files; disk fills to 100 %

| Field                     | Value |
|---------------------------|-------|
| Detected during           | This certification (live disk exhaustion at 14:55 UTC) |
| File                      | `/app/backend/backups/` |
| Symptom                   | Three abandoned `.tmp.<hash>` files (605 + 568 + 378 MB ≈ 1.55 GB) accumulated when the upstream call was interrupted by the 60-second gateway timeout during `POST /api/admin/backup-verification/run-now`. Local disk hit 100 % full. |
| Root cause (hypothesis)   | The backup pipeline opens a temp file (`MASCI_full_backup_<ts>.zip.tmp.<hex>`), streams MongoDB collections into it, then renames atomically on completion. When the request is killed mid-stream the file descriptor is held by a child process and the file persists. There is no startup-time sweep of orphan temp files. |
| Reproduction              | Trigger `POST /api/admin/backup-verification/run-now` via the public gateway. Cloudflare disconnects at 60 s; the backend child process continues writing for several more minutes; the `.tmp.<hash>` artefact remains on disk after the run is abandoned. |
| Why it matters            | Production disk would silently fill if the operator ever clicks the admin "Run Backup Now" button via the gateway. Subsequent scheduled runs would also fail until the orphan files are manually deleted. |
| Recommended fix           | (a) On scheduler startup, sweep `/app/backend/backups/*.tmp.*` older than 10 minutes. (b) Use `tempfile.NamedTemporaryFile(delete=True)` inside a `finally` block. (c) Increase backend write timeout above the gateway 60 s, or stream archive to R2 directly without a local temp. |
| Workaround (now)          | Backend was restarted to release the deleted file handles; disk reclaimed from 100 % → 86 %. Ops runbook entry should be added. |
| Severity rationale        | Affects production reliability under operator-triggered backups. Not auto-triggered by scheduler (scheduled runs to date have all completed before any timeout). Therefore P1, not P0. |

---

## P2 — non-blocking operational issues

### P2-01 · `test_hr_portal_iter71.py` HR-login fixture is stale

| Field                | Value |
|----------------------|-------|
| File                 | `backend/tests/test_hr_portal_iter71.py` |
| Failing tests        | `TestHrAuth::test_login_returns_token` (FAIL · 401) + `TestHrAuth::test_me_with_valid_token`, `TestHrData::test_*` (ERROR · cascading auth fixture) — 1 fail, 8 errors |
| Symptom              | Hardcoded `HR_PASSWORD = "HRPortal2026!"` no longer matches DB seed; login returns `{"detail":"Invalid email or password"}` |
| Live impact          | None. Production HR users authenticate via `/api/auth/multi-login` with their actual credentials (verified during PROJECT-IDENTITY-005 sprint). |
| Recommended fix      | Update the fixture to obtain the current HR-manager password from `test_credentials.md`, OR reseed the HR user with the test password as part of test setup. |

### P2-02 · Daily Reports DELETE tests expect 200/404 but endpoint now returns 410 Gone

| Field                | Value |
|----------------------|-------|
| File                 | `backend/tests/test_daily_reports.py:140, :147` |
| Failing tests        | `TestDailyReportCRUD::test_delete_and_verify_removed`, `test_delete_404_for_unknown` |
| Symptom              | `assert 410 == 200` / `assert 410 == 404` |
| Reason               | The DR delete endpoint was intentionally changed to a soft-delete model that returns `410 Gone` to signal the document is "removed but historically preserved." The tests were never updated. |
| Live impact          | None. Production behavior is desired. |
| Recommended fix      | Update assertions to expect `410`, or split into two test branches (one for unknown-id 404, one for soft-deleted 410). |

### P2-03 · Phase 2 dashboard seed test long-deferred (5th recurrence)

| Field                | Value |
|----------------------|-------|
| File                 | `backend/tests/test_trench_safety_phase2.py::test_dashboard_seed_data` |
| Status               | Deferred since Feb 2026 under OMEGA discipline. 5th recurrence in the handoff history. |
| Live impact          | None — Trench Safety hub fully operational (verified via PROJECT-IDENTITY-001 audit). |
| Recommended fix      | Re-seed the dashboard fixture, or convert to a snapshot-driven assertion. |

### P2-04 · No fresh backup-verification run since 2026-05-25 scheduled

| Field                | Value |
|----------------------|-------|
| Detected             | `/api/admin/backup-verification/state` → `last_run_iso: 2026-05-25T14:00:00` |
| Live impact          | Scheduler is configured (next fire 2026-06-15). Latest `complete-r2` archive on R2 is dated 2026-05-31 (good); but the **verification email** has not been re-sent since 2026-05-25. |
| Recommended fix      | Trigger `POST /api/admin/backup-verification/run-now` (after P1-01 fix) and confirm a fresh email arrives. |

---

## P3 — cosmetic / advisory

### P3-01 · weasyprint CSS `aspect-ratio` warnings

Backend log shows continuous `Ignored \`aspect-ratio: 4/3\` at 56:34, unknown property` warnings during every PDF generation. Output unaffected. Recommend either upgrading weasyprint or removing the unsupported CSS rule from the PDF stylesheet.

### P3-02 to P3-06 · Pre-existing `react-hooks/set-state-in-effect` lint hits

The MCP linter reports five blocking warnings on:

| File                                                  | First introduced |
|-------------------------------------------------------|------------------|
| `frontend/src/pages/Dashboard.jsx`                    | Apr 2026 |
| `frontend/src/pages/EquipmentDashboard.jsx`           | Apr 2026 |
| `frontend/src/pages/IncidentsDashboard.jsx`           | Apr 2026 |
| `frontend/src/pages/MeetingsDashboard.jsx`            | Apr 2026 |
| `frontend/src/pages/PmQaqcList.jsx`                   | May 2026 |
| `frontend/src/components/AdminSafetyFormsPanel.jsx`   | May 2026 |
| `frontend/src/pages/JobPhotosLibrary.jsx`             | May 2026 |

The actual project ESLint config (used by webpack dev-server and CI builds) **does not have this rule enabled**, so production builds are unaffected. Left untouched per OMEGA. Cosmetic.

---

## Summary

| Severity | Count |
|----------|------:|
| P0       | 0 |
| P1       | 1 |
| P2       | 4 |
| P3       | ~6 |
