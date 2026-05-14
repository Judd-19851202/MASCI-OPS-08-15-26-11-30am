import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ShieldCheck, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setShopToken, clearShopToken } from "@/lib/shopAuth";
import { toast } from "sonner";

/**
 * ShopChangePassword — first-login + admin-reset rotation page for shop users.
 *
 * Lives at /shop/change-password. Reachable two ways:
 *   1. Login flow detects must_change_password=true and redirects here.
 *   2. Shop user clicks "Change my password" from the Shop hub (future).
 *
 * On success swaps the stored token for the freshly-issued one and
 * bounces back to the page they were originally trying to reach
 * (state.from), defaulting to /shop.
 */
export default function ShopChangePassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const location = useLocation();
  const originalFrom = location.state?.from || "/shop";
  const [me, setMe] = useState(null);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/shop/me");
        if (!alive) return;
        if (r.data?.is_legacy) {
          // Legacy shared-password / open-mode session — no per-user account to rotate.
          toast.error(t("Only per-user accounts can change password here"));
          navigate("/shop", { replace: true });
          return;
        }
        setMe(r.data?.user || null);
      } catch {
        clearShopToken();
        navigate("/shop/login", { replace: true });
      }
    })();
    return () => {
      alive = false;
    };
  }, [navigate, t]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (newPw.length < 6) {
      toast.error(t("New password must be at least 6 characters"));
      return;
    }
    if (newPw !== confirmPw) {
      toast.error(t("Passwords don't match"));
      return;
    }
    if (newPw === oldPw) {
      toast.error(t("New password must be different from the old one"));
      return;
    }
    setSubmitting(true);
    try {
      const r = await api.post("/shop/change-password", {
        old_password: oldPw,
        new_password: newPw,
      });
      if (r.data?.ok && r.data?.token) {
        setShopToken(r.data.token, { remember: true });
        toast.success(t("Password updated"));
        navigate(originalFrom, { replace: true });
      } else {
        toast.error(t("Update failed"));
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("Update failed"));
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
            to="/shop"
            className="inline-flex items-center text-white hover:text-amber-300 text-sm font-bold uppercase tracking-wide"
            data-testid="shop-change-pw-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Shop")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/shop" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/shop" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700">
                {t("Mechanics & Shop")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Choose your password")}
              </h1>
            </div>
          </div>
          {me && (
            <p className="text-slate-600 text-sm mb-1">
              {t("Signed in as")}{" "}
              <span className="font-mono text-slate-900 font-bold">{me.email}</span>
            </p>
          )}
          <p className="text-slate-600 text-sm mb-6">
            {t("Pick something at least 6 characters. The temporary password the admin issued will stop working as soon as you save.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="shop-change-pw-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Current (or temporary) password")}
              </Label>
              <PasswordInput
                value={oldPw}
                onChange={(e) => setOldPw(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="shop-change-pw-old"
                toggleTestId="shop-change-pw-old-toggle"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("New password (6+ characters)")}
              </Label>
              <PasswordInput
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="shop-change-pw-new"
                toggleTestId="shop-change-pw-new-toggle"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Confirm new password")}
              </Label>
              <PasswordInput
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="shop-change-pw-confirm"
                toggleTestId="shop-change-pw-confirm-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-amber-800"
              data-testid="shop-change-pw-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Saving…")}
                </>
              ) : (
                t("Save new password")
              )}
            </Button>
          </form>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          MASCI · {t("Shop Use Only")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
