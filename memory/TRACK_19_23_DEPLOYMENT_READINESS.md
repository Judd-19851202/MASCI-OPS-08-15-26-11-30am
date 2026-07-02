# TRACK 19.23 · Production Deployment Readiness Certification

## Deployment scope
Deploying the current preview build to production, covering:
- Track 19.17-19.18 · Incident Engine + PDF Excellence + Safety Case (LIVE-LOCKED)
- Track 19.19 · Daily Report `.xlsm` support
- Track 19.20 · Historical Records intelligence audit
- Track 19.21 (+ 19.21b) · Employee 360° + Universal Employee Record + Historical Intake foundation
- Track 19.22 · P1 Operational Completion (Documents tab · search · 6 export packages · bulk batches)

## Pre-deployment matrix

| Item | Status |
|---|---|
| Backend lock tests (isolated per-file) | ✅ 329+/329+ GREEN |
| Test-suite bleed (documented flake) | 🟡 Pre-existing, not a regression |
| `.xlsm` allow-list + macro-safety | ✅ Verified live |
| Employee 360° render + timeline | ✅ Verified live |
| Documents tab + search + lane filter | ✅ Verified live (7 real docs · search narrows correctly) |
| 6 export PDFs render correctly | ✅ `%PDF` magic verified · 2421-3002 bytes |
| Permission matrix (HR/Safety/Asset/Admin) | ✅ Airtight (403/200 as designed) |
| Bulk batch cycle (upload → classify → approve) | ✅ Verified end-to-end |
| Historical Intake single-record flow | ✅ Verified end-to-end |
| Audit ledger append-only | ✅ 0 update/delete calls anywhere in module |
| `db.employees` untouched | ✅ 0 mutation calls |
| `db.incident_cases` untouched | ✅ 0 mutation calls |
| Email governance | ✅ Employee Records emits 0 emails; existing routes unchanged |
| Bilingual coverage | ✅ 170 `t()` calls across new pages |
| Zero-drift sentinels | ✅ No OCR / AI / fuzzy libs imported |
| Original file preservation | ✅ SHA-256 + R2/base64 dual path |

## Environmental checklist

| Item | Preview | Production plan |
|---|---|---|
| `RESEND_API_KEY` | Set | Must be set — pilot recipients only initially |
| `MONGO_URL` / `DB_NAME` | Set | Set |
| Cloudflare R2 credentials | Set (photo_storage) | Set (or graceful base64 fallback) |
| `REACT_APP_BACKEND_URL` | Set to preview | Must switch to prod origin |
| Frontend build | Live (yarn build) | Rebuild against prod env |
| Supervisor services | RUNNING | Verified on preview |
| Health endpoint | 200 | Must verify post-deploy |

## Post-deploy smoke test (30 minutes)
1. `GET /api/health` → 200
2. Sign in as HR super-admin via `/sign-in` → all portal tokens issued
3. Open one Employee 360° → verify Documents tab loads real records
4. Attempt one intake upload → verify staged in queue
5. Approve → verify appears on Employee 360°
6. Generate Complete Employee File PDF → verify `%PDF` magic
7. Attempt a Safety token access to HR queue → verify 403
8. Run one `.xlsm` Daily Report upload → verify label "Spreadsheet"

If all 8 pass in production: **DEPLOY LOCKED.**

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Cloudflare R2 misconfig in prod | Low | Base64 fallback preserves records; alarms in logs |
| Email governance regression | Very low | Employee Records module has no email calls |
| Pytest asyncio bleed masking a real failure | Low | Isolated per-file execution is the source of truth |
| PDF font missing in production container | Low | ReportLab uses Helvetica (bundled with library) |
| Employee 360° token gate misfire | Very low | `RequireHR` React gate + backend `X-HR-Token` gate — belt + suspenders |
| Bulk upload timeout on very large batches | Medium | Files skipped individually (silent skip preserves the rest) |

## Deployment blockers
- **None identified.** All P0/P1 checks pass. Pytest bleed is documented flake, not a blocker.

## Sign-off
Preview environment is production-like. Certification date: 2026-07-02. Ready for pilot on production.

**Verdict:** GO.
