// SignIn.jsx — Master multi-portal sign-in page (iter82)
//
// Single entry point at /sign-in for users who have access to MORE than
// one portal (Admin + PM + HR, etc.). They type email + master password
// once; the backend mints all eligible per-portal tokens and we fan
// them out via `applyMultiLoginResponse`. Lands the user on either
// their single portal (if they only have one) or the Hub (so they can
// pick).
//
// All existing per-portal login flows (/pm/login, /hr/login, /shop/login,
// /admin/login) keep working unchanged for single-portal users.

import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Loader2, ArrowLeft, Mail, KeyRound, ShieldCheck, Fingerprint } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { CanonicalHeader } from "@/components/CanonicalHeader";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { applyMultiLoginResponse, landingFor, stabilizeAdminPortalToken } from "@/lib/directoryAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearHrToken } from "@/lib/hrAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { setMustChange } from "@/lib/mustChangePassword";
import { passkeySupported, platformAuthenticatorAvailable, signInWithPasskey } from "@/lib/passkeys";
import { setPortalContext, setPortalContextForPath } from "@/lib/portalContext";
import { prepareFreshLoginSession } from "@/lib/sessionReset";
import { toast } from "sonner";

export default function SignIn() {
  const { t } = useT();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  // iter375 · MFA challenge state
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaChallenge, setMfaChallenge] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [mfaUseRecovery, setMfaUseRecovery] = useState(false);
  const [mfaUserName, setMfaUserName] = useState("");
  // iter422 · Phase 24 · Passkey availability (Face ID / Touch ID / Hello)
  const [passkeyReady, setPasskeyReady] = useState(false);
  const [passkeyBusy, setPasskeyBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (passkeySupported()) {
        const ok = await platformAuthenticatorAvailable();
        if (!cancelled) setPasskeyReady(!!ok);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const onPasskeySignIn = async () => {
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      toast.error(t("Enter your work email first"));
      return;
    }
    setPasskeyBusy(true);
    try {
      const data = await signInWithPasskey({ email: cleanEmail });
      if (data?.mfa_required) {
        setMfaChallenge(data.mfa_challenge_token || "");
        setMfaUserName(data?.user?.name || data?.user?.email || "");
        setMfaRequired(true);
        return;
      }
      if (data?.ok) {
        await prepareFreshLoginSession();
        applyMultiLoginResponse(data, rememberMe);
        await stabilizeAdminPortalToken(data, rememberMe);
        setPortalContextForPath(landingFor(data.user));
        // Track 15.14A Layer 1 — temp-password enforcement on passkey path.
        if (data.must_change_password) {
          setMustChange("directory", true);
          toast.info(t("Welcome — please choose a new password to continue"));
          navigate("/change-password", { replace: true });
          return;
        }
        toast.success(`${t("Welcome")} ${data?.user?.name || ""}`, { duration: 4000 });
        navigate(landingFor(data.user), { replace: true });
      } else {
        toast.error(t("Device sign-in failed"));
      }
    } catch (err) {
      // NotAllowedError = user cancelled or no matching passkey · stay calm
      const name = err?.name || "";
      const msg = err?.message || t("Device sign-in failed");
      if (name === "NotAllowedError" || /cancel/i.test(msg)) {
        // Silent — user cancelled
      } else {
        toast.error(msg, { duration: 5000 });
      }
    } finally {
      setPasskeyBusy(false);
    }
  };

  useEffect(() => {
    // Iter88 — Removed mount-time token wipe. See AdminLogin.jsx rationale.
    // The multi-login response below atomically sets all 4 portal tokens,
    // so there's no need to nuke prior state. Reaching /sign-in with a
    // live session is a no-op until the user submits a fresh password.
    try { setPortalContext("public"); } catch { /* noop */ }
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      toast.error(t("Enter your work email and master password"));
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post(
        "/auth/multi-login",
        { email: email.trim().toLowerCase(), password },
        { timeout: 90000 }
      );
      // iter375 · MFA gate — if super-admin has MFA enabled, swap to challenge UI
      if (res?.data?.ok && res.data.mfa_required) {
        setMfaChallenge(res.data.mfa_challenge_token || "");
        setMfaUserName(res.data?.user?.name || res.data?.user?.email || "");
        setMfaRequired(true);
        setSubmitting(false);
        return;
      }
      if (res?.data?.ok) {
        await prepareFreshLoginSession();
        applyMultiLoginResponse(res.data, rememberMe);
        await stabilizeAdminPortalToken(res.data, rememberMe);
        const user = res.data.user;
        const granted = Object.entries(res.data.portal_tokens || {})
          .filter(([, v]) => !!v)
          .map(([k]) => k);
        // Track 15.14A Layer 1 — temp-password enforcement. The
        // backend suppresses portal_tokens entirely when the directory
        // user still owes a password rotation. The SPA must NOT
        // proceed to landingFor() because no portal tokens exist;
        // we drop the user into the unified /change-password flow
        // (uses the session_token) and let them re-acquire the token
        // bundle after a successful rotation.
        if (res.data.must_change_password) {
          setMustChange("directory", true);
          toast.info(t("Welcome — please choose a new password to continue"));
          navigate("/change-password", { replace: true });
          return;
        }
        toast.success(
          `${t("Welcome")} ${user?.name || ""} · ${t("Signed in to")}: ${
            granted.length ? granted.map((p) => p.toUpperCase()).join(" · ") : "—"
          }`,
          { duration: 5000 }
        );
        setPortalContextForPath(landingFor(user));
        navigate(landingFor(user), { replace: true });
      } else {
        toast.error(t("Sign-in failed"));
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : status === 401
          ? t("Invalid email or password")
          : t("Sign-in failed — try again");
      toast.error(msg, { duration: 6000 });
    } finally {
      setSubmitting(false);
    }
  };

  // iter375 · Phase 4B — verify MFA challenge
  const onMfaSubmit = async (e) => {
    e.preventDefault();
    const code = (mfaCode || "").trim();
    if (!code) {
      toast.error(t(mfaUseRecovery ? "Enter a recovery code" : "Enter the 6-digit code"));
      return;
    }
    setSubmitting(true);
    try {
      const payload = mfaUseRecovery
        ? { challenge_token: mfaChallenge, recovery_code: code }
        : { challenge_token: mfaChallenge, code };
      const res = await api.post("/auth/mfa/verify-login", payload, { timeout: 30000 });
      if (res?.data?.ok) {
        await prepareFreshLoginSession();
        applyMultiLoginResponse(res.data, rememberMe);
        await stabilizeAdminPortalToken(res.data, rememberMe);
        setPortalContextForPath(landingFor(res.data.user));
        // Track 15.14A Layer 1 — temp-password enforcement on MFA path.
        if (res.data.must_change_password) {
          setMustChange("directory", true);
          toast.info(t("Welcome — please choose a new password to continue"));
          navigate("/change-password", { replace: true });
          return;
        }
        toast.success(`${t("Welcome")} ${res.data?.user?.name || ""}`, { duration: 4000 });
        navigate(landingFor(res.data.user), { replace: true });
      } else {
        toast.error(t("MFA verification failed"));
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const status = err?.response?.status;
      const msg =
        status === 423
          ? t("MFA locked due to repeated failures. Try again in a few minutes.")
          : typeof detail === "string"
          ? detail
          : t("Invalid MFA code");
      toast.error(msg, { duration: 6000 });
    } finally {
      setSubmitting(false);
    }
  };

  const cancelMfaChallenge = () => {
    setMfaRequired(false);
    setMfaChallenge("");
    setMfaCode("");
    setMfaUseRecovery(false);
    setMfaUserName("");
  };

  return (
    <div className="wp17-public-shell flex min-h-screen flex-col">
      <div className="caution-stripe" />
      <CanonicalHeader
        portalLabel={t("MASCI Operations Platform")}
        pageLabel={t("Shared sign-in")}
        accent="red"
        backTo="/"
        backLabel={t("Home")}
        homeTo="/"
        showHomeLink={false}
        showLangToggle
        containerClassName="max-w-6xl"
        testIdPrefix="sign-in"
      />

      <main className="wp17-public-main flex-1 flex items-center justify-center py-12">
        <div className="w-full wp17-public-grid items-stretch">
          <section className="wp17-public-hero" data-testid="sign-in-entry-architecture">
            <div>
              <div className="wp17-kicker">Shared experience foundation</div>
              <h1 className="mt-3 font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-950">
                {t("One entry. The right workspace. The next safe step.")}
              </h1>
              <p className="mt-4 max-w-2xl text-sm sm:text-base text-slate-700 leading-relaxed">
                {t("Use the shared sign-in when your account works across multiple workspaces. If you only use one workspace, the direct links stay available below.")}
              </p>
            </div>
            <div className="space-y-4 mt-8">
              <div className="wp17-panel bg-white/70">
                <div className="wp17-kicker">What happens here</div>
                <div className="mt-2 wp17-panel-title">Clear routing, no guessing</div>
                <ul className="mt-3 space-y-2 text-sm text-slate-700" data-testid="sign-in-guidance-list">
                  <li>• {t("Sign in once for shared access across Admin, PM, HR, Shop, Safety, Dispatch, and Leadership.")}</li>
                  <li>• {t("Return to the right workspace automatically after authentication.")}</li>
                  <li>• {t("Keep direct workspace links for single-workspace operators.")}</li>
                </ul>
              </div>
              <div className="wp17-panel bg-white/70">
                <div className="wp17-kicker">Next actions</div>
                <div className="mt-2 wp17-chip-row">
                  <span className="wp17-chip !bg-slate-900 !text-white !border-slate-900/20" data-testid="sign-in-next-auth-chip">{t("Authenticate")}</span>
                  <span className="wp17-chip !bg-white !text-slate-900 !border-slate-200" data-testid="sign-in-next-route-chip">{t("Route to workspace")}</span>
                  <span className="wp17-chip !bg-white !text-slate-900 !border-slate-200" data-testid="sign-in-next-help-chip">{t("Open direct portal if needed")}</span>
                </div>
              </div>
            </div>
          </section>

          <div className="wp17-public-card w-full max-w-none p-7 sm:p-9">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700">
                {t("Operations Platform")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-2 mb-6">
            {t("Multi-workspace sign-in for accounts with access to more than one workspace. Single-workspace employees, use your workspace's direct sign-in page (linked below).")}
          </p>

          {/* iter375 · MFA challenge UI — replaces the password form when a super-admin needs a TOTP code */}
          {mfaRequired ? (
            <form onSubmit={onMfaSubmit} className="space-y-4" data-testid="mfa-challenge-form">
              <div className="rounded-md border-2 border-red-700 bg-red-50 px-4 py-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-800 font-bold">
                  {t("Multi-Factor Authentication Required")}
                </div>
                <div className="text-sm text-slate-700 mt-1">
                  {mfaUserName ? `${mfaUserName} · ` : ""}
                  {mfaUseRecovery
                    ? t("Enter one of your recovery codes.")
                    : t("Open your authenticator app and enter the 6-digit code.")}
                </div>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                  {mfaUseRecovery ? t("Recovery Code") : t("Authenticator Code")}
                </Label>
                <Input
                  type="text"
                  inputMode={mfaUseRecovery ? "text" : "numeric"}
                  value={mfaCode}
                  onChange={(e) => setMfaCode(mfaUseRecovery ? e.target.value.toUpperCase() : e.target.value)}
                  autoFocus
                  autoComplete="one-time-code"
                  placeholder={mfaUseRecovery ? "XXXX-XXXX-XX" : "123456"}
                  maxLength={mfaUseRecovery ? 12 : 6}
                  className="mt-2 h-12 text-lg font-mono tracking-widest text-center border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
                  data-testid="mfa-code-input"
                />
              </div>
              <button
                type="button"
                onClick={() => { setMfaUseRecovery((v) => !v); setMfaCode(""); }}
                className="inline-flex items-center min-h-[44px] px-1 -mx-1 text-xs font-mono uppercase tracking-wide text-red-700 hover:text-red-900 font-bold"
                data-testid="mfa-toggle-recovery"
              >
                {mfaUseRecovery
                  ? t("Use authenticator code instead")
                  : t("Use a recovery code")}
              </button>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={cancelMfaChallenge}
                  className="flex-1 h-12 font-mono uppercase tracking-wide font-bold"
                  data-testid="mfa-cancel-btn"
                >
                  {t("Cancel")}
                </Button>
                <Button
                  type="submit"
                  disabled={submitting || !mfaCode}
                  className="flex-1 h-12 bg-red-700 hover:bg-red-800 font-mono uppercase tracking-wide font-bold"
                  data-testid="mfa-verify-btn"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : t("Verify")}
                </Button>
              </div>
            </form>
          ) : (
          <form onSubmit={onSubmit} className="space-y-4" data-testid="signin-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Work Email")}
              </Label>
              <div className="relative mt-2">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                  autoComplete="username"
                  placeholder="yourname@yourcompany.com"
                  className="h-12 pl-9 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
                  data-testid="signin-email"
                />
              </div>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Master Password")}
              </Label>
              <PasswordInput
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
                data-testid="signin-password"
                toggleTestId="signin-password-toggle"
              />
            </div>
            <label className="inline-flex items-center gap-2 cursor-pointer select-none -mt-1">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 accent-red-700"
                data-testid="signin-remember"
              />
              <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                {t("Remember me on this device")}
              </span>
            </label>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="signin-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Signing in…")}
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4 mr-2" /> {t("Sign In")}
                </>
              )}
            </Button>
            {/* iter422 · Phase 24 · Optional device passkey sign-in (Face ID · Touch ID · Hello) */}
            {passkeyReady ? (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={onPasskeySignIn}
                  disabled={passkeyBusy || submitting}
                  data-testid="signin-passkey-btn"
                  className="w-full h-11 inline-flex items-center justify-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-800 bg-white border-2 border-slate-300 hover:border-red-700 hover:text-red-700 rounded-md disabled:opacity-50"
                >
                  {passkeyBusy ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Fingerprint className="w-4 h-4" />
                  )}
                  {passkeyBusy ? t("Verifying device…") : t("Use device sign-in")}
                </button>
                <p className="mt-2 text-[11px] text-slate-500 leading-snug" data-testid="signin-passkey-hint">
                  {t("Your device handles Face ID / Touch ID securely. MASCI never stores biometric information.")}
                </p>
              </div>
            ) : null}
          </form>
          )}

          <div className="mt-8 pt-6 border-t border-slate-200">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-2">
              {t("Single-Workspace Sign-In")}
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <Link to="/pm/login" className="wp17-public-link" data-testid="signin-pm-link">
                <span>Project Management</span><span aria-hidden="true">→</span>
              </Link>
              <Link to="/shop/login" className="wp17-public-link" data-testid="signin-shop-link">
                <span>Shop Operations</span><span aria-hidden="true">→</span>
              </Link>
              <Link to="/hr/login" className="wp17-public-link" data-testid="signin-hr-link">
                <span>Human Resources</span><span aria-hidden="true">→</span>
              </Link>
              <Link to="/safety-portal/login" className="wp17-public-link" data-testid="signin-safety-link">
                <span>Safety Operations</span><span aria-hidden="true">→</span>
              </Link>
              <Link to="/dispatch-portal/login" className="wp17-public-link" data-testid="signin-dispatch-link">
                <span>Transportation Operations</span><span aria-hidden="true">→</span>
              </Link>
              <Link to="/leadership/login" className="wp17-public-link" data-testid="signin-leadership-link">
                <span>Field Leadership</span><span aria-hidden="true">→</span>
              </Link>
              <Link to="/admin/login" className="wp17-public-link col-span-2" data-testid="signin-admin-link">
                <span>Administration</span><span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
          </div>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI Operations Platform · Master Sign-In")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
