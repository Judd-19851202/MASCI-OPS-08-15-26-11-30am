# WP-18DB Health Probe Contract

## Public probe surface

- `GET /api/health`
- `GET /api/healthz`
- `GET /api/ready`
- `GET /api/health/full`

## Current preview runtime evidence

- Public preview smoke checks returned `200` during active certification.
- Runtime-health admin evidence shows:
  - liveness: `ok / alive`
  - readiness: `ok / ready`
  - readiness reason: `startup_complete`
- Backend logs show repeated successful probe responses on the local supervisor path during the certification window.

## Current production read-only evidence

- `https://mascidocs.com/api/health` returned `200`
- Production public health payload confirmed runtime identity verification.

## Contract expectations preserved in WP-18DB

- Liveness must indicate process survival.
- Readiness must not advertise ready state before startup completes.
- Deep/expanded health surfaces remain available for governed diagnostics.
- Probe truth is separated from backup/recovery certification truth.

## Known operational caution

- Preview ingress occasionally exhibited transient 502/timeout behavior during earlier package work and during hot reload windows.
- This package treats those as transport-path observations and does not confuse them with backend liveness/readiness when server logs and admin runtime truth remain green.

## Conclusion

The probe contract remains valid and evidenced in preview runtime and production public read-only checks.