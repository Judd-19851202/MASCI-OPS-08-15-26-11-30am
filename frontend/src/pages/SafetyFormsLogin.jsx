import React, { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ShieldCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { PasswordInput } from "@/components/PasswordInput";
import PortalLoginShell from "@/components/PortalLoginShell";
import PortalContextBanner from "@/components/PortalContextBanner";
import { api } from "@/lib/api";
import { setSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

export default function SafetyFormsLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useT();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

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
    <PortalLoginShell
      portalLabel={t("Safety Forms")}
      title={t("Safety Forms")}
      subtitle={t("Protected entry for safety-issued forms and training workflows.")}
      homeLink="/safety"
      homeLabel={t("Safety")}
      headerBorderClass="border-red-700"
      footerLabel={t("MASCI · Safety Department")}
      rootTestId="safety-forms-login-page"
    >
      <div className="flex flex-col items-center justify-center">
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
              <h1 className="field-glance-anchor font-display text-2xl font-black text-slate-900 leading-none mt-1" data-testid="safety-forms-login-title">
                {t("Safety Forms")}
              </h1>
            </div>
          </div>

          <div
            className="mb-5 rounded-md border border-slate-200 border-l-4 border-l-cyan-700 bg-cyan-50/60 p-3"
            data-testid="safety-forms-portal-notice"
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-800 font-bold">
              {t("Primary sign-in")}
            </div>
            <p className="text-xs text-slate-700 mt-1">
              {t("Safety Operations owns the full review flow.")} {" "}
              <Link
                to="/safety-portal/login?from=safety-forms"
                className="font-bold text-cyan-800 underline"
                data-testid="safety-forms-portal-cta"
              >
                {t("Use Safety Operations sign-in →")}
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
                className="mt-2"
                data-testid="safety-forms-password-input"
                toggleTestId="safety-forms-password-toggle"
              />
            </div>

            <label className="inline-flex items-center gap-3 cursor-pointer select-none -mt-1">
              <Checkbox
                checked={rememberMe}
                onCheckedChange={(value) => setRememberMe(Boolean(value))}
                data-testid="safety-forms-remember-me"
              />
              <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                {t("Remember me on this device")}
              </span>
            </label>

            <Button
              type="submit"
              disabled={submitting}
              aria-busy={submitting}
              className="w-full"
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
      </div>
    </PortalLoginShell>
  );
}