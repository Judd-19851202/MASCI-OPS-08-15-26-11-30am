import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Loader2, ShieldCheck, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { setHrToken, setHrUser } from "@/lib/hrAuth";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

export default function HrLogin() {
  const { t } = useT();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    if (!email || !password) return toast.error(t("Email and password required"));
    setBusy(true);
    try {
      const r = await api.post("/hr/login", { email: email.trim(), password });
      setHrToken(r.data.token, remember);
      setHrUser(r.data.user);
      if (r.data.must_change_password) {
        toast.info(t("Please change your temporary password."));
        nav("/hr/change-password");
      } else {
        nav("/hr");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Login failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-purple-700">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>
      <main className="max-w-md mx-auto px-5 py-10">
        <Link to="/" className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-purple-700 font-bold mb-6">
          <ArrowLeft className="w-3.5 h-3.5" /> {t("Hub")}
        </Link>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-purple-700">{t("Restricted · HR Portal")}</div>
        <h1 className="font-display text-3xl font-black mt-1 mb-1">{t("HR Portal Sign-In")}</h1>
        <p className="text-sm text-slate-600 mb-6">{t("Employee records · accountability · payroll-time verification")}</p>
        <Card className="p-6">
          <form onSubmit={submit} className="space-y-4">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Email")}</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" data-testid="hr-login-email" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Password")}</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" data-testid="hr-login-password" />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} data-testid="hr-login-remember" />
              {t("Remember me on this device")}
            </label>
            <Button type="submit" disabled={busy} className="w-full bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-login-submit">
              {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <ShieldCheck className="w-4 h-4 mr-2" />}
              {t("Sign In")}
            </Button>
            <div className="text-center text-xs">
              <Link to="/hr/forgot" className="text-purple-700 hover:underline">{t("Forgot password?")}</Link>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
}
