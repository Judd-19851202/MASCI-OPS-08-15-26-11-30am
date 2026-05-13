import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Briefcase, Loader2, ArrowLeft, Mail, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setPmToken, clearPmToken } from "@/lib/pmAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function PmLogin() {
  const { t } = useT();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotBusy, setForgotBusy] = useState(false);

  useEffect(() => {
    // Iter88 — DO NOT wipe tokens on mount.
    // Previously cleared all 3 tokens here; killed multi-portal sessions
    // when this page was reached transiently. See AdminLogin.jsx for the
    // full rationale.
  }, []);

  const submitForgot = async () => {
    const e = (forgotEmail || "").trim();
    if (!e) return;
    setForgotBusy(true);
    try {
      const res = await api.post("/pm/forgot-password", { email: e.toLowerCase() });
      // Backend always returns ok:true with a generic message — no
      // enumeration of valid emails. Show the message verbatim.
      toast.success(
        res?.data?.message ||
          t("If that email is on file, a reset link is on its way.")
      );
      setForgotOpen(false);
    } catch (err) {
      const status = err?.response?.status;
      // 429 only fires on the per-IP brute-force gate.
      const detail = err?.response?.data?.detail;
      toast.error(
        typeof detail === "string"
          ? detail
          : status === 429
          ? t("Too many requests — wait a minute and try again")
          : t("Couldn't send reset email — try again or call the office")
      );
    } finally {
      setForgotBusy(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      toast.error(t("Enter your work email and password"));
      return;
    }
    setSubmitting(true);
    // Iter88 — DO NOT pre-wipe tokens here either. setPmToken below
    // overwrites the PM slot; leaving admin/shop tokens alone preserves
    // multi-portal sessions for legacy single-portal direct logins.
    try {
      const res = await api.post(
        "/pm/login",
        { email: email.trim().toLowerCase(), password },
        { timeout: 90000 }
      );
      if (res?.data?.ok && res?.data?.token) {
        setPmToken(res.data.token, { remember: rememberMe });
        // First-time login OR admin reset → must rotate before any access.
        if (res.data.must_change_password) {
          toast.info(t("Welcome — please choose a new password"));
          navigate("/pm/change-password", {
            replace: true,
            // Forward the original target so PmChangePassword can land
            // them where they were headed (e.g. /training/pm) instead
            // of the generic /pm dashboard.
            state: { from: location.state?.from },
          });
          return;
        }
        const pmName = res.data?.pm?.name;
        toast.success(pmName ? `${t("Welcome")} ${pmName}` : t("Welcome, PM"));
        const from = location.state?.from || "/pm";
        navigate(from, { replace: true });
      } else {
        toast.error(t("Login failed — server didn't return a token"));
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      let msg;
      if (status === 401) msg = typeof detail === "string" ? detail : t("Wrong email or password");
      else if (status === 403) msg = typeof detail === "string" ? detail : t("Account locked — contact admin");
      else if ([520, 521, 522, 523, 524].includes(status))
        msg = t("Server is waking up — give it ~60 seconds and try again");
      else if (status >= 500 && status < 600)
        msg = `${t("Server error")} (${status}) — ${t("try again in a moment")}`;
      else if (err?.code === "ECONNABORTED" || /timeout/i.test(err?.message || ""))
        msg = t("Request timed out — server is cold-starting, try again");
      else if (!err?.response) msg = t("Can't reach server — check your internet");
      else msg = `${t("Login failed")} (${status || "unknown"})`;
      toast.error(msg, { duration: 6000 });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-amber-500">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-amber-300 text-sm font-bold uppercase tracking-wide"
            data-testid="pm-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
          </Link>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-500 text-white">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700">
                {t("Project Management")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("PM Portal Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            {t("Sign in with your MASCI work email. If this is your first time, the admin will give you a temporary password — you'll choose your own on first login.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="pm-login-form">
            <div>
              <Label
                htmlFor="pm-email"
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700"
              >
                {t("Work Email")}
              </Label>
              <div className="relative mt-2">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <Input
                  id="pm-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                  autoComplete="username"
                  placeholder="yourname@mascigc.com"
                  className="h-12 pl-9 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                  data-testid="pm-email-input"
                />
              </div>
            </div>
            <div>
              <Label
                htmlFor="pm-password"
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700"
              >
                {t("Password")}
              </Label>
              <PasswordInput
                id="pm-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="pm-password-input"
                toggleTestId="pm-password-toggle"
              />
            </div>
            <div className="flex items-center justify-between gap-3 -mt-1">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 accent-amber-600"
                  data-testid="pm-remember-me"
                />
                <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                  {t("Remember me on this device")}
                </span>
              </label>
              <button
                type="button"
                onClick={() => {
                  setForgotEmail(email);
                  setForgotOpen(true);
                }}
                className="text-xs font-bold text-red-700 hover:text-red-900 underline-offset-2 hover:underline"
                data-testid="pm-forgot-password-link"
              >
                {t("Forgot password?")}
              </button>
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-amber-500 hover:bg-amber-600 text-slate-900 font-bold uppercase tracking-wide text-sm border-b-2 border-amber-700"
              data-testid="pm-login-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Verifying…")}
                </>
              ) : (
                <>{t("Sign In")}</>
              )}
            </Button>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              {t("Forgot password? Click the link above and we'll email you a reset. Or call the office — admin can issue a fresh temp password from the console.")}
            </p>
          </form>
        </div>
      </main>

      {/* Forgot password dialog */}
      <Dialog open={forgotOpen} onOpenChange={setForgotOpen}>
        <DialogContent data-testid="pm-forgot-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-amber-700">
              <KeyRound className="w-5 h-5" /> {t("Reset your password")}
            </DialogTitle>
            <DialogDescription className="leading-relaxed">
              {t("Enter your work email. If we have you on file with an active account, we'll email you a one-time link to set a new password. Link expires in 30 minutes.")}
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
                data-testid="pm-forgot-email-input"
                autoFocus
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setForgotOpen(false)}
              disabled={forgotBusy}
              data-testid="pm-forgot-cancel"
            >
              {t("Cancel")}
            </Button>
            <Button
              onClick={submitForgot}
              disabled={forgotBusy || !forgotEmail.trim()}
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
              data-testid="pm-forgot-submit"
            >
              {forgotBusy ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Sending…")}
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4 mr-1" /> {t("Email reset link")}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Project Management Portal")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
