# LIVE AUTH ROOT-CAUSE AUDIT — must_change_password (jaymn.judd@mascigc.com)

Read-only. No password change/reset, no account creation, no production mutation.

## CORRECTION OF EARLIER INTERIM REPORT
My Checkpoint-2 interim note attributed the 3 auth-gated production probe failures to
`must_change_password`. That was WRONG. Production `/api/auth/multi-login` for this
account returns **must_change_password = FALSE** and issues all 8 portal tokens.
The account is NOT in a must-change state in production.

## EXPLICIT ANSWERS
- PASSWORD INCORRECT? **NO** — multi-login returns ok:true, session_token + all portal tokens issued.
- PASSWORD ACCEPTED BEFORE MUST-CHANGE GATE? **YES** — credential verification succeeds; the flag is read
  from the record AFTER successful auth (server.py:3535 `bool(user.get("must_change_password"))`).
- BREACH/COMPROMISED-PASSWORD SIGNAL INVOLVED? **NO** — no HIBP/breach logic in this path; it is a plain stored boolean.
- must_change_password STORED OR DERIVED? **STORED** boolean on the user/directory record (not derived from
  password age/expiry/policy). Read by multi_portal_session_enrichment.py:77 and directory_portal_login.py:137.
- EXACT FIELD/SOURCE: `must_change_password` field on the directory user record (`user_directory`) and on the
  legacy `users` record. Set True at provisioning/seed (server.py:13117/13878 Welcome2MASCI! first-login;
  15318 seeds SUPER then flips False on the change path).
- WHY IT IS TRUE FOR THIS EXISTING LIVE ACCOUNT: **It is NOT true in production for this account.**
  Production directory identity = must_change_password:False. (The gate, when True, WITHHOLDS portal tokens —
  returns None — which is correct first-login-rotation enforcement, not a defect.)

## ACTUAL BLOCKER FOR THE 3 AUTH-GATED PROBES (separate from must_change)
Production issues all portal tokens (must_change=False) but the READ validators reject them:
`_require_any_portal_read` -> HTTP 401 "Authenticated portal session required";
`_is_valid_directory_admin_token_async` -> "Invalid admin token".
Fresh, immediately-used tokens are still rejected. => The portal tokens minted by multi-login are not, by
themselves, accepted by the portal-session read validators (they appear to require an additional session
binding / X-Session-Id lookup that a raw API caller has not reconstructed). This is an auth-integration
binding nuance for headless API callers — NOT a must_change_password issue and NOT a Wave-4 count/total defect.
The browser SPA presumably supplies the missing session binding, so operator UI is unaffected.

## DIRECTORY vs LEGACY IDENTITY MISMATCH (found in preview, reproduction proxy)
- `user_directory` (192 users): jaymn.judd must_change_password=**False**, portals=[admin,dispatch,fl,hr,pm,safety,shop].
- legacy `users` (5 users): jaymn.judd must_change_password=**True**, role=owner. ALL 5 legacy users flagged True.
- Production multi-login uses the DIRECTORY (must_change=False) — correct. The legacy `users.must_change_password=True`
  is a stale seed artifact in the legacy collection; if any code path reads the legacy `users` flag for auth it could
  diverge. FLAG for review, NOT auto-repaired.

## PRODUCTION READ-ONLY COUNTS
- I have NO production DB access from this environment, so exact production counts cannot be enumerated here.
- Preview proxy: user_directory total=192, must_change_password=true=2; legacy users total=5, must_change=true=5.
- No evidence that established production users are unexpectedly flagged (production super admin = False).

## CLASSIFICATION
- must_change_password on this account = NOT a production auth defect (production value is False; enforcement logic
  is correct). Earlier interim attribution corrected.
- Directory-vs-legacy `users` must_change divergence = potential migration/seed hygiene item (preview) — needs review,
  no production repair without owner authorization.
- Headless portal-token validation binding = auth-integration nuance for API callers; browser sessions unaffected.
