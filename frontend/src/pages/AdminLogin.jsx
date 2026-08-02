// AdminLogin.jsx — iter85 rewrite
//
// Parity with PM/Shop/HR login pages: email + password fields, "Forgot
// password?" link, "Remember me on this device" checkbox. Authenticates
// via the unified `/api/auth/multi-login` directory endpoint (same one
// /sign-in uses), so an admin's user_directory record drives the
// session.
//
// The legacy single-password `POST /api/admin/login` endpoint is left
// intact server-side as an API-only break-glass path (callable via
// curl / scripts) but the human-facing UI now matches every other
// portal's sign-in chrome.
import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ShieldAlert, Loader2, Mail, KeyRound, Fingerprint } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginHelp } from "@/components/PortalLoginHelp";
import { AuthRequiredBanner } from "@/components/PortalContextBanner";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { api } from "@/lib/api";
import { applyMultiLoginResponse, landingFor } from "@/lib/directoryAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { passkeySupported, platformAuthenticatorAvailable, signInWithPasskey } from "@/lib/passkeys";
import { useT } from "@/lib/i18n";
import { useBranding } from "@/lib/BrandingProvider";
import { toast } from "sonner";

export default function AdminLogin() {
  const { t } = useT();
  const branding = useBranding();
  const brandShort = branding?.platform_short_name || branding?.company_name || "Operations";
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  // iter422 · Phase 24 · Optional device-native sign-in
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
    return () => {
      cancelled = true;
    };
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
        // Redirect to /sign-in to complete MFA flow (existing path)
        toast.message(t("Continue sign-in at the master page."));
        navigate("/sign-in", { replace: true });
        return;
      }
      if (data?.ok) {
        applyMultiLoginResponse(data, rememberMe);
        toast.success(`${t("Welcome")} ${data?.user?.name || ""}`, { duration: 4000 });
        navigate(landingFor(data.user), { replace: true });
      } else {
        toast.error(t("Device sign-in failed"));
      }
    } catch (err) {
      const name = err?.name || "";
      const msg = err?.message || t("Device sign-in failed");
      if (name === "NotAllowedError" || /cancel/i.test(msg)) {
        // user cancelled · stay calm
      } else {
        toast.error(msg, { duration: 5000 });
      }
    } finally {
      setPasskeyBusy(false);
    }
  };

  useEffect(() => {
    // TRACK 14.0-S2A · Multi-tab SSO auto-elevation.
    //
    // If the user already has a valid Admin token (from a fresh
    // multi-login in another tab, or from a not-yet-expired prior
    // session), redirect them straight to the Admin Hub instead of
    // re-rendering the login form. This is the single fix for the
    // iteration_515 multi-tab SSO defect: tokens land in localStorage
    // but each portal /login page must check for them on mount.
    //
    // Iter88 contract preserved: we do NOT clear tokens here. We
    // ONLY redirect away when a valid token already exists. If no
    // token exists, the login form renders as before.
    const tok = getAdminToken();
    if (tok) {
      navigate("/admin", { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    // Iter88 — DO NOT wipe tokens on mount.
    //
    // Previous behavior cleared every portal token here so a stale
    // session couldn't poison the next login. That was hostile to
    // multi-portal users: if a route-guard race transiently bounced
    // them to this page, the mount wipe killed their entire session,
    // making the bounce permanent.
    //
    // Tokens are now cleared ONLY on:
    //   • Explicit "Sign Out" (handled elsewhere)
    //   • Right before a successful login response is applied (the new
    //     bundle overwrites the old tokens via setX(), no clear needed)
    // Reaching this page with a live multi-portal session is a transient
    // hiccup — the page-guards' hydration hook will rescue it.
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      toast.error("Enter your work email and admin password");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post(
        "/auth/multi-login",
        { email: email.trim().toLowerCase(), password },
        { timeout: 90000 } // backend cold-start can take ~60s
      );
      if (res?.data?.ok) {
        applyMultiLoginResponse(res.data, rememberMe);
        const user = res.data.user;
        const portals = user?.portals || [];
        if (!portals.includes("admin")) {
          // Authenticated, but this directory user doesn't have admin scope.
          // Redirect them to whatever portal they DO have access to.
          toast.warning(
            `Welcome ${user?.name || ""} — this account doesn't have Admin access. Routing you to ${portals[0]?.toUpperCase() || "the Hub"}.`,
            { duration: 6000 }
          );
          navigate(landingFor(user), { replace: true });
          return;
        }
        toast.success(`Welcome back, ${user?.name || "admin"}`);
        const from = location.state?.from || "/admin";
        navigate(from, { replace: true });
      } else {
        toast.error("Sign-in failed — server did not return a session");
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      let msg;
      if (status === 401) {
        msg = "Wrong email or password";
      } else if (status === 423) {
        msg = "Account is locked — call the office";
      } else if (status === 429) {
        msg = detail || "Too many attempts — wait a minute and try again";
      } else if (status === 520 || status === 521 || status === 522 || status === 523 || status === 524) {
        msg = "Server is waking up — give it ~60 seconds and try again";
      } else if (status >= 500 && status < 600) {
        msg = `Server error (${status}) — try again in a moment`;
      } else if (err?.code === "ECONNABORTED" || /timeout/i.test(err?.message || "")) {
        msg = "Request timed out — server is cold-starting, try again";
      } else if (!err?.response) {
        msg = "Can't reach server — check your internet";
      } else {
        msg = typeof detail === "string" ? detail : `Sign-in failed (${status || "unknown"})`;
      }
      toast.error(msg, { duration: 6000 });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalLoginShell
      headerBorderClass="border-red-700"
      backHoverClass="hover:text-red-300"
      backTestId="admin-login-back"
      rootTestId="admin-login-page"
      footerLabel={`${brandShort} · Office Use Only`}
    >
      <AuthRequiredBanner />
      <div className="bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
        <div className="flex items-center gap-3 mb-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
              {t("Restricted Area")}
            </div>
            <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1" data-testid="admin-login-title">
              {t("Admin Sign In")}
            </h1>
          </div>
        </div>
        <p className="text-slate-600 text-sm mt-3 mb-6">{t("Office sign-in for managers and supervisors.")}</p>

        <form onSubmit={onSubmit} className="space-y-4" data-testid="admin-login-form">
          <div>
            <Label htmlFor="admin-email" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
              {t("Work Email")}
            </Label>
            <div className="relative mt-2">
              <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <Input
                id="admin-email"
                type="email"
                inputMode="email"
                autoComplete="username"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@yourcompany.com"
                className="h-12 pl-9 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                data-testid="admin-email-input"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="admin-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1">
              <KeyRound className="w-3 h-3" /> {t("Password")}
            </Label>
            <PasswordInput
              id="admin-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
              data-testid="admin-password-input"
              toggleTestId="admin-password-toggle"
            />
          </div>

          <div className="flex items-center justify-between flex-wrap gap-2">
            <label className="inline-flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 accent-red-700"
                data-testid="admin-remember-me"
              />
              <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                {t("Remember me on this device")}
              </span>
            </label>
            <span className="text-[11px] text-slate-500">{t("Forgot password? Call the office.")}</span>
          </div>

          <Button
            type="button"
            disabled={submitting}
            onClick={onSubmit}
            className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
            data-testid="admin-login-submit"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Verifying…")}
              </>
            ) : (
              <>{t("Sign In")}</>
            )}
          </Button>

          {passkeyReady ? (
            <div className="pt-2">
              <button
                type="button"
                onClick={onPasskeySignIn}
                disabled={passkeyBusy || submitting}
                data-testid="admin-login-passkey-btn"
                className="w-full h-11 inline-flex items-center justify-center gap-2 text-sm font-bold uppercase tracking-wide text-slate-800 bg-white border-2 border-slate-300 hover:border-red-700 hover:text-red-700 rounded-md disabled:opacity-50"
              >
                {passkeyBusy ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Fingerprint className="w-4 h-4" />
                )}
                {passkeyBusy ? t("Verifying device…") : t("Use device sign-in")}
              </button>
            </div>
          ) : null}
        </form>
        <PortalLoginHelp portal="admin" />

        <p className="mt-5 pt-4 border-t border-slate-200 text-[11px] text-slate-500 leading-relaxed text-center">
          {t("Access multiple portals?")}{" "}
          <Link
            to="/sign-in"
            className="inline-flex items-center min-h-[44px] px-1 -mx-1 text-slate-900 font-bold hover:underline"
            data-testid="admin-login-master-link"
          >
            {t("Use the master sign-in")}
          </Link>{" "}
          {t("to land on any portal in one step.")}
        </p>
      </div>
    </PortalLoginShell>
  );
}