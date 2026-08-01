// SafetyForgotPassword — request a reset link.
// Posts /api/safety/forgot-password and tells the user to check their
// email. Preview reset artifacts must not appear in the operator-facing UI.
import React, { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { ShieldAlert, Loader2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { useT } from "@/lib/i18n";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SafetyForgotPassword() {
  const { t } = useT();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    try {
      const r = await axios.post(`${API}/safety/forgot-password`, {
        email: email.trim(),
      });
      setDone(true);
    } catch {
      // Backend always returns ok shape — surface a generic message.
      setDone(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <PortalLoginShell
      homeLink="/safety-portal/login"
      headerBorderClass="border-cyan-700"
      backHoverClass="hover:text-cyan-300"
      backTestId="safety-forgot-back"
      rootTestId="safety-forgot-page"
      footerLabel={t("MASCI · Safety Operations")}
    >
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-cyan-700 text-white">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-cyan-700">
                {t("Safety Operations")}
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1" data-testid="safety-forgot-title">
                {t("Forgot password")}
              </h1>
            </div>
          </div>

          {done ? (
            <div className="space-y-4">
              <div className="flex items-start gap-2 bg-emerald-50 border-2 border-emerald-200 rounded-md p-4 text-sm text-emerald-900">
                <Check className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  {t("If this email belongs to a Safety user, a reset link is on its way. The link expires in 30 minutes.")}
                </div>
              </div>
              <Link
                to="/safety-portal/login"
                className="block text-center text-xs font-mono uppercase tracking-[0.18em] text-cyan-700 hover:underline"
                data-testid="safety-forgot-return-link"
              >
                {t("Back to sign in")} →
              </Link>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4" data-testid="safety-forgot-form">
              <p className="text-slate-600 text-sm">{t("Enter your Safety Portal email.")}</p>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                  {t("Email")}
                </Label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                  className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700"
                  data-testid="safety-forgot-email"
                />
              </div>
              <Button
                type="submit"
                disabled={busy || !email.trim()}
                className="w-full h-12 bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-cyan-900 disabled:opacity-60"
                data-testid="safety-forgot-submit"
              >
                {busy ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Sending…")}
                  </>
                ) : (
                  t("Send reset link")
                )}
              </Button>
            </form>
          )}
      </div>
    </PortalLoginShell>
  );
}
