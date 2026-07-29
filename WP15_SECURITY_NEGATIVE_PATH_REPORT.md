# WP15 Security Negative Path Report

Last updated: 2026-07-29
Status: Expanded evidence complete for closeout review

## Verified Negative Paths
- Incorrect PM password → `401`
- Disabled directory identity fixture → `401`
- Governed admin API with missing `X-Directory-Token` → denied (`401` in independent API verification)
- Governed admin API with mismatched `X-Directory-Token` → denied (`401` in independent API verification)
- PM portal token + mismatched directory session → `401`
- PM portal token + missing directory session → `401`
- Explicit expired directory session fixture on governed admin API → `200` before expiry, `401` after expiry mutation
- Session-timeout middleware fail-closed contract verified in pytest (`35 passed` focused suite including middleware + recovery checks)

## Verified Positive Controls
- Governed admin API with valid admin token + matching directory token → `200`
- PM governed workflow with valid lifecycle headers → `200`
- Safety and Dispatch representative protected reads → `200`
- PM portal token + matching directory session → `200`

## Lockout / Recovery Evidence
- Lockout configuration and helper contract validated in `test_track14_auth_password_parity.py`.
- Session recovery / scoped 401 cleanup contract validated in `test_track_15_13e_production_auth_session_recovery.py`.
- Live brute-force unlock cycling was **not** exercised in this run to avoid intentionally self-locking the preview ingress IP.
- End-to-end password-reset email redemption was **not** exercised in this run.

## Current Determination
- Request-lifecycle negative-path hardening is evidence-backed and functioning.
- Residual security evidence is now **P1 completeness work**, not the primary blocker for final constitutional certification.