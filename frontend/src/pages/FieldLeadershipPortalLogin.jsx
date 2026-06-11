// FieldLeadershipPortalLogin — iter343 · Platform-family chrome rebuild.
//
// This page now mirrors HrLogin.jsx STRUCTURALLY, line-for-line, so an
// operator who has used /hr/login feels at home here. Differences are
// purely portal-palette (red instead of HR's purple) — the layout,
// spacing, header bar, blueprint background, caution-stripe, card
// chrome, form pattern, button rhythm, footer, and helper-link section
// are all platform-standard.
//
// Auth model:
//   - Primary: per-user email + password against /api/field-leadership/portal/login
//     (FL identity collection: `field_leadership_users`, NOT the master
//      `user_directory`. This is by design — FL is a bounded operational
//      role family with its own lifecycle.)
//   - Super-admin / Admin: NOT accepted at this gate. Admins who arrive
//     here while already signed in as Admin see an "Already signed in"
//     helper that takes them straight to the FL Hub (the Hub gate
//     accepts admin tokens — `isAdmin()` satisfies it).
//   - Legacy shared-password: hidden behind a calm secondary link to
//     /leadership/legacy-login (backwards compat for crews that still
//     know only the shared MASCIGC code).

import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { HardHat, Loader2, ArrowLeft, Mail, KeyRound, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { PortalLoginHelp } from "@/components/PortalLoginHelp";
import { LangToggle } from "@/components/LangToggle";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setFlToken, setFlUser, clearFlToken } from "@/lib/flAuth";
import { isAdmin, clearAdminToken, setAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { clearHrToken } from "@/lib/hrAuth";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";

export default function FieldLeadershipPortalLogin() {
  const { t } = useT();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotBusy, setForgotBusy] = useState(false);
  const [adminAware, setAdminAware] = useState(false);

  useEffect(() => {
    // If an Admin token is present, surface a calm shortcut — the FL Hub
    // already accepts admin tokens, so we don't force them to sign in
    // again. Bounded RBAC clarity.
    setAdminAware(isAdmin());
  }, []);

  const submitForgot = async () => {
    const e = (forgotEmail || "").trim();
    if (!e) return;
    setForgotBusy(true);
    try {
      await api.post("/field-leadership/portal/forgot-password", { email: e.toLowerCase() });
      toast.success(t("If that email is on file, a reset link is on its way."));
      setForgotOpen(false);
    } catch (err) {
      toast.error(operationalError(err,
        t("Couldn't send reset email — try again or call the office"),
        t("Your session expired. Please sign in again.")));
    } finally {
      setForgotBusy(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    const em = (email || "").trim().toLowerCase();
    if (!em || !password) {
      toast.error(t("Enter your work email and password"));
      return;
    }
    setSubmitting(true);
    try {
      // Clear sibling portal tokens so no ghost sessions linger — same
      // pattern as HrLogin / PmLogin / ShopLogin.
      clearAdminToken(); clearHrToken(); clearPmToken(); clearShopToken(); clearFlToken();
      const r = await api.post(
        "/field-leadership/portal/login",
        { email: em, password },
        { timeout: 90000 },
      );
      const tok = r?.data?.token;
      const user = r?.data?.user || null;
      const kind = r?.data?.kind || "fl";
      if (!tok) throw new Error("missing-token");
      if (kind === "admin") {
        // iter344 · Super-admin signed in via FL screen. Store as admin
        // token (the Hub gate accepts admin via isAdmin()). Do NOT mint
        // an FL identity — admin is a different identity domain.
        setAdminToken(tok, { remember: rememberMe });
        toast.success(`${t("Welcome,")} ${user?.name || t("Admin")}`);
      } else {
        setFlToken(tok, rememberMe);
        setFlUser(user);
        toast.success(`${t("Welcome,")} ${user?.name || t("Field Leader")}`);
      }
      if (r?.data?.must_change_password) {
        navigate("/field-leadership/portal/change-password", { replace: true });
      } else {
        // Land directly in the Field Leadership Hub.
        navigate("/leadership", { replace: true });
      }
    } catch (err) {
      const status = err?.response?.status;
      let msg;
      if (status === 401) msg = t("Invalid email or password");
      else if (status === 423) msg = t("Account is disabled — call the office to reactivate");
      else if (status === 429) msg = t("Too many attempts — wait a minute and try again");
      else if (err?.code === "ECONNABORTED" || /timeout/i.test(err?.message || ""))
        msg = t("Request timed out — server is cold-starting, try again");
      else if (!err?.response) msg = t("Can't reach server — check your internet");
      else msg = operationalError(err,
        t("Sign in failed — try again or call the office"),
        t("Your session expired. Please sign in again."));
      toast.error(msg, { duration: 6000 });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalLoginShell
      headerBorderClass="border-red-700"
      backHoverClass="hover:text-red-300"
      backTestId="fl-login-back"
      rootTestId="fl-portal-login"
      footerLabel={t("MASCI · Field Leadership Portal")}
      dialogs={
        <Dialog open={forgotOpen} onOpenChange={setForgotOpen}>
          <DialogContent data-testid="fl-forgot-dialog">
            <DialogHeader>
              <DialogTitle className="font-display font-black flex items-center gap-2 text-red-700">
                <KeyRound className="w-5 h-5" /> {t("Reset your password")}
              </DialogTitle>
              <DialogDescription className="leading-relaxed">
                {t("Enter your work email. If we have you on file with an active Field Leadership account, we'll email you a one-time link to set a new password. Link expires in 30 minutes.")}
              </DialogDescription>
            </DialogHeader>
            <div className="pt-1">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
                {t("Work Email")}
              </Label>
              <div className="relative mt-1.5">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <Input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      submitForgot();
                    }
                  }}
                  placeholder="yourname@mascigc.com"
                  className="h-11 pl-9 text-base border-2 border-slate-300"
                  data-testid="fl-forgot-email"
                  autoFocus
                />
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setForgotOpen(false)} disabled={forgotBusy}>
                {t("Cancel")}
              </Button>
              <Button
                onClick={submitForgot}
                disabled={forgotBusy || !forgotEmail.trim()}
                className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
                data-testid="fl-forgot-submit"
              >
                {forgotBusy ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Sending…")}</>
                ) : (
                  <><Mail className="w-4 h-4 mr-1" /> {t("Email reset link")}</>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      }
    >
      {adminAware ? (
            <div
              className="mb-4 bg-amber-50 border-l-4 border-amber-500 rounded p-3 text-xs text-slate-800"
              data-testid="fl-admin-aware"
            >
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-amber-700" />
                <div className="flex-1">
                  <div className="font-bold text-slate-900">{t("You're already signed in as Admin")}</div>
                  <p className="mt-1 leading-snug">
                    {t("Admin tokens already satisfy the Field Leadership Hub gate — you do not need to sign in here.")}
                  </p>
                  <Link
                    to="/leadership"
                    className="inline-block mt-1 font-bold text-amber-700 hover:text-amber-900 underline-offset-2 hover:underline"
                    data-testid="fl-admin-continue"
                  >
                    {t("Continue to Field Leadership Hub")} →
                  </Link>
                </div>
              </div>
            </div>
          ) : null}

          <div className="bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
            <div className="flex items-center gap-3 mb-2">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
                <HardHat className="w-6 h-6" />
              </div>
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700">
                  {t("Field Leadership")}
                </div>
                <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                  {t("Field Leadership Sign In")}
                </h1>
              </div>
            </div>
            <p className="text-slate-600 text-sm mt-3 mb-6">
              {t("Sign in with your MASCI work email. For approved Field Leadership personnel — Superintendents, Foremen, Truck Bosses, and Working Supervisors. If this is your first time, the admin or HR will give you a temporary password — you'll choose your own on first login.")}
            </p>

            <form onSubmit={onSubmit} className="space-y-4" data-testid="fl-login-form">
              <div>
                <Label htmlFor="fl-email" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                  {t("Work Email")}
                </Label>
                <div className="relative mt-2">
                  <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <Input
                    id="fl-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoFocus
                    autoComplete="username"
                    placeholder="yourname@mascigc.com"
                    className="h-12 pl-9 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
                    data-testid="fl-email"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="fl-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                  {t("Password")}
                </Label>
                <PasswordInput
                  id="fl-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
                  data-testid="fl-password"
                  toggleTestId="fl-password-toggle"
                />
              </div>
              <div className="flex items-center justify-between gap-3 -mt-1">
                <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 accent-red-700"
                    data-testid="fl-remember-me"
                  />
                  <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                    {t("Remember me on this device")}
                  </span>
                </label>
                <button
                  type="button"
                  onClick={() => { setForgotEmail(email); setForgotOpen(true); }}
                  className="text-xs font-bold text-red-700 hover:text-red-900 underline-offset-2 hover:underline"
                  data-testid="fl-forgot-link"
                >
                  {t("Forgot password?")}
                </button>
              </div>
              <Button
                type="submit"
                disabled={submitting}
                className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
                data-testid="fl-submit"
              >
                {submitting ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Verifying…")}</>
                ) : (
                  <>{t("Sign In")}</>
                )}
              </Button>
              <p className="text-xs text-slate-500 leading-relaxed pt-1">
                {t("Forgot password? Click the link above and we'll email you a reset. Or call the office — admin or HR can issue a fresh temp password from the console.")}
              </p>
            </form>

            <PortalLoginHelp portal="leadership" />

            <div className="mt-6 pt-4 border-t border-slate-200 text-center">
              <Link
                to="/leadership/legacy-login"
                className="inline-flex items-center min-h-[32px] px-2 py-1 text-[11px] text-slate-500 hover:text-slate-800 underline-offset-2 hover:underline"
                data-testid="fl-legacy-login-link"
              >
                {t("Crew using a shared leadership code? Use the legacy gate →")}
              </Link>
            </div>
          </div>
    </PortalLoginShell>
  );
}
