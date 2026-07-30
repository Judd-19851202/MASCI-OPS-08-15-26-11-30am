import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, KeyRound, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { useT } from "@/lib/i18n";
import { HelpTipBlock } from "@/components/HelpTip";
import { api } from "@/lib/api";
import { setFlToken, getFlUser } from "@/lib/flAuth";
import { setMustChange } from "@/lib/mustChangePassword";
import { toast } from "sonner";

/**
 * FieldLeadershipPortalChangePassword (iter314)
 *
 * Required after first login (must_change_password=true) or anytime
 * the user wants to change their password.
 */
export default function FieldLeadershipPortalChangePassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const user = getFlUser();
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (newPw.length < 8) {
      toast.error(t("New password must be at least 8 characters"));
      return;
    }
    if (newPw !== confirmPw) {
      toast.error(t("Passwords do not match"));
      return;
    }
    setSubmitting(true);
    try {
      const body = { new_password: newPw };
      if (currentPw) body.current_password = currentPw;
      const r = await api.post("/field-leadership/portal/change-password", body);
      const tok = r?.data?.token;
      if (tok) setFlToken(tok, true);
      setMustChange("fl", false);
      setMustChange("field_leadership", false);
      toast.success(t("Password updated"));
      navigate("/field-leadership/portal/dashboard", { replace: true });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("Could not change password"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalLoginShell
      headerBorderClass="border-red-700"
      backHoverClass="hover:text-red-300"
      backTestId="fl-change-password-back"
      rootTestId="fl-portal-change-password"
      footerLabel={t("MASCI · Field Leadership Portal")}
      homeLink="/leadership"
    >
        <form onSubmit={submit} className="bg-white border border-slate-200 rounded-lg p-5 sm:p-7 shadow-xl space-y-4">
          <div className="flex items-center gap-3 mb-1">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white shrink-0">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                {t("Field Leadership")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Set your password")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm">
            {user?.name ? `${user.name}${user.role ? ` · ${user.role}` : ""}` : t("Field Leadership Portal")}
          </p>
          <HelpTipBlock formKey="field-leadership.change-password" />
          <div>
            <Label className="text-xs uppercase tracking-wider text-slate-600">
              {t("Current temporary password")}
            </Label>
            <PasswordInput
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
              data-testid="fl-cp-current"
              autoComplete="current-password"
              disabled={submitting}
            />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-wider text-slate-600">
              {t("New password (min 8 chars)")}
            </Label>
            <PasswordInput
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              data-testid="fl-cp-new"
              autoComplete="new-password"
              disabled={submitting}
            />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-wider text-slate-600">
              {t("Confirm new password")}
            </Label>
            <PasswordInput
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              data-testid="fl-cp-confirm"
              autoComplete="new-password"
              disabled={submitting}
            />
          </div>
          <Button
            type="submit" disabled={submitting}
            data-testid="fl-cp-submit"
            className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
          >
            {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <KeyRound className="w-4 h-4 mr-2" />}
            {t("Set password")}
          </Button>
        </form>
    </PortalLoginShell>
  );
}
