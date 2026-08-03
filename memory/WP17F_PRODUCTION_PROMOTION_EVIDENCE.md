# WP-17F Production Promotion Evidence

## Rollback Point
- Release candidate commit: `c31011d18c20d46d99d67ffd76cc17a168a39135`
- Immediate predecessor anchor: `f12eacf2c509b068ba1b0357068419efcb0abae7`
- Verification command evidence:
  - `git -C /app rev-parse HEAD`
  - `git -C /app rev-parse HEAD^`
  - `git -C /app log --oneline -n 5`

## Release Version / Commit
- Frontend package version: `0.1.0`
- Release candidate commit: `c31011d18c20d46d99d67ffd76cc17a168a39135`

## Guards and Checks Passed
- Hidden-surface forensic regeneration: `python /app/scripts/wp17_hidden_surface_forensics.py` ✅
- Route-governance guard: `python /app/scripts/wp17_route_governance_guard.py` ✅
- Constitutional guard: `python /app/scripts/wp17d_constitution_guard.py` ✅
- Release-surface frontend lint: production surfaces clear after excluding known test-only files and the long-standing global `frontend/src/lib/i18n.js` duplicate-key noise; one shared utility lint defect in `frontend/src/lib/platformTime.js` was repaired ✅

## Deployment Result
- Release-candidate deployment readiness check executed in preview.
- Preview app available at `https://backup-forensics.preview.emergentagent.com`.
- No new Category 1 or Category 5 defect was detected during release review.

## Immediate Smoke-Test Results
- Executive smoke test passed `18/18` checks.
- Verified successfully:
  - Home and sign-in entry
  - Admin access
  - PM access
  - HR access
  - Safety access
  - Dispatch access
  - Shop access
  - Field Leadership access
  - Shared public entry routes: `/daily/submit`, `/fleet/dvir/new`, `/equipment/new`, `/incidents/report`, `/safety/inspections/new`, `/qaqc`
  - EN/ES switching
  - Mobile rendering smoke
  - Session restoration
- Evidence: `/app/test_result.md` executive smoke entry and saved screenshots listed there.

## Critical Workflow Results
- Portal-access and shared-entry spine smoke: ✅
- Daily report detail fixture: `/api/daily-reports/4cab04c6-a17d-47d6-a02c-2942538cfcd5` → `200` ✅
- Safety training detail fixture: `/api/safety-forms/equipment-trainings/603a1d13-0acb-4668-a83a-a7743982f92a` → `200` ✅
- Safety training PDF fixture: `/api/safety-forms/equipment-trainings/603a1d13-0acb-4668-a83a-a7743982f92a/pdf` → `200 application/pdf` ✅
- Safety issuance detail fixture: `/api/safety-forms/equipment-issuances/54e109fe-14d4-42a7-bb49-16ce4e8877a4` → `200` ✅
- Safety issuance PDF fixture: `/api/safety-forms/equipment-issuances/54e109fe-14d4-42a7-bb49-16ce4e8877a4/pdf` → `200 application/pdf` ✅
- Email delivery mailbox confirmation: not provable from this environment; not claimed.

## Console / Network Results
- Smoke validation found only benign warnings (`ERR_ABORTED` for Cloudflare RUM, usage tracking, Sentry).
- No fatal console/runtime/network issue blocked rendered workflows.

## Accepted-Risk Register Preservation
- Preserved at `/app/memory/WP17F_ACCEPTED_RISK_REGISTER.md`.
- This register keeps the `15` Category 2 record-dependent routes explicitly unproven in Preview and the `5` `/_internal/*` routes explicitly restricted.

## Accepted-Risk Routes Validated With Legitimate Records
- No Category 2 route moved out of accepted risk during this promotion pass.
- Legitimate fixture-backed shared records were revalidated only for release-smoke support surfaces (daily report, safety training, safety issuance) and did not alter the accepted-risk denominator.

## Failures and Disposition
- No new production-readiness failure was detected.
- Backend smoke helper initially exercised an outdated field-leadership path for the safety issuance evidence lane; exact release evidence was revalidated directly against `/api/safety-forms/equipment-issuances/:id` and `/pdf`, both returning `200`.

## Final Production Status
- Executive decision preserved: **GO WITH ACCEPTED RISKS**
- Production interpretation: ready for controlled promotion with the accepted-risk register preserved and no fake PASS applied to record-dependent routes.