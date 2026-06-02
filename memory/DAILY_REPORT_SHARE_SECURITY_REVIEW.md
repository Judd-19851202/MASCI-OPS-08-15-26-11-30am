# DAILY REPORT SHARE EMAIL · SECURITY REVIEW

**Date**: 2026-06-02
**Companion**: `DAILY_REPORT_SHARE_FORENSIC_AUDIT.md`, `SHARED_LINK_PERMISSION_MATRIX.md`, `DEPLOYMENT_IMPACT_ASSESSMENT.md`.
**Mode**: READ-ONLY.

---

## 1 · Findings (7 governance concerns)

All seven concerns are on the **Field Revision `/revise/{token}` adjacent feature** (iter452.5 Tier 1), NOT on the Share Email Dialog itself. The Share Email Dialog is structurally safe (§2 below).

### GC-1 · `/revise/{token}` is anonymous, token-only auth

* Source: `backend/routes/field_revision.py:71-177`.
* The handler trusts the JWT signature exclusively. No portal session is consulted. POST writes to the underlying record's `field_submitter_revisions[]` succeed in incognito, logged-out, different-device, or different-user scenarios.
* **Severity**: 🟡 MEDIUM. By-design for the iter452.5 "Tier 1 in-the-field correction" use case, but the lack of human-session re-check is a deliberate trade-off that the operator should ratify.

### GC-2 · 7-day TTL with no single-use enforcement

* Source: `lib/field_submitter_identity.py:96-100` (`FIELD_REVISION_LINK_TTL_HOURS` default 168) and `lib/field_submitter_identity.py:417-419` (expiry check).
* The token is reusable as many times as the holder wants within the 7-day window. Every POST appends a NEW `revision_saved` audit row (no idempotency).
* **Severity**: 🟡 MEDIUM. Multiple replays are detectable in the audit chain BUT not blocked.

### GC-3 · Audit attribution misrepresents the actor

* Source: `backend/routes/field_revision.py:148-156` and `lib/field_submitter_identity.py:471-475`.
* The `revision_saved` chain event records `actor = {_actor: "field_submitter", name: <binding.submitter_name>, email: <binding.submitter_email_at_submit>}` — i.e., the ORIGINAL submitter, regardless of who actually held the link at POST time.
* The IP address IS captured (`extra.ip`), but it is buried inside the revision document, not surfaced as a primary actor field.
* **Severity**: 🟡 MEDIUM. Forensic chain is recoverable from `ip + binding_id + ladder_tier` triangulation but is not immediately obvious to a non-forensic reviewer.

### GC-4 · Email recipient is NOT necessarily the report owner

* Source: `lib/field_submitter_identity.py:541-555` (5-tier ladder resolution: `fl → employee → per_submit → pm_relay → dead_letter`).
* If tiers 1-3 fail, the link goes to the **PM** (relay tier) or **safety admin / dead-letter** address — neither of whom is the original report submitter. They are explicitly told to "forward this link to them so they can apply the correction" (`pm_relay` banner, line 605-611).
* Forwarding the email exposes the tokenized URL to everyone in the forwarding chain. The token does not regenerate on forward.
* **Severity**: 🟡 MEDIUM. Operationally intended; documented in `lib/field_submitter_identity.py:533-535`.

### GC-5 · No revocation / rotation API

* No endpoint exists to invalidate or rotate an outstanding `/revise/{token}`. The only mitigations available today are:
  1. Wait for the 7-day TTL to expire.
  2. Rotate `FIELD_REVISION_JWT_SECRET` (invalidates ALL outstanding tokens for ALL records).
  3. Manually delete the binding from `db.field_submitter_bindings` — but `verify_revision_token` does NOT check binding presence at signature time, only at handler time, so a fresh binding-not-found 404 would still leak that the token format was valid.
* **Severity**: 🟢 LOW. Acceptable when paired with the 7-day TTL ceiling.

### GC-6 · Dev-fallback JWT secret if all env vars unset

* Source: `lib/field_submitter_identity.py:90-93` — if `FIELD_REVISION_JWT_SECRET`, `JWT_SECRET`, and `ADMIN_HMAC_SECRET` are ALL absent, the signer falls back to the literal string `"iter452_5_dev_only_secret_DO_NOT_USE_IN_PROD"`. This is published in the source code.
* **Preview env state (verified)**: `JWT_SECRET` is set → fallback is NOT used in preview.
* **Production env state**: not directly inspected. Standing doctrine in `test_credentials.md` requires `ADMIN_HMAC_SECRET` to be set; assuming policy is honoured, the fallback is not in use.
* **Severity**: 🟢 LOW — contingent on `JWT_SECRET` OR `ADMIN_HMAC_SECRET` being set in production (it MUST be per existing security doctrine). The fallback string itself is a code-smell that should be removed in a future hardening iter.

### GC-7 · `changes` payload has no schema validation

