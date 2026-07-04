# Permission Census

- **Portal tokens:** 7 (admin · pm · hr · safety · shop · dispatch · field_leadership).
- **Auth-gate call sites:** 355 across backend.
- **Gate functions:** 6 canonical — `require_admin`, `require_admin_pm_or_hr_read`, `require_safety_or_admin`, `require_pm_or_admin`, `require_dev`, `is_valid_pm_user_token_async` / `is_valid_hr_user_token_async` / `is_valid_directory_admin_token_async`.

## Classification
- **KEEP** — all 355 call sites (Track 15.87 multi-portal access authority green).
- **FIX post-deploy** — `require_admin_pm_or_hr_read` still uses retired sync-HMAC for admin path; Track 21.x updates it to accept directory-admin async tokens (see Track 20.6B TD-20.7-C01 fix report).
- **MERGE / RETIRE / DELETE** — 0.

Zero permission widening in any of Tracks 20.6B, 20.7, 20.8, 20.9, 21.0.
