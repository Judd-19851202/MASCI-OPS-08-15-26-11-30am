// lib/attemptSsoUpgrade.js — TRACK 23.9A.
//
// After a per-portal login succeeds (HR / PM / Shop / Safety /
// Dispatch / Field Leadership / Admin), silently call the master
// multi-login endpoint with the same credentials. If they also
// authenticate as a directory user, fan out the full master session
// envelope (session_token + every portal_tokens[] the user is
// granted + user.portals[]) so cross-portal navigation just works.
//
// If the email is not a directory user (legacy portal-only account),
// or multi-login declines the credentials for any other reason, this
// helper silently no-ops — the per-portal login already succeeded on
// its own, so nothing regresses.
//
// This closes the operator-reported gap where logging in via
// /hr/login left the master directory session empty, so navigating
// to /pm bounced to /pm/login even for a user granted both portals.
//
// The helper NEVER throws. Any error is logged and swallowed so the
// original per-portal login remains the source of truth for its own
// success/failure state.

import { applyMultiLoginResponse } from "./directoryAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Attempt an SSO upgrade of the current session by calling
 * /api/auth/multi-login with the credentials that just succeeded
 * on a per-portal endpoint.
 *
 * @param {string} email
 * @param {string} password
 * @param {boolean} rememberMe
 * @returns {Promise<{ok:boolean, sso:boolean, portals?:string[]}>}
 */
export async function attemptSsoUpgrade(email, password, rememberMe = true) {
  if (!email || !password) return { ok: false, sso: false };
  try {
    const r = await fetch(`${API}/auth/multi-login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!r.ok) return { ok: false, sso: false };
    const body = await r.json();
    if (!body?.ok) return { ok: false, sso: false };
    // MFA-gated users must complete MFA via /sign-in; we do NOT
    // bypass MFA here. Skip the upgrade.
    if (body.mfa_required) return { ok: true, sso: false, mfa: true };
    // Must-change-password path — no portal tokens issued. Skip.
    if (body.must_change_password) return { ok: true, sso: false, must_change: true };
    // Apply the full master envelope. `applyMultiLoginResponse`
    // preserves the existing per-portal setter contract, so any
    // token already stored is simply refreshed to the deterministic
    // value the master session would have minted.
    applyMultiLoginResponse(body, rememberMe);
    return {
      ok: true,
      sso: true,
      portals: body?.user?.portals || [],
    };
  } catch (e) {
    // Silent fallthrough — the per-portal login already succeeded,
    // so this upgrade attempt is best-effort only.
    console.debug("[attemptSsoUpgrade] silent fallback:", e?.message || e);
    return { ok: false, sso: false };
  }
}
