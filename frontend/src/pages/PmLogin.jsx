import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Briefcase, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setPmToken, clearPmToken } from "@/lib/pmAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { toast } from "sonner";

export default function PmLogin() {
  const { t } = useT();
  const navigate = useNavigate();
  const location = useLocation();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Clear every tier's token on arrival so a PM never inherits a ghost
    // Admin/Shop session from whoever used this browser before them.
    clearPmToken();
    clearAdminToken();
    clearShopToken();
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error(t("Enter the PM password"));
      return;
    }
    setSubmitting(true);
    clearPmToken();
    clearAdminToken();
    clearShopToken();
    try {
      const res = await api.post(
        "/pm/login",
        { password, _t: Date.now() },
        { timeout: 90000 }
      );
      if (res?.data?.ok && res?.data?.token) {
        setPmToken(res.data.token);
        toast.success(t("Welcome, PM"));
        const from = location.state?.from || "/pm";
        navigate(from, { replace: true });
      } else {
        toast.error(t("Login failed — server didn't return a token"));
      }
    } catch (err) {
      const status = err?.response?.status;
      let msg;
      if (status === 401) msg = t("Wrong password");
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
            {t("Project-manager workspace — every record, every form, every master list. Backup / restore controls live in the Admin Console only.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="pm-login-form">
            <div>
              <Label
                htmlFor="pm-password"
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700"
              >
                {t("PM Password")}
              </Label>
              <PasswordInput
                id="pm-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="pm-password-input"
                toggleTestId="pm-password-toggle"
              />
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
          </form>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Project Management Portal")}
        </div>
        <JuddGroupAttribution variant="login" />
      </footer>
    </div>
  );
}
