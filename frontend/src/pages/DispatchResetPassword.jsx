// DispatchResetPassword — completes the forgot-password flow. Orange
// accent. Clones SafetyResetPassword.
import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { Truck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { useT } from "@/lib/i18n";
import { setDispatchToken, setDispatchUser } from "@/lib/dispatchAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DispatchResetPassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const { token } = useParams();
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (newPw.length < 8) {
      toast.error(t("Password must be at least 8 characters"));
      return;
    }
    if (newPw !== confirmPw) {
      toast.error(t("Passwords don't match"));
      return;
    }
    setSubmitting(true);
    try {
      const r = await axios.post(`${API}/dispatch/reset-password`, {
        token,
        new_password: newPw,
      });
      if (r.data?.ok && r.data?.token) {
        setDispatchToken(r.data.token, true);
        setDispatchUser(r.data.user || {});
        toast.success(t("Password reset successful"));
        navigate("/dispatch-portal", { replace: true });
      } else {
        toast.error(t("Reset failed"));
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(
        typeof detail === "string"
          ? detail
          : t("This reset link is invalid or has expired."),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalLoginShell
      homeLink="/dispatch-portal/login"
      headerBorderClass="border-orange-700"
      backHoverClass="hover:text-orange-300"
      backTestId="dispatch-reset-back"
      rootTestId="dispatch-reset-page"
      footerLabel={t("MASCI · Dispatch")}
    >
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-700 text-white">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-700 font-bold">
                {t("Operations · Fleet Movement")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1" data-testid="dispatch-reset-title">
                {t("Reset your password")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mb-6">
            {t("Pick a new password to finish signing in.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="dispatch-reset-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("New password (8+ characters)")}
              </Label>
              <PasswordInput
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                autoFocus
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-700"
                data-testid="dispatch-reset-new"
                toggleTestId="dispatch-reset-new-toggle"
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
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-700"
                data-testid="dispatch-reset-confirm"
                toggleTestId="dispatch-reset-confirm-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-orange-700 hover:bg-orange-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-orange-900"
              data-testid="dispatch-reset-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Saving…")}
                </>
              ) : (
                t("Save password & sign in")
              )}
            </Button>
          </form>
      </div>
    </PortalLoginShell>
  );
}
