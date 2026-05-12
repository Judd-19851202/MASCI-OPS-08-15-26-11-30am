import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Loader2, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { setHrToken, setHrUser } from "@/lib/hrAuth";
import { MasciLogo } from "@/components/MasciLogo";
import { useT } from "@/lib/i18n";

export default function HrResetPassword() {
  const { t } = useT();
  const nav = useNavigate();
  const { token } = useParams();
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    if (!next || next.length < 8) return toast.error(t("Password must be at least 8 characters"));
    if (next !== confirm) return toast.error(t("Passwords do not match"));
    setBusy(true);
    try {
      const r = await api.post(`/hr/reset/${token}`, { new_password: next });
      setHrToken(r.data.token, true);
      setHrUser(r.data.user);
      toast.success(t("Password reset successful"));
      nav("/hr");
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Reset link is invalid or expired"));
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
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-purple-700">{t("HR Portal · Reset")}</div>
        <h1 className="font-display text-3xl font-black mt-1 mb-1">{t("Reset Password")}</h1>
        <p className="text-sm text-slate-600 mb-6">{t("Pick a new password to finish signing in.")}</p>
        <Card className="p-6">
          <form onSubmit={submit} className="space-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("New password")}</Label>
              <Input type="password" value={next} onChange={(e) => setNext(e.target.value)} data-testid="hr-reset-new" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Confirm new password")}</Label>
              <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} data-testid="hr-reset-confirm" />
            </div>
            <Button type="submit" disabled={busy} className="w-full bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-reset-submit">
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <KeyRound className="w-4 h-4 mr-2" />}
              {t("Reset Password")}
            </Button>
          </form>
        </Card>
      </main>
    </div>
  );
}
