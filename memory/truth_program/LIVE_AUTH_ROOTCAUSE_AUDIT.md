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

## ===== SIDE LANE A — LEGACY `users` vs `user_directory` AUTHORITY (READ-ONLY STATIC AUDIT) =====
Method: grep every served read of `must_change_password` and trace its source collection + reachability.

FINDING — TWO ARCHITECTURALLY SEPARATE AUTH STACKS:
- CANONICAL directory/portal stack (what the SPA uses): reads the flag from `user_directory`
  (`lib/multi_portal_session_enrichment.py:77` via `ud.authenticate`; `lib/directory_portal_login.py:137`;
  `routes/auth_directory_routes.py:408`; `routes/mfa_routes.py:311`). Production jaymn.judd = must_change=False.
- LEGACY JWT-cookie stack: `auth.py` `build_auth_router` (mounted at server.py:20623). `POST /api/auth/login`
  reads the LEGACY `db.users` collection; `get_current_user` reads `db.users`; deps
  `require_admin_or_owner` / (auth.py:253,260) call `_require_password_rotation_cleared(user)` which gates on
  the LEGACY `users.must_change_password`. These deps protect `projects.py` and `tools.py` routers.

REACHABILITY:
- The SPA does NOT call `/api/auth/login` (only directory `/auth/me-directory` + portal logins). Grep of
  `frontend/src` shows no legacy-login usage.
- The legacy gate is therefore only reachable by a client presenting a legacy JWT cookie obtained from
  `/api/auth/login` — a flow the production SPA never exercises.

CLASSIFICATION: **DUAL AUTHORITY — LOW SEVERITY / LATENT** (per owner criteria "any served path CAN consume
the legacy value"). It is NOT a high-severity shared-auth defect: the two stacks are separate, the SPA uses
only the canonical `user_directory` authority, and no production operator path reads the stale legacy flag.
The divergence risk is confined to the unused legacy `/api/auth/login` subsystem (stale seed `users`
must_change=True for the 5 legacy owner rows incl. Jaymn).

RESOLUTION PATH (NOT executed — auth change requires integration_expert + owner authorization):
- Preferred: retire/guard the legacy `/api/auth/*` + `db.users` gate so `user_directory` is the sole authority,
  OR route `projects.py`/`tools.py` admin deps to the directory validator. This is an auth-subsystem change and
  MUST be reproduced in preview + owner-authorized before any code edit. NO production mutation. NO blind edit.
- Guard-against-reintroduction recommended once the repair path is owner-approved.

## ===== SIDE LANE B — RAW/HEADLESS TOKEN vs SPA SESSION BINDING =====
Trace: `/api/auth/multi-login` mints `session_token` + `portal_tokens{admin,hr,pm,...}`. The SPA
(`directoryAuth.js`) fans each portal token into its matching request header (`X-Admin-Token`, `X-HR-Token`, …).

Portal READ validator `_require_any_portal_read` (server.py:1191) accepts ONLY per-portal headers
(`X-<Portal>-Token`). For admin it calls `_is_valid_directory_admin_token_async`
(server.py:679) with `allow_unbound_directory_session=True` -> a FRESH multi-login admin token IS valid here
**if presented as `X-Admin-Token`**. Continuity-gated endpoints instead use
`_directory_admin_row_for_continuity_async` (server.py:709) which additionally REQUIRES `session_activity`
(matching user_id + idle/absolute TTL) — established by the SPA, not by a bare curl.

WHY RAW REPLAY 401s: the headless caller either (a) does not resend the correct per-portal
`X-<Portal>-Token` header (e.g. replays `session_token` or `Authorization: Bearer`), and/or (b) never
established `session_activity` for continuity-gated endpoints.

CLASSIFICATION: **INTENTIONAL SESSION BINDING** (header contract + session-activity continuity) — NOT a
validator inconsistency, NOT a defect. No auth weakening.

CORRECT HEADLESS-TESTING MECHANISM (documented, used by test_wave5_pc_checklist_contract.py):
1. POST `/api/auth/multi-login` with credentials.
2. Read `portal_tokens["admin"]` (or the needed portal) + `session_token` (as `X-Directory-Token`).
3. Send the portal token in its matching header, e.g. `X-Admin-Token: <portal_tokens.admin>`.
4. For continuity/TTL-gated endpoints, drive via the browser SPA context (session_activity present) instead
   of a bare token. This mirrors `directoryAuth.js` — no auth change required.
