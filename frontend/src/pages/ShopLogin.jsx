import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Wrench, Loader2, ArrowLeft, Mail, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { PortalLoginHelp } from "@/components/PortalLoginHelp";
import { AuthRequiredBanner } from "@/components/PortalContextBanner";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { api } from "@/lib/api";
import { setShopToken, clearShopToken, isShop } from "@/lib/shopAuth";
import { attemptSsoUpgrade } from "@/lib/attemptSsoUpgrade";
import { clearAdminToken, setAdminToken, isAdmin } from "@/lib/adminAuth";
import { useRedirectIfDirectoryGrant } from "@/lib/useRedirectIfDirectoryGrant";
import { clearPmToken } from "@/lib/pmAuth";
import { toast } from "sonner";
import { setMustChange } from "@/lib/mustChangePassword";
import { useT } from "@/lib/i18n";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function ShopLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useT();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotBusy, setForgotBusy] = useState(false);

  useEffect(() => {
    // Iter88 — Removed mount-time token wipe. See AdminLogin.jsx rationale.
  }, []);

  // TRACK 14.0-SSO · Auto-forward if directory grants Shop.
  // Track 15.13A · destination is dynamic — once login fires and the
  // ShopLogin onSubmit writes `masci.is_asset_admin=true` to localStorage,
  // this hook re-evaluates (deps on hasToken) and must honor the asset
  // admin landing to avoid racing past our /shop/asset-care navigate.
  const _isAssetAdminLanding =
    typeof window !== "undefined" &&
    window.localStorage.getItem("masci.is_asset_admin") === "true";
  useRedirectIfDirectoryGrant(
    "shop",
    isShop() || isAdmin(),
    _isAssetAdminLanding ? "/shop/asset-care" : "/shop",
  );

  const submitForgot = async () => {
    const e = (forgotEmail || "").trim();
    if (!e) return;
    setForgotBusy(true);
    try {
      const res = await api.post("/shop/forgot-password", { email: e.toLowerCase() });
      // Backend always returns ok:true with a generic message — no email enumeration.
      toast.success(
        res?.data?.message ||
          t("If that email is on file, a reset link is on its way.")
      );
      setForgotOpen(false);
    } catch (err) {
      const status = err?.response?.status;
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
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      toast.error(t("Enter your work email"));
      return;
    }
    if (!password) {
      toast.error(t("Enter your password"));
      return;
    }
    setSubmitting(true);
    // Iter88 — Removed pre-submit token wipe. setShopToken below replaces
    // the shop slot atomically; other portal tokens are left intact.
    try {
      const payload = { email: cleanEmail, password, _t: Date.now() };
      const res = await api.post("/shop/login", payload, {
        timeout: 90000, // backend cold-start on Atlas can take up to 60s
      });
      if (res?.data?.ok && res?.data?.token) {
        const kind = res?.data?.kind || "shop";
        // iter346-B · universal super-admin fallback.
        if (kind === "admin") {
          setAdminToken(res.data.token, { remember: rememberMe });
          const name = res.data?.user?.name;
          toast.success(name ? `${t("Welcome,")} ${name}` : t("Welcome, Admin"));
          navigate("/admin", { replace: true });
          return;
        }
        setShopToken(res.data.token, { remember: rememberMe });
        // TRACK 23.9A — SSO upgrade: silently establish master session
        // + fan out every portal token the directory grants this user.
        try { await attemptSsoUpgrade(email.trim().toLowerCase(), password, rememberMe); } catch { /* no-op */ }
        // Track 15.13A — Asset Care landing. When the shop user is
        // also flagged `is_asset_admin` on the canonical directory row,
        // backend mirrors that into the shop_login response. Send the
        // user to /shop/asset-care so they land where the asset work
        // lives (`landingFor()` already returns the right route, but it
        // expects a directory-user shape; we honor the mirror here in
        // a single-line addition so non-asset shop users are unaffected).
        const isAssetAdmin =
          res.data?.is_asset_admin === true ||
          res.data?.user?.is_asset_admin === true;
        try {
          if (isAssetAdmin) {
            window.localStorage.setItem("masci.is_asset_admin", "true");
          }
        } catch (_e) { /* ignore storage errors */ }
        const intended =
          location.state?.from || (isAssetAdmin ? "/shop/asset-care" : "/shop");
        // Track 15.14A Layer 2 — persist must-change-password flag.
        const mustChange = !!res.data.must_change_password;
        setMustChange("shop", mustChange);
        if (mustChange) {
          toast.success(t("Password rotation required — pick a new one"));
          navigate("/shop/change-password", {
            replace: true,
            state: { from: intended },
          });
        } else {
          toast.success(
            isAssetAdmin ? t("Welcome to Asset Care") : t("Welcome to the Shop")
          );
          navigate(intended, { replace: true });
        }
      } else {
        toast.error(t("Login failed — server didn't return a token"));
      }
    } catch (err) {
      const status = err?.response?.status;
      let msg;
      if (status === 401) {
        msg = t("Wrong email or password");
      } else if (status === 403) {
        msg = err?.response?.data?.detail || t("Access blocked");
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
    <PortalLoginShell
      headerBorderClass="border-amber-500"
      backHoverClass="hover:text-amber-300"
      backTestId="shop-login-back"
      rootTestId="shop-portal-login"
      footerLabel={<>MASCI · {t("Shop Use Only")}</>}
      dialogs={
        <Dialog open={forgotOpen} onOpenChange={setForgotOpen}>
          <DialogContent data-testid="shop-forgot-dialog">
            <DialogHeader>
              <DialogTitle className="font-display font-black flex items-center gap-2 text-orange-700">
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
                  placeholder="yourname@yourcompany.com"
                  className="h-11 pl-9 text-base border-2 border-slate-300"
                  data-testid="shop-forgot-email-input"
                  autoFocus
                />
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => setForgotOpen(false)}
                disabled={forgotBusy}
                data-testid="shop-forgot-cancel"
              >
                {t("Cancel")}
              </Button>
              <Button
                onClick={submitForgot}
                disabled={forgotBusy || !forgotEmail.trim()}
                className="bg-orange-600 hover:bg-orange-700 text-white font-bold uppercase tracking-wide"
                data-testid="shop-forgot-submit"
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
      }
    >
      <AuthRequiredBanner />
      <div className="bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
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
            {t("Sign in with the account the admin issued you. First-time users will be prompted to set their own password after entering the temporary one from their welcome email.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="shop-login-form">
            <div>
              <Label htmlFor="shop-email" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Work email")}
              </Label>
              <Input
                id="shop-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                placeholder="shop-manager@yourcompany.com"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="shop-email-input"
              />
            </div>
            <div>
              <Label htmlFor="shop-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Password")}
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
            <div className="flex items-center justify-between flex-wrap gap-2 -mt-1">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 accent-amber-600"
                  data-testid="shop-remember-me"
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
                className="inline-flex items-center min-h-[44px] px-1 -mx-1 text-xs font-bold text-orange-700 hover:text-orange-900 underline-offset-2 hover:underline"
                data-testid="shop-forgot-password-link"
              >
                {t("Forgot password?")}
              </button>
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
          <PortalLoginHelp portal="shop" />
          </div>
    </PortalLoginShell>
  );
}
