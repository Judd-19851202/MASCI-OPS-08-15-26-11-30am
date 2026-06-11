import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ShieldCheck, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import PortalContextBanner from "@/components/PortalContextBanner";
import { api } from "@/lib/api";
import { setSafetyFormsToken, clearSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

export default function SafetyFormsLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useT();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  useEffect(() => {
    clearSafetyFormsToken();
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error(t("Enter the password"));
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post(
        "/safety-forms/login",
        { password, _t: Date.now() },
        { timeout: 90000 }
      );
      if (res?.data?.ok && res?.data?.token) {
        setSafetyFormsToken(res.data.token, { remember: rememberMe });
        toast.success(t("Welcome to Safety Forms"));
        const from = location.state?.from || "/safety/forms";
        navigate(from, { replace: true });
      } else {
        toast.error(t("Login failed"));
      }
    } catch (err) {
      const status = err?.response?.status;
      if (status === 401) toast.error(t("Wrong password"));
      else toast.error(t("Login failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/safety"
            className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="safety-forms-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Safety")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-5 sm:px-8 py-12">
        {/* iter322 · continuity banner when arriving from another
            portal via `?from=<key>`. Zero footprint when absent. */}
        <div className="w-full max-w-md">
          <PortalContextBanner currentLabel={t("Safety Forms · Sign-in required")} />
        </div>
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700">
                {t("Safety Department")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Safety Forms")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-3">
            {t("Equipment Issuance and Use & Care Training. Password-gated for the Safety Department.")}
          </p>
          {/* iter323 · Safety Portal ownership notice — primary path is
              now Safety Portal sign-in. Legacy password kept for
              backwards compatibility (field bookmarks / automation). */}
          <div
            className="mb-5 rounded-md border border-slate-200 border-l-4 border-l-cyan-700 bg-cyan-50/60 p-3"
            data-testid="safety-forms-portal-notice"
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-800 font-bold">
              {t("Safety Portal Ownership")}
            </div>
            <p className="text-xs text-slate-700 mt-1">
              {t("Safety Forms are now owned by the Safety Portal. Sign in there for the full review experience.")}{" "}
              <Link
                to="/safety-portal/login?from=safety-forms"
                className="font-bold text-cyan-800 underline"
                data-testid="safety-forms-portal-cta"
              >
                {t("Go to Safety Portal sign-in →")}
              </Link>
            </p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="safety-forms-login-form">
            <div>
              <Label htmlFor="sf-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Password")}
              </Label>
              <PasswordInput
                id="sf-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                data-testid="safety-forms-password-input"
                toggleTestId="safety-forms-password-toggle"
              />
            </div>
            <label className="inline-flex items-center gap-2 cursor-pointer select-none -mt-1">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 accent-red-700"
                data-testid="safety-forms-remember-me"
              />
              <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                {t("Remember me on this device")}
              </span>
            </label>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="safety-forms-login-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Verifying…")}
                </>
              ) : (
                <>{t("Sign In")}</>
              )}
            </Button>
          </form>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          MASCI · {t("Safety Department")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