* Source: `backend/routes/field_revision.py:55-58` — `RevisionPayload.changes: Dict[str, Any] = Field(default_factory=dict)`.
* An attacker holding a valid token can push arbitrary key/value pairs into the array. Mongo's 16 MB document limit is the only hard ceiling.
* The `field_submitter_revisions[]` array is NEVER read back into the canonical record fields, so the impact is limited to audit-log bloat / chain noise, not record corruption.
* **Severity**: 🟢 LOW — read-only on canonical fields. Audit-bloat DoS would require thousands of POSTs.

---

## 2 · Why the Share Email Dialog itself is NOT a concern

Verified by direct code inspection:

1. `backend/server.py:11522-11593` (`POST /api/email-report`) — body is gated by `Depends(require_admin)`. Anonymous POSTs are rejected at the auth boundary. **The operator must already be a privileged user to even invoke this endpoint.**
2. `backend/pdf_render.py::render_email_html` (lines 1456-1528) — the HTML body contains **zero** `<a href>` elements. `grep -n "href\|<a " backend/pdf_render.py` returns 0 matches.
3. The PDF attachment, rendered via WeasyPrint from the same module, is **static** — no clickable hyperlinks.
4. The email's only "URL-shaped" text is the literal string `mascidocs.com` rendered as plain text inside a `<div>`. Most email clients will auto-linkify this to the site root, NOT to any deep-link record URL. Clicking would land the recipient at the site root, where standard portal gates apply (`RequireAdmin` / `RequirePm` / etc.).
5. The frontend dialog (`EmailReportDialog.jsx`) labels the action explicitly: "Generates a polished PDF and emails it" — no false suggestion that a live-link is being shared.

**Conclusion**: the Share Email Dialog is **🟢 EXPECTED BEHAVIOUR**. No security issue.

---

## 3 · Why the live-page edit affordance is NOT a defect

The Superintendent's perceived ability to "edit from the email" is most plausibly explained by the `EditProjectDialog` rendered unconditionally on `ViewDailyReport.jsx` (line 203). This button:

1. Is visible only when the user is already inside the protected `/admin/daily/{id}` or `/pm/daily/{id}` route (gated by `RequireAdminOrPm`).
2. Edits only **project_name / project_number / project_id / location** — a deliberate "re-tag the project" affordance for when a foreman picked the wrong job at submit time. Narrative, signatures, photos, time, weather, crew counts, audit envelope hash — all immutable.
3. Calls `PATCH /api/admin/records/daily-reports/{id}/project`, which requires the same admin/PM token. The token comes from the user's **browser session**, NOT from any email content.

The email did not grant this access. The Superintendent's existing session did. This is **by-design** workflow correctness, not a defect.

---

## 4 · Aggregate verdict

| Surface | Verdict |
|---|---|
| Daily Report Share Email Dialog | 🟢 EXPECTED BEHAVIOUR |
| `/revise/{token}` Field Revision (adjacent feature) | 🟡 7 GOVERNANCE CONCERNS (2 MED · 4 LOW · 1 LOW-contingent) — by-design trade-offs, no defects |
| Live ViewDailyReport `EditProjectDialog` | 🟢 EXPECTED BEHAVIOUR (project re-tag only · canonical fields immutable) |
| **Cumulative** | 🟡 **GOVERNANCE CONCERN** (not a defect) |

No 🔴 SECURITY / WORKFLOW INTEGRITY DEFECT was identified. Deployment is not blocked by this audit. Recommendations to harden the `/revise/{token}` surface are listed in §5 below for a future operator-authorized iter (NOT in scope of this read-only audit).

---

## 5 · Hardening recommendations (NOT actioned · future iter)

1. **GC-1**: Add an opt-in "require matching session" mode for `/revise/{token}` POSTs (toggled per-workflow via env). Default OFF to preserve current Tier 1 behaviour.
2. **GC-2**: Add single-use enforcement — first successful POST stamps the binding with `revision_link_consumed_first_at` and rejects subsequent POSTs with 409 until a new link is minted.
3. **GC-3**: Surface the actual revising IP / user-agent as a primary `actor.identity_source` field on the `revision_saved` chain event (not just buried in `extra.ip`).
4. **GC-5**: Add `POST /api/admin/revise/{rid}/revoke` (admin-strict) that bumps the binding's `revision_link_revoked_at` field; `verify_revision_token` would check this before returning OK.
5. **GC-6**: Remove the literal dev-fallback string from `_jwt_secret()` and raise `RuntimeError("FIELD_REVISION_JWT_SECRET / JWT_SECRET / ADMIN_HMAC_SECRET must be set")` at startup if all three are absent.
6. **GC-7**: Tighten `RevisionPayload.changes` to a known whitelist of field keys + bounded value lengths.
7. **General**: Add an in-email banner reminding the recipient "This link grants edit access — do not forward."
