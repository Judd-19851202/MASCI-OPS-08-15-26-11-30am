// Dispatch Portal sign-in. Mirrors HrLogin / ShopLogin chrome. Cyan
// accent. Posts to /api/dispatch/login and stores the token via
// dispatchAuth.setDispatchToken so the rest of the portal can hit
// /api/dispatch/* with `X-Safety-Token` headers.
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Loader2, Truck, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
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
        email: email.trim(),
        password,
      });
      setDispatchToken(r.data.token, remember);
      setDispatchUser(r.data.user);
      toast.success(t("Welcome to Dispatch"));
      if (r.data.must_change_password) {
        nav("/dispatch-portal/change-password", { replace: true });
      } else {
        nav("/dispatch-portal", { replace: true });
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
            data-testid="safety-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="lg" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-700 text-white">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-700">
                {t("Operations · Fleet Movement")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Dispatch Portal Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            {t(
              "Dispatcher access. Use the credentials issued by Admin."
            )}
          </p>

          <form onSubmit={submit} className="space-y-4" data-testid="safety-login-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Email")}
              </Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                autoComplete="username"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-600"
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
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-600"
                data-testid="safety-login-password"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="w-4 h-4 rounded border-slate-400"
              />
              {t("Keep me signed in on this device")}
            </label>
            <Button
              type="submit"
              disabled={busy || !email.trim() || !password}
              className="w-full h-12 bg-orange-700 hover:bg-orange-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-orange-900 disabled:opacity-60"
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
            <div className="text-center">
              <Link
                to="/dispatch-portal/forgot-password"
                className="text-xs font-mono uppercase tracking-[0.18em] text-orange-700 hover:underline"
                data-testid="safety-forgot-link"
              >
                {t("Forgot password?")}
              </Link>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
