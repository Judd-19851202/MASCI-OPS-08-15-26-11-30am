import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { useT } from "@/lib/i18n";
import { HelpTipBlock } from "@/components/HelpTip";
import { api } from "@/lib/api";
import { setFlToken, getFlUser } from "@/lib/flAuth";
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
    <div className="min-h-screen bg-slate-50 flex flex-col" data-testid="fl-portal-change-password">
      <div className="max-w-md mx-auto w-full px-4 py-10 flex-1">
        <div className="flex flex-col items-center mb-6">
          <MasciLogo size={48} />
          <h1 className="mt-3 text-xl font-bold text-slate-900">
            {t("Set your password")}
          </h1>
          <p className="mt-1 text-xs text-slate-600 text-center">
            {user?.name ? `${user.name} · ${user.role || ""}` : t("Field Leadership Portal")}
          </p>
        </div>
        <form onSubmit={submit} className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
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
            className="w-full bg-slate-800 hover:bg-slate-900 text-white"
          >
            {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <KeyRound className="w-4 h-4 mr-2" />}
            {t("Set password")}
          </Button>
        </form>
      </div>
      <ForgedOpsAttribution />
    </div>
  );
}
