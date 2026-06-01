# Production Deploy Readiness Report · Sprint 1C/1D

**Batch:** OMEGA Critical Fix Sprint 1C (Incident Delete) + 1D (UI Hygiene)
**Date:** 2026-02-27
**Subject:** Production deployment readiness assessment based on preview-environment certification.
**Audience:** Operator (final go/no-go owner).
**Predecessor file:** `PRODUCTION_DEPLOY_READINESS_REPORT.md` (2026-05-29, redeploy-readiness gate). This report supersedes nothing — it is a sprint-specific deploy gate.

This report is **read-only**. No production write occurred during its preparation. Per OMEGA directive: "Preview first. Do not deploy production." The deploy itself remains the operator's explicit decision.

---

## 1 · Executive verdict

# 🟢 GO TO DEPLOY

Both stages of Sprint 1C/1D pass every required check on the preview environment:

* 7/7 incident-delete pytest cases pass.
* 16/16 regression probes return 200 / 401 as expected.
* 6/6 role-permission probes confirm safety / no-token tokens are rejected and admin / PM tokens unlock as designed.
* 0 production database writes during the entire sprint.
* Backend + frontend lint clean across all 4 modified files.

The patches are surgical, identifier-strict, audit-emitting, and reversible: rolling back is a single `git revert` of the four code files. No DB schema change. No new collection. No new env variable.

---

## 2 · Deployment payload manifest

| Type | File | Change shape | Reversibility |
|---|---|---|---|
| Backend | `backend/routes/safety.py` | DELETE route logic only; helpers & imports unchanged | `git revert` restores 5-line legacy route |
| Frontend | `frontend/src/pages/HrHub.jsx` | One className delta on Sign Out button | `git revert` |
| Frontend | `frontend/src/pages/IncidentsDashboard.jsx` | Catch block expanded; no logic outside catch changed | `git revert` |
| Frontend | `frontend/src/pages/ViewIncident.jsx` | Catch block expanded; identical pattern | `git revert` |
| Tests | `backend/tests/test_sprint1c_incident_delete.py` | New file (preview fixtures only; tests are skipped if no admin token available) | Delete file |

**No `.env` change. No new dependency. No new collection. No new index. No new background job.**

---

## 3 · Pre-deploy preflight (operator confirms)

| Check | Confirmation procedure |
|---|---|
| Production database is `masci_safety` (not `masci_safety_preview`) | `grep DB_NAME` in production env config |
| Production `APP_ENV=production` (or unset) | env config |
| Production `ADMIN_HMAC_SECRET` intact (delete relies on `require_admin` token contract) | env config |
| Production `audit_events` collection writable | Existing collection — already in use by `/api/admin/logout`, `/api/admin/login`, dispatch impersonate, PM impersonate, etc. |
| Production `corrective_actions.source_id` index present | Per `server.py:9415` — `db.corrective_actions.create_index("source_id")` runs at startup. |
| Production preview-vs-production build pipeline parity | Standard pattern — no deviation in this sprint. |

---

## 4 · Behavioural changes the operator should communicate

Three user-visible changes worth surfacing in release notes:

### 4.1 · `DELETE /api/incidents/{id}` returns HTTP 409 when CAPAs cite the incident

| Audience | Pre-Sprint behaviour | Post-Sprint behaviour |
|---|---|---|
| Safety / Admin / PM operator | Successful delete with no warning; orphan CAPAs left dangling | HTTP 409 + body: "Cannot delete incident — N corrective action(s) still reference it. Close or relink the CAPAs before deleting." UI toast surfaces this exact message. |
| Audit reviewer | No audit row written on delete | `audit_events.kind=incident_deleted` row with actor_role, ip, ua, doc_id, project_number |

**No automated regression risk:** there is no known caller (frontend or batch script) that depends on a successful 200 in the presence of linked CAPAs. The 409 is a strictly stricter precondition; legacy callers were previously producing orphan state silently.

### 4.2 · Doc-id acceptance on delete

The route now accepts either `id` (UUID) or `doc_id` (`INC-YYYY-NNNNN`) as the path argument. Pre-Sprint, only UUID worked; passing a doc_id returned 404. Post-Sprint, both shapes work and the response body returns both ids:

```json
{"deleted": true, "id": "<uuid>", "doc_id": "INC-2026-00099"}
```

**No regression risk:** the frontend already passes UUID; the doc_id branch only adds flexibility for CSV-driven admin scripts.

