import React, { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ShieldCheck, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setHrToken, setHrUser } from "@/lib/hrAuth";
import { toast } from "sonner";

/**
 * HrResetPassword — self-service password reset, step 2.
 *
 * URL: /hr/reset/:token
 * The user lands here from the email link sent by /api/hr/forgot-password.
 * They pick a new password + confirm and we POST to /api/hr/reset/{token}.
 * On success we get a fresh per-HR session token and drop straight into /hr.
 *
 * Mirrors PmResetPassword.jsx exactly — purple accent instead of amber.
 */
export default function HrResetPassword() {
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
      const r = await api.post(`/hr/reset/${token}`, { new_password: newPw });
      if (r.data?.ok && r.data?.token) {
        // Self-service reset implies the user has the email + just
        // chose the new password → presumably their own device.
        setHrToken(r.data.token, true);
        setHrUser(r.data.user || {});
        toast.success(t("Password reset successful"));
        navigate("/hr", { replace: true });
      } else {
        toast.error(t("Reset failed"));
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(
        typeof detail === "string"
          ? detail
          : t("This reset link is invalid or has expired. Request a new one from the HR login page.")
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-purple-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/hr/login"
            className="inline-flex items-center text-white hover:text-purple-300 text-sm font-bold uppercase tracking-wide"
            data-testid="hr-reset-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("HR Login")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-purple-700 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-purple-700">
                {t("Human Resources")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Reset your password")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mb-6">
            {t("Pick a new password to finish signing in. You'll be dropped straight into the HR portal once saved.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="hr-reset-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("New password (8+ characters)")}
              </Label>
              <PasswordInput
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                autoFocus
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700"
                data-testid="hr-reset-new"
                toggleTestId="hr-reset-new-toggle"
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
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700"
                data-testid="hr-reset-confirm"
                toggleTestId="hr-reset-confirm-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-purple-700 hover:bg-purple-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-purple-900"
              data-testid="hr-reset-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Saving…")}
                </>
              ) : (
                t("Save password &amp; sign in")
              )}
            </Button>
          </form>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Human Resources Portal")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
