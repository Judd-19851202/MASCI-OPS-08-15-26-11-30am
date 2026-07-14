# AI Architecture Lock

Date: 2026-07-14
Track: DR-02

## Verified current AI paths

### Path A · Active assist path
- `DailySummaryAssist.jsx`
- pre-saves evidence bundle to `/api/dr-v2/drafts`
- calls `/api/dr-v2/ai/synthesize`
- freezes accepted result into `ai_accepted_summary` + `ai_accepted_summary_meta` inside the Daily Report submit payload

Evidence:
- `frontend/src/components/daily-report/DailySummaryAssist.jsx:177-183,257-280`
- `frontend/src/pages/NewDailyReport.jsx:2998-3004`
- `frontend/src/pages/NewDailyReportV3.jsx:795-796`

### Path B · Additive deterministic summary path
- `/api/daily-reports/summary/draft`
- `/api/daily-reports/{report_id}/summary/accept`
- writes `daily_operational_summary*` onto submitted Daily Reports

Evidence:
- `backend/routes/daily_summary.py:295-445`

## Architecture violation
Two summary systems exist. This violates **Simple**, **Trusted**, **Deployable**, and **Relentless Ownership**.

## Canonical lock
- Daily Report shall have **one accepted-summary architecture**.
- The accepted summary that gates submit, feeds PDF, feeds ODS, and feeds downstream intelligence must be the same canonical field family.
- AI remains assistive only:
  - operator is source of truth
  - no factual overwrite
  - provenance and confidence retained
  - provider/model names masked from operator-facing surfaces
  - fallback behavior honest

## Canonical recommendation
- Retain the field family already enforced by submit validation and downstream consumers (`ai_accepted_summary` + `ai_accepted_summary_meta`) as the canonical Daily Report summary contract.
- Reclassify any alternate summary field family as non-canonical for Daily Report unless explicitly remapped into the same contract.

## AI boundaries
- Equipment detection is suggestion-only and must never mutate Daily Report autonomously.
- Photo intelligence may enrich evidence, but must remain grounded.
- Accepted summary cannot override typed facts.
