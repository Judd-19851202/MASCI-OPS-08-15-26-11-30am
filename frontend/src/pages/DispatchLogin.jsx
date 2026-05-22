// Dispatch Portal sign-in. Mirrors HrLogin / ShopLogin / SafetyLogin
// chrome. Orange-700 accent. Posts to /api/dispatch/login and stores
// the token via dispatchAuth.setDispatchToken so the rest of the
// portal can hit /api/dispatch/* with X-Dispatch-Token headers.
import React, { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Loader2, Truck, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { PortalLoginHelp } from "@/components/PortalLoginHelp";
import { LangToggle } from "@/components/LangToggle";
import { AuthRequiredBanner } from "@/components/PortalContextBanner";
import { toast } from "sonner";
import axios from "axios";
import { useT } from "@/lib/i18n";
import {
  setDispatchToken,
  setDispatchUser,
  isDispatch,
} from "@/lib/dispatchAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DispatchLogin() {
  const { t } = useT();
  const nav = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [remember, setRemember] = useState(true);

  React.useEffect(() => {
    if (isDispatch()) nav("/dispatch-portal", { replace: true });
  }, [nav]);

  const submit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setBusy(true);
    try {
      const r = await axios.post(`${API}/dispatch/login`, {
        email: email.trim().toLowerCase(),
        password,
      });
      setDispatchToken(r.data.token, remember);
      setDispatchUser(r.data.user);
      toast.success(t("Welcome to Dispatch"));
      // iter322-B · honor redirect intent
      const intended = location.state?.continuity?.continueTo
        || location.state?.from
        || "/dispatch-portal";
      if (r.data.must_change_password) {
        nav("/dispatch-portal/change-password", {
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
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-orange-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-orange-300 text-sm font-bold uppercase tracking-wide"
            data-testid="dispatch-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md">
          <AuthRequiredBanner />
          <div className="bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-700 text-white">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-700 font-bold">
                {t("Operations · Fleet Movement")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Dispatch Portal Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            {t("Dispatcher access. Use the credentials issued by Admin.")}
          </p>

          <form onSubmit={submit} className="space-y-4" data-testid="dispatch-login-form">
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
                placeholder="yourname@mascigc.com"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-600"
                data-testid="dispatch-email-input"
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
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-600"
                data-testid="dispatch-password-input"
                toggleTestId="dispatch-password-toggle"
              />
            </div>
            <div className="flex items-center justify-between gap-3 -mt-1">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="w-4 h-4 accent-orange-700"
                  data-testid="dispatch-remember-me"
                />
                <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                  {t("Remember me on this device")}
                </span>
              </label>
              <Link
                to="/dispatch-portal/forgot-password"
                className="text-xs font-bold text-orange-700 hover:text-orange-900 underline-offset-2 hover:underline"
                data-testid="dispatch-forgot-password-link"
              >
                {t("Forgot password?")}
              </Link>
            </div>
            <Button
              type="submit"
              disabled={busy || !email.trim() || !password}
              className="w-full h-12 bg-orange-700 hover:bg-orange-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-orange-900 disabled:opacity-60"
              data-testid="dispatch-login-submit"
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
          <PortalLoginHelp portal="dispatch" />
          </div>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Dispatch Portal")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
