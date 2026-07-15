# DR-03 Final Closeout Repair

Status: IMPLEMENTATION READY FOR INDEPENDENT CERTIFICATION

## Scope closed in this repair pass
- Governed Production Certification Lane built for Daily Reports
- Intermittent `/api/draft-telemetry` 422 eliminated for valid long scoped form keys
- HR / Shop / Safety intelligence timeout UX hardened
- DR-03 evidence package updated

## Exact repairs
### 1) Governed Production Certification Lane
- Added canonical governed lane helper: `backend/lib/governed_certification_lane.py`
- Daily Report submit path now auto-classifies certification submissions for the controlled project + controlled identity pair
- Controlled routing override now routes Daily Report fan-out to certification recipients only
- Generic certification rows still remain suppressed outside this governed lane

### 2) Draft telemetry 422
- Exact mismatch repaired: frontend emitted long scoped `formKey` values while backend still enforced the old 64-char limit
- Backend contract widened to `FORM_KEY_MAX_LENGTH=180`
- Frontend canonical payload now sanitizes and bounds overlong form keys deterministically
- Pagehide/keepalive telemetry flush now works even without a portal token

### 3) HR / Shop / Safety timeout hardening
- Shop intelligence now surfaces truthful timeout copy + retry
- Safety KPI card and trench intelligence card now surface truthful timeout copy + retry
- HR intelligence strip remains calm and retryable without request storms; memoized dependencies were stabilized

## Verification executed
- Backend targeted pytest: PASS
- Frontend targeted Jest: PASS
- Frontend timeout regression Jest: PASS
- Frontend production-equivalent build: PASS
- Live preview-safe telemetry POST with long scoped form key: PASS (`200`)
- Live preview-safe governed certification Daily Report submit: PASS (`200`)

## Remaining manual work
- Independent full preview/browser certification still required
- Cross-platform manual/agent regression still required
- Physical iPad/Safari execution still required and not claimed