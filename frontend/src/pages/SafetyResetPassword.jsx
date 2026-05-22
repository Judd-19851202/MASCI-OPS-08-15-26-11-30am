// SafetyResetPassword — completes the forgot-password flow. The user
// lands here via /safety-portal/reset/:token email link. Posts new
// password + token to /api/safety/reset-password, then drops them
// straight into the portal with a fresh session token.
import React, { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import axios from "axios";
import { ShieldCheck, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { setSafetyToken, setSafetyUser } from "@/lib/safetyAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SafetyResetPassword() {
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
      const r = await axios.post(`${API}/safety/reset-password`, {
        token,
        new_password: newPw,
      });
      if (r.data?.ok && r.data?.token) {
        setSafetyToken(r.data.token, true);
        setSafetyUser(r.data.user || {});
        toast.success(t("Password reset successful"));
        navigate("/safety-portal", { replace: true });
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
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/safety-portal/login"
            className="inline-flex items-center text-white hover:text-cyan-300 text-sm font-bold uppercase tracking-wide"
            data-testid="safety-reset-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Safety Login")}
          </Link>
          <MasciLogo variant="mark" size="lg" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-cyan-700 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700">
                {t("Safety Operations")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                {t("Reset your password")}
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mb-6">
            {t("Pick a new password to finish signing in.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="safety-reset-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("New password (8+ characters)")}
              </Label>
              <PasswordInput
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                autoFocus
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700"
                data-testid="safety-reset-new"
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
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700"
                data-testid="safety-reset-confirm"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-cyan-900"
              data-testid="safety-reset-submit"
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
      </main>
    </div>
  );
}
