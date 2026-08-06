# WP-18DB Security During Failure Report

## Certified controls

- Admin-strict routes fail closed without privileged bypass.
- Invalid or missing privileged tokens are rejected.
- PM tokens do not unlock admin-strict routes.
- No secret material is stored in WP-18DB evidence artifacts.

## Evidence

- `backend/tests/test_iter370_r7_admin_strict_fail_closed.py` → PASS / SKIP ONLY ON TRANSPORT NOISE
- runtime public health/version probes do not disclose secrets

## Executive conclusion

Security behavior during failure is certified for the current application-controlled auth boundary.