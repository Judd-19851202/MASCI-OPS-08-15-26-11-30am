// Safety Portal sign-in. Mirrors HrLogin / ShopLogin chrome. Cyan
// accent. Posts to /api/safety/login and stores the token via
// safetyAuth.setSafetyToken so the rest of the portal can hit
// /api/safety/* with `X-Safety-Token` headers.
import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Loader2, ShieldAlert, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { PortalLoginHelp } from "@/components/PortalLoginHelp";
import { LangToggle } from "@/components/LangToggle";
import { AuthRequiredBanner } from "@/components/PortalContextBanner";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { toast } from "sonner";
import axios from "axios";
import { useT } from "@/lib/i18n";
import {
  setSafetyToken,
  setSafetyUser,
  isSafety,
} from "@/lib/safetyAuth";
import { setAdminToken } from "@/lib/adminAuth";
import { setMustChange } from "@/lib/mustChangePassword";
import { useRedirectIfDirectoryGrant } from "@/lib/useRedirectIfDirectoryGrant";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SafetyLogin() {
  const { t } = useT();
  const nav = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [remember, setRemember] = useState(true);

  // TRACK 14.0-SSO · If the user already holds a directory session
  // that grants Safety, silently mint the Safety token and forward
  // into /safety-portal instead of showing a redundant login form.
  // Falls back to the legacy "isSafety() → redirect" short-circuit
  // baked into the hook so single-portal Safety users keep their
  // existing UX.
  useRedirectIfDirectoryGrant("safety", isSafety(), "/safety-portal");

  useEffect(() => {
    // TRACK 14.0-S2A · Multi-tab SSO auto-elevation. If a valid
    // Safety (or Admin-as-Safety) token already exists in this
    // browser from a prior tab's multi-login, redirect to
    // /safety-portal and skip the login form. Iteration_515
    // surfaced this as a real defect: tokens land in localStorage
    // but the page re-rendered the login form anyway.
    if (isSafety()) {
      nav("/safety-portal", { replace: true });
    }
  }, [nav]);

  const submit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setBusy(true);
    try {
      const r = await axios.post(`${API}/safety/login`, {
        email: email.trim(),
        password,
      });
      // iter346-B · universal super-admin fallback. Backend returns
      // kind:"admin" when a super-admin signed in via this gate.
      const kind = r?.data?.kind || "safety";
      if (kind === "admin") {
        setAdminToken(r.data.token, { remember });
        const name = r.data?.user?.name;
        toast.success(name ? `${t("Welcome,")} ${name}` : t("Welcome, Admin"));
        nav("/admin", { replace: true });
        return;
      }
      setSafetyToken(r.data.token, remember);
      setSafetyUser(r.data.user);
      // Track 15.14A Layer 2 — persist must-change-password flag.
      const mustChange = !!r.data.must_change_password;
      setMustChange("safety", mustChange);
      toast.success(t("Welcome to Safety Operations"));
      // iter322-B · honor redirect intent — bounce user back to the
      // protected workflow they originally clicked, not the hub root.
      const intended = location.state?.continuity?.continueTo
        || location.state?.from
        || "/safety-portal";
      if (mustChange) {
        nav("/safety-portal/change-password", {
          replace: true,
          state: { from: intended },
        });
      } else {
        nav(intended, { replace: true });
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("Invalid email or password"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PortalLoginShell
      headerBorderClass="border-cyan-700"
      backHoverClass="hover:text-cyan-300"
      backTestId="safety-login-back"
      rootTestId="safety-portal-login"
      footerLabel={t("MASCI · Safety Operations")}
    >
      {/* iter322-B · context-aware banner when redirected from a
          protected workflow (rendered only when state.continuity
          is present — zero footprint otherwise). */}
      <AuthRequiredBanner />
      <div className="bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-cyan-700 text-white">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700 font-bold">
                {t("Safety Operations")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Safety Operations Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            {t(
              "Safety Manager, Coordinator, and Officer access. Use the credentials issued by Admin."
            )}
          </p>

          <form onSubmit={submit} className="space-y-4" data-testid="safety-login-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Work Email")}
              </Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                autoComplete="username"
                placeholder="yourname@yourcompany.com"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-600"
                data-testid="safety-login-email"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Password")}
              </Label>
              <PasswordInput
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-600"
                data-testid="safety-login-password"
                toggleTestId="safety-password-toggle"
              />
            </div>
            <div className="flex items-center justify-between gap-3 -mt-1">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="w-4 h-4 accent-cyan-700"
                  data-testid="safety-remember-me"
                />
                <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                  {t("Remember me on this device")}
                </span>
              </label>
              <Link
                to="/safety-portal/forgot-password"
                className="text-xs font-bold text-cyan-700 hover:text-cyan-900 underline-offset-2 hover:underline"
                data-testid="safety-forgot-link"
              >
                {t("Forgot password?")}
              </Link>
            </div>
            <Button
              type="submit"
              disabled={busy || !email.trim() || !password}
              className="w-full h-12 bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-cyan-900 disabled:opacity-60"
              data-testid="safety-login-submit"
            >
              {busy ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Signing in…")}
                </>
              ) : (
                <>{t("Sign In")}</>
              )}
            </Button>
          </form>
          <PortalLoginHelp portal="safety" />
      </div>
    </PortalLoginShell>
  );
}
