# WP15 Security Negative Path Report

Last updated: 2026-07-29
Status: Partial verification complete

## Verified Negative Paths
- Incorrect PM password → `401`
- Disabled directory identity fixture → `401`
- PM portal token + mismatched directory session → `401`
- PM portal token + missing directory session → `401`

## Verified Positive Control
- PM portal token + matching directory session → `200`

## Gaps Remaining
- explicit session-expiry fixture verification
- lockout/unlock lifecycle verification
- password-reset lifecycle verification
- active-session authority revocation checks
- emergency override negative-path checks

## Current Determination
Negative-path hardening is improved and evidence-backed, but not yet complete enough for final GO certification.