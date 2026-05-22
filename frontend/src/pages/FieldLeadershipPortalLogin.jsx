import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Loader2, ArrowLeft, Mail, KeyRound, HardHat } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setFlToken, setFlUser, clearFlToken } from "@/lib/flAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { clearHrToken } from "@/lib/hrAuth";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";

/**
 * FieldLeadershipPortalLogin (iter314)
 *
 * Per-user email/password identity for approved Field Leadership
 * personnel (Superintendents · Foremen · Truck Bosses · Working
 * Supervisors). Mirrors HrLogin.jsx structure exactly. Slate accent
 * (operational tone, distinct from HR purple).
 *
 * NOTE — distinct from `/field-leadership/login` (legacy shared-
 * password document gate; powered by `leadershipAuth.js`). This
 * portal lives at `/field-leadership/portal/login`.
 */
export default function FieldLeadershipPortalLogin() {
  const { t } = useT();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotBusy, setForgotBusy] = useState(false);

  const submit = async (e) => {
    e?.preventDefault?.();
    const em = (email || "").trim().toLowerCase();
    if (!em || !password) {
      toast.error(t("Email and password are both required"));
      return;
    }
    setSubmitting(true);
    try {
      // Clear other portal tokens on arrival — no ghost sessions.
      clearAdminToken(); clearHrToken(); clearPmToken(); clearShopToken(); clearFlToken();
      const r = await api.post("/field-leadership/portal/login", {
        email: em, password,
      });
      const tok = r?.data?.token;
      const user = r?.data?.user || null;
      if (!tok) throw new Error("missing-token");
      setFlToken(tok, true);
      setFlUser(user);
      toast.success(`${t("Welcome,")} ${user?.name || t("Field Leader")}`);
      if (r?.data?.must_change_password) {
        navigate("/field-leadership/portal/change-password", { replace: true });
      } else {
        // iter342 · land directly in the Field Leadership Hub. The Hub
        // gate (FieldLeadershipHub.jsx) now accepts the FL portal token
        // as proof, so this collapses the previous two-step
        // "portal-dashboard → hub" navigation into one calm landing.
        navigate("/leadership", { replace: true });
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      toast.error(
        typeof detail === "string" ? detail
          : status === 401 ? t("Invalid email or password")
          : status === 429 ? t("Too many attempts — wait a minute and try again")
          : t("Sign in failed — try again or call the office")
      );
    } finally {
      setSubmitting(false);
    }
  };

  const submitForgot = async () => {
    const em = (forgotEmail || "").trim();
    if (!em) return;
    setForgotBusy(true);
    try {
      await api.post("/field-leadership/portal/forgot-password", {
        email: em.toLowerCase(),
      });
      toast.success(t("If that email is on file, a reset link is on its way."));
      setForgotOpen(false);
    } catch {
      toast.error(t("Couldn't send reset email — try again or call the office"));
    } finally {
      setForgotBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid="fl-portal-login">
      <div className="max-w-md mx-auto w-full px-4 pt-6 flex items-center justify-between">
        <Link to="/" className="text-xs text-slate-500 hover:text-slate-900 inline-flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> {t("Back to home")}
        </Link>
        <LangToggle />
      </div>
      <div className="max-w-md mx-auto w-full px-4 py-10 flex-1">
        <div className="flex flex-col items-center mb-6">
          <MasciLogo size={56} />
          <div className="mt-3 inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] font-bold text-slate-600 bg-slate-100 border border-slate-300 rounded px-2 py-1">
            <HardHat className="w-3 h-3" /> {t("Field Leadership Portal")}
          </div>
          <h1 className="mt-3 text-2xl font-bold text-slate-900 tracking-tight">
            {t("Field Leadership sign-in")}
          </h1>
          <p className="mt-1 text-xs text-slate-600 text-center max-w-xs">
            {t("For approved Field Leadership personnel only — Superintendents, Foremen, Truck Bosses, and Working Supervisors.")}
          </p>
        </div>
        <form onSubmit={submit} className="bg-white border border-slate-200 rounded-lg p-5 space-y-3 shadow-sm">
          <div>
            <Label htmlFor="fl-email" className="text-xs uppercase tracking-wider text-slate-600">
              {t("Email")}
            </Label>
            <div className="relative mt-1">
              <Mail className="w-4 h-4 absolute left-2.5 top-2.5 text-slate-400" />
              <Input
                id="fl-email" data-testid="fl-email"
                type="email" value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="fieldleader@mascigc.com"
                className="pl-8"
                autoComplete="email"
                disabled={submitting}
                required
              />
            </div>
          </div>
          <div>
            <Label htmlFor="fl-password" className="text-xs uppercase tracking-wider text-slate-600">
              {t("Password")}
            </Label>
            <div className="relative mt-1">
              <KeyRound className="w-4 h-4 absolute left-2.5 top-2.5 text-slate-400 z-10" />
              <PasswordInput
                id="fl-password" data-testid="fl-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-8"
                autoComplete="current-password"
                disabled={submitting}
              />
            </div>
          </div>
          <Button
            type="submit" disabled={submitting}
            data-testid="fl-submit"
            className="w-full bg-slate-800 hover:bg-slate-900 text-white"
          >
            {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            {t("Sign in")}
          </Button>
          <button
            type="button"
            onClick={() => { setForgotEmail(email); setForgotOpen(true); }}
            className="text-xs text-slate-600 hover:text-slate-900 underline w-full text-center"
            data-testid="fl-forgot-link"
          >
            {t("Forgot password?")}
          </button>
        </form>
        <div className="mt-4">
          <HelpTipBlock formKey="field-leadership.portal-login" />
        </div>
        <p className="mt-4 text-[11px] text-slate-500 text-center">
          {t("This portal is for governed operational identity access. The legacy field-leadership document viewer is unchanged.")}
        </p>
        {/* iter342 · backwards-compat disclosure — crews that only know
            the shared MASCIGC leadership code can still reach the legacy
            gate. Hidden behind a calm secondary link so the modern
            per-user flow is the visible primary UX. */}
        <div className="mt-3 text-center">
          <Link
            to="/leadership/legacy-login"
            className="text-[11px] text-slate-500 hover:text-slate-800 underline"
            data-testid="fl-legacy-login-link"
          >
            {t("Crew using a shared leadership code? Use the legacy gate →")}
          </Link>
        </div>
      </div>
      <ForgedOpsAttribution />
      <Dialog open={forgotOpen} onOpenChange={setForgotOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("Reset your Field Leadership password")}</DialogTitle>
            <DialogDescription>
              {t("Enter your work email. If it's on file, we'll send a reset link valid for 30 minutes.")}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label className="text-xs">{t("Email")}</Label>
            <Input
              type="email"
              value={forgotEmail}
              onChange={(e) => setForgotEmail(e.target.value)}
              placeholder="fieldleader@mascigc.com"
              data-testid="fl-forgot-email"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setForgotOpen(false)} disabled={forgotBusy}>
              {t("Cancel")}
            </Button>
            <Button onClick={submitForgot} disabled={forgotBusy || !forgotEmail} data-testid="fl-forgot-submit">
              {forgotBusy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              {t("Send reset link")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
