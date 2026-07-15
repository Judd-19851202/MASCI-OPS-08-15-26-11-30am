# DR-03 Governed Production Certification Lane

Status: IMPLEMENTATION READY FOR INDEPENDENT CERTIFICATION

## Purpose
- Create a production-safe Daily Report certification lane that uses the real write path while keeping operational surfaces clean.
- Preserve Trust Spine, audit, ODS, PDF, and evidence retention.
- Route certification fan-out only to controlled certification recipients.

## Canonical lane controls
- **Controlled certification project:** `ZZ-RUNTIME-CERT-2026`
- **Controlled certification project name:** `Runtime Certification — Internal Test Project`
- **Controlled certification identity family:** `cert.*` users, including `cert.foreman@example.com`
- **Controlled PM route:** `cert.pm@example.com`
- **Controlled Co-PM route:** `cert.copm@example.com`

## Backend implementation
- New helper: `backend/lib/governed_certification_lane.py`
- Daily Report submit path now auto-classifies the lane when both conditions are true:
  - project matches the governed certification project
  - submitter identity is a controlled certification identity
- On match, the backend now stamps:
  - `certification_record=true`
  - `synthetic_record=true`
  - `hidden_from_operations=true`
  - governed routing override (`cert.pm@example.com` + `cert.copm@example.com`)
  - governed lane evidence payload under `certification_lane`
  - release source hash when absent
- Existing generic certification behavior remains intact for non-governed certification rows.

## Downstream behavior preserved
- **Trust Spine:** preserved through the normal Daily Report write path
- **Audit:** preserved by canonical stored report + lane evidence payload
- **ODS:** preserved because the report still persists through the canonical handler
- **Search:** hidden from operational surfaces via certification/synthetic markers
- **PDF:** preserved because canonical report persistence and viewer routes are unchanged
- **Evidence preservation:** lane metadata now records identity verification, project snapshot, routing override, and preservation intent

## Controlled routing behavior
- Governed lane Daily Reports no longer fall into the generic certification email suppression branch.
- Instead, they use a controlled routing override:
  - To: `cert.pm@example.com`
  - CC: `cert.copm@example.com`
- Generic certification rows outside the governed lane remain email-suppressed.

## Live preview-safe proof executed
- FL login with `cert.foreman@example.com` succeeded.
- POST to `/api/daily-reports` with project `ZZ-RUNTIME-CERT-2026` succeeded.
- Response proved:
  - `certification_record=true`
  - `email_dispatch_suppressed=false`
  - governed `routing_override` populated
  - `certification_lane` evidence payload populated

## Regression protection
- `backend/tests/test_dr03_governed_certification_lane.py`
- Existing closeout/static certification suites retained
- Build remains clean: `cd /app/frontend && CI=true yarn build` → PASS

## Non-claims
- No production deployment performed
- No GitHub push performed
- No physical iPad execution claimed here