### 4.3 · Toast wording

Operators will see five new toast variants on the incident-delete page (replacing the single `"Delete failed"`). Wording is plain English and translatable (ViewIncident wraps in `t()`).

* 401 → "Permission denied. Admin or PM sign-in required to delete incidents."
* 404 → "Incident not found. It may already be deleted." (and list prunes / page redirects.)
* 409 → server-provided detail message (e.g. "Cannot delete incident — 2 corrective action(s) still reference it. …")
* 5xx → "Server error (HTTP {code}). Try again or contact support."
* Other / network → "Delete failed (HTTP {code|network})"

---

## 5 · Rollback plan

If a defect surfaces in production:

1. **Backend rollback:** `git revert <commit-sha-for-safety.py>` → safety.py returns to the 5-line legacy delete. Supervisor hot-reload picks up the change. Total time-to-revert: < 60 seconds.
2. **Frontend rollback:** `git revert` the 3 frontend files. The build is hot-reloaded by the preview pod / restarted by the supervisor in production. Total time-to-revert: < 2 minutes.
3. **Audit events written under the new contract:** remain in `audit_events`. They are append-only metadata; rolling back the route does not invalidate them.
4. **No DB cleanup required on rollback.** No schema change was applied.

---

## 6 · Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Operator passes doc_id that collides with a UUID prefix | Vanishing — UUIDs are 36-char hex with dashes; doc_ids are `INC-YYYY-NNNNN`. Resolution is exact-match. | n/a | n/a |
| 409 surfaces orphan CAPA references from previous hard-deletes | Possible (pre-Sprint hard-delete left orphan CAPAs) | Operator cannot delete the new incident until they close/relink the orphan CAPAs | Operator can clean orphan CAPAs via Safety Portal CAPA panel — same workflow that existed pre-Sprint. |
| Audit insert fails (e.g. Mongo transient) | Low | Delete still succeeds; audit row missing for one event | Failure is swallowed by design (delete contract is the priority). Audit gap can be detected via `audit_events.count_documents` over time. |
| Frontend i18n surfaces template literal in ES locale | Low | English fallback string shown | Both surfaces use `t()` on the user-visible string; the template-literal HTTP-code interpolation is intentionally English-only (technical code). |
| Sibling routes (inspections / meetings / jhas) regress | None — they were not modified | n/a | Confirmed by §2.6 of `CRITICAL_FIX_SPRINT1C1D_CERTIFICATION.md` — all still return 401 on no-token DELETE. |
| HR Hub Sign Out button visual regression | None — CSS-class delta only | n/a | Lint clean, no JSX-tree change. |

---

## 7 · Post-deploy verification recipe (operator should run after deploy)

Against `https://mascidocs.com` (admin token required):

```bash
# 1 · Auth gate intact
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE \
  https://mascidocs.com/api/incidents/post-deploy-probe
# expected: 401

# 2 · Admin delete to a doc that does not exist
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE \
  -H "X-Admin-Token: <admin-token>" \
  https://mascidocs.com/api/incidents/post-deploy-probe-uuid
# expected: 404

# 3 · Confirm audit visibility
curl -s -H "X-Admin-Token: <admin-token>" \
  "https://mascidocs.com/api/admin/audit?kind=incident_deleted&limit=5"
# expected: 200, JSON list (empty if no real delete has occurred yet)

# 4 · Sibling read endpoints still 200
curl -s -o /dev/null -w "%{http_code}\n" -H "X-Admin-Token: <admin-token>" \
  https://mascidocs.com/api/incidents
# expected: 200

# 5 · HR Hub Sign Out button visually consistent on dark header
#    (no automation — operator manual check at https://mascidocs.com/hr)
```

If any probe deviates from expected, run rollback (§5) and notify ForgedOps.

---

## 8 · Sign-off

| Surface | Verdict |
|---|---|
| Preview backend tests | 🟢 7/7 |
| Preview regression probes | 🟢 16/16 |
| Preview role/permission probes | 🟢 6/6 |
| Lint (backend + frontend) | 🟢 |
| Production data safety | 🟢 0 prod writes during sprint |
| Patches reversibility | 🟢 single `git revert` per file |
| Schema / env / index footprint | 🟢 zero new |
| OMEGA discipline | 🟢 every "NO" rule observed |

# 🟢 GO TO DEPLOY

🛑 STOP. Awaiting operator's explicit production-deploy authorization.
