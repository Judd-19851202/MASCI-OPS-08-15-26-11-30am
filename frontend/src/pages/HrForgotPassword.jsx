import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, Mail, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { MasciLogo } from "@/components/MasciLogo";
import { useT } from "@/lib/i18n";

export default function HrForgotPassword() {
  const { t } = useT();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    if (!email) return toast.error(t("Email required"));
    setBusy(true);
    try {
      await api.post("/hr/forgot-password", { email: email.trim() });
      setSent(true);
    } catch {
      // Endpoint always returns 200 for security — only network errors hit here.
      setSent(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-purple-700">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
        </div>
      </header>
      <main className="max-w-md mx-auto px-5 py-10">
        <Link to="/hr/login" className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-purple-700 font-bold mb-6">
          <ArrowLeft className="w-3.5 h-3.5" /> {t("Back to sign in")}
        </Link>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-purple-700">{t("HR Portal · Forgot")}</div>
        <h1 className="font-display text-3xl font-black mt-1 mb-1">{t("Reset your password")}</h1>
        <p className="text-sm text-slate-600 mb-6">{t("Enter your email and we'll send a reset link.")}</p>
        <Card className="p-6">
          {sent ? (
            <div className="text-center py-4">
              <Mail className="w-10 h-10 mx-auto text-purple-700 mb-3" />
              <div className="font-bold text-base text-slate-900">{t("Check your inbox")}</div>
              <p className="text-sm text-slate-600 mt-2">
                {t("If an HR account exists for that email, a reset link is on its way. The link expires in 30 minutes.")}
              </p>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Email")}</Label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" data-testid="hr-forgot-email" />
              </div>
              <Button type="submit" disabled={busy} className="w-full bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-forgot-submit">
                {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Mail className="w-4 h-4 mr-2" />}
                {t("Send Reset Link")}
              </Button>
            </form>
          )}
        </Card>
      </main>
    </div>
  );
}
