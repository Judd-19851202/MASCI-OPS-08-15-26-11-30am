# TRACK 15.60 — Deployment Readiness

## Code change summary

| File | Lines changed | Risk | Type |
|---|---|---|---|
| `/app/frontend/src/pages/NewMeeting.jsx` | +35 LOC additive (imports, hook wiring, JSX additions) | LOW | autosave wiring |
| `/app/frontend/src/components/EmployeeCombo.jsx` | ~+45 LOC additive (replaced one method body, +1 import) | LOW | reliability fix |

**Backend:** zero changes. No new endpoint, no schema migration, no env-var changes.
**Database:** zero changes.
**Build pipeline:** zero changes.
**Dependencies:** zero new packages.

## Risk assessment

| Risk vector | Probability | Mitigation |
|---|---|---|
| Autosave hook crashes the Safety Meeting page | LOW | Same hook already shipping in 4 other forms (NewIncident, NewDailyReport, NewInspection, HrPayrollVariance) with proven track record back to iter440. |
| `useFormDraft` writes corrupt the `data` shape during restore | LOW | Restore is OPT-IN (`DraftRestorePrompt` requires explicit user click). If a previous draft is bad, the user can pick Discard. The schema is stable JSON; not lossy. |
| Resiliency queue swallows a request silently | LOW | `enqueueUpload` returns `{ok, queued, lastError, status}` and the success / queued / failed branches in the fix each surface a calm toast. The queue persists to IDB with `key=masci.resiliency.queue.v1`; the user can inspect via DevTools. |
| Idempotency key collision | NEGLIGIBLE | `mintIdempotencyKey()` uses crypto-strong UUIDs. The backend `POST /api/employee-requests` accepts duplicates idempotently (a second submit with the same key is a no-op). |
| Increased localStorage / IDB usage on iPad | LOW-MEDIUM | `useFormDraft` already includes a quota probe with calm operator warning at 80% (TF-004). The Safety Meeting draft is comparable in size to NewIncident/NewDailyReport drafts (~10–50 KB). |
| Hot-reload race during dev | n/a | Only affects preview env. |

## What this fix does NOT include (intentional)

- **Does not offline-queue the final Safety Meeting submission.** Adding `enqueueUpload` to the `POST /api/meetings` call is technically possible (mirrors `NewIncident`'s submit path), but it changes the success UX (operator may submit and not know if the server actually received it until reconnect). The current behaviour — autosave the draft locally, require operator to retry submit when the network is back — is the safer posture for a legal record like a Safety Meeting. Marked as backlog item; revisit if a future field report demands offline submission specifically.
- **Does not retroactively link approved HR requests back to old Safety Meeting attendee rows.** That would corrupt the audit trail. New meetings will pick up the new employee via `EmployeeCombo` after HR approval.
- **Does not add Request-to-Add to Equipment Issuance / Equipment Training forms.** No field-loss reported; backlog.

## Verification before deploy

| Check | Status |
|---|---|
| `yarn build` / hot-reload compiles | ✅ verified — frontend.out.log shows "Compiled successfully!" after each save |
| Lint passes on `NewMeeting.jsx` | ✅ no issues |
| Lint on `EmployeeCombo.jsx` | ⚠️ 2 pre-existing react/no-unescaped-entities warnings (unchanged by 15.60 — see git history) |
| Stress test runs locally on preview | ✅ 6/6 scenarios pass, cleanup leaves 0 tagged records |
| Smoke screenshot of `/meetings/new` | ✅ form renders, no errors, draft pill hidden until typing |
| Existing regression suites for safety meeting PDF | unchanged · not touched |

## Rollback plan

If a regression is discovered post-deploy:

1. **Single-file rollback** — `git revert` the two file changes. No DB / env / endpoint state to undo.
2. **Selective disable** — wrap the `useFormDraft` call in a feature flag (`localStorage.setItem("masci.meeting.autosave", "off")`) — quick toggle for one operator without redeploy. The hook returns harmless defaults when the IDB layer fails.
3. The HR queue + `POST /api/employee-requests` backend continues to work whether or not the FE uses `enqueueUpload`; the legacy `api.post` path is interchangeable.

## Deploy verification post-rollout

After deploy, re-run:

```bash
cd /app && python3 tests/post_deploy/track_15_60_stress_test.py
```

against the deployed URL by overriding `REACT_APP_BACKEND_URL=https://mascidocs.com python3 ...`. The cleanup contract ensures the production DB is unchanged after the run.

## Final readiness verdict

- ✅ All 11 Phase 1–9 deliverables produced
- ✅ Stress test 6/6 scenarios pass
- ✅ Zero left-over synthetic artefacts
- ✅ Backend untouched
- ✅ Schema untouched
- ✅ Risk profile: LOW

**🟢 GO for production redeploy.**
