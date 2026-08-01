import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ShieldCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setShopToken } from "@/lib/shopAuth";
import { toast } from "sonner";

/**
 * ShopResetPassword — self-service password reset, step 2.
 *
 * URL: /shop/reset/:token
 * Mirrors PmResetPassword. The token is a 30-min HMAC-signed string
 * emitted by /api/shop/forgot-password. On success we get a fresh
 * per-user shop token and drop straight into /shop.
 */
export default function ShopResetPassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const { token } = useParams();
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (newPw.length < 6) {
      toast.error(t("Password must be at least 6 characters"));
      return;
    }
    if (newPw !== confirmPw) {
      toast.error(t("Passwords don't match"));
      return;
    }
    setSubmitting(true);
    try {
      const r = await api.post("/shop/reset-password", {
        token,
        new_password: newPw,
      });
      if (r.data?.ok && r.data?.token) {
        setShopToken(r.data.token, { remember: true });
        toast.success(t("Password updated — welcome back!"));
        navigate("/shop", { replace: true });
      } else {
        toast.error(t("Reset failed — request a fresh link from /shop/login"));
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("Reset failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalLoginShell
      homeLink="/shop/login"
      headerBorderClass="border-amber-500"
      backHoverClass="hover:text-amber-300"
      backTestId="shop-reset-back"
      rootTestId="shop-reset-page"
      footerLabel={t("MASCI · Shop Use Only")}
    >
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700">
                {t("Self-service reset")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1" data-testid="shop-reset-title">
                {t("Choose a new password")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mb-6">{t("Pick something at least 6 characters.")}</p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="shop-reset-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("New password (6+ characters)")}
              </Label>
              <PasswordInput
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                autoFocus
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
                data-testid="shop-reset-new"
                toggleTestId="shop-reset-new-toggle"
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
                data-testid="shop-reset-confirm"
                toggleTestId="shop-reset-confirm-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-amber-800"
              data-testid="shop-reset-submit"
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
    </PortalLoginShell>
  );
}
