# DR-UNIFY-004 · Rollback Plan

## Rollback triggers

Roll back if any of the following surfaces in production:

- `POST /api/daily-reports` returns 5xx on a valid submission.
- HR crew CSV export shows missing rows.
- PDF renderer errors on a valid report.
- ODS `operational_facts` writes fail.
- Admin AI Configuration page cannot render.
- Any provider API key value appears in an admin-visible surface.

## Rollback surfaces

Each of this session's tracks is independently rollback-safe.

### AI-CONFIG-001 (Feb 2026)

- Rollback: delete added rows in `backend/.env` and `.env.example`,
  revert `services/ai_gateway/capabilities.py` + `routes/ai_gateway_status.py`.
- Data impact: none (no writes).
- Downstream: none.

### AI-ADMIN-001 (Feb 2026)

- Rollback: delete `routes/ai_admin_config.py`, revert the 7-line
  register hunk in `server.py`; delete the frontend page +
  routing/nav edits.
- Data impact: `tenant_ai_capabilities` and
  `tenant_ai_capability_audit` collections become dormant — safe to
  ignore.
- Downstream: none.

### DR-CUTOVER-002 (Feb 2026)

- Rollback: delete `routes/daily_summary.py`, revert the 11-line
  register hunk in `server.py`; delete the frontend section +
  2-line mount in `NewDailyReport.jsx`.
- Data impact: `daily_operational_summary_*` fields become dead
  weight on submitted docs — safe.
- Downstream: none (V1 submit path is loose-coupled).

### DR-UNIFY-003 (Feb 2026)

- Rollback: revert the 3-line change to `AppRoutes.jsx` (put the
  `DailyReportV2` import + route element back).
- Data impact: none (no writes; migration was dry-run only).
- Downstream: none.

## Full-track rollback recipe (worst case)

```
# Backend
rm backend/routes/ai_admin_config.py
rm backend/routes/daily_summary.py
rm backend/lib/daily_report_collections.py
rm backend/scripts/migrate_dr_v2_collections_to_daily_report.py
git checkout backend/server.py backend/.env

# Frontend
rm frontend/src/components/daily-report/DailyOperationalSummarySection.jsx
rm frontend/src/pages/admin/AdminAIConfiguration.jsx
git checkout frontend/src/pages/NewDailyReport.jsx
git checkout frontend/src/app/routing/AppRoutes.jsx
git checkout frontend/src/components/admin/sidebar/domainMap.js
git checkout frontend/src/components/AdminShell.jsx

# Then
sudo supervisorctl restart backend frontend
```

Rollback time: **< 5 minutes**. Zero data actions required.

## Partial rollback (single track)

Each track's changed-file list is enumerated in its
`_EXECUTIVE_SUMMARY.md`. Reverting a single track is a per-file
`git checkout` operation plus a supervisor restart.

## Post-rollback verification

After any rollback:

1. `curl /api/health` → 200
2. `curl /api/daily-reports/approved` → responds (auth-gated or 200)
3. Log in as super-admin, verify existing admin surfaces render.
4. Submit a test daily report via `/daily/submit`, verify HR data
   preserved.
5. Confirm `operational_facts` write via ODS ingest hook.

## Never destroy

- Do not drop `daily_reports`, `operational_facts`, `operational_kpi_snapshots`,
  or any `dr_v2_*` legacy collection during rollback.
- Do not clear tenant_ai_capabilities* collections during rollback —
  they carry admin configuration state and become inert if the admin
  page is removed.
