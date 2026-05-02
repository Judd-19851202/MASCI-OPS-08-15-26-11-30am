import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Wrench, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { JuddGroupAttribution } from "@/components/JuddGroupAttribution";
import { api } from "@/lib/api";
import { setShopToken, clearShopToken } from "@/lib/shopAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

export default function ShopLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useT();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Clear every tier's token on arrival so a shop user never inherits
    // a ghost Admin/PM session from a previously logged-in teammate.
    clearShopToken();
    clearAdminToken();
    clearPmToken();
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error(t("Enter the shop password"));
      return;
    }
    setSubmitting(true);
    clearShopToken();
    clearAdminToken();
    clearPmToken();
    try {
      const res = await api.post("/shop/login", { password, _t: Date.now() }, {
        timeout: 90000, // backend cold-start on Atlas can take up to 60s
      });
      if (res?.data?.ok && res?.data?.token) {
        setShopToken(res.data.token);
        toast.success(t("Welcome to the Shop"));
        const from = location.state?.from || "/shop";
        navigate(from, { replace: true });
      } else {
        toast.error(t("Login failed — server didn't return a token"));
      }
    } catch (err) {
      const status = err?.response?.status;
      let msg;
      if (status === 401) {
        msg = t("Wrong password");
      } else if (status >= 520 && status <= 524) {
        msg = t("Server is waking up — give it ~60 seconds and try again");
      } else if (status >= 500 && status < 600) {
        msg = `${t("Server error")} (${status}) — ${t("try again in a moment")}`;
      } else if (err?.code === "ECONNABORTED" || /timeout/i.test(err?.message || "")) {
        msg = t("Request timed out — server is cold-starting, try again");
      } else if (!err?.response) {
        msg = t("Can't reach server — check your internet");
      } else {
        msg = `${t("Login failed")} (${status || "unknown"})`;
      }
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
            data-testid="shop-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
          </Link>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <span className="hidden sm:inline-block w-20" />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700">
                {t("Mechanics & Shop")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Shop Sign In")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            {t("Sign in to review every Pre-Op inspection, sign off on Out-of-Service and Needs-Attention items, and keep the fleet running.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="shop-login-form">
            <div>
              <Label htmlFor="shop-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Shop Password")}
              </Label>
              <PasswordInput
                id="shop-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="shop-password-input"
                toggleTestId="shop-password-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-amber-800"
              data-testid="shop-login-submit"
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
          MASCI · {t("Shop Use Only")}
        </div>
        <JuddGroupAttribution variant="login" />
      </footer>
    </div>
  );
}
