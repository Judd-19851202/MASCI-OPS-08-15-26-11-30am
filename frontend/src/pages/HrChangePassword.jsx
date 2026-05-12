import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { setHrToken, setHrUser, getHrUser } from "@/lib/hrAuth";
import { MasciLogo } from "@/components/MasciLogo";
import { useT } from "@/lib/i18n";

export default function HrChangePassword() {
  const { t } = useT();
  const nav = useNavigate();
  const user = getHrUser();
  const mustChange = user?.must_change_password;
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    if (!next || next.length < 8) return toast.error(t("Password must be at least 8 characters"));
    if (next !== confirm) return toast.error(t("Passwords do not match"));
    setBusy(true);
    try {
      const payload = { new_password: next };
      if (!mustChange) payload.current_password = current;
      const r = await api.post("/hr/change-password", payload);
      setHrToken(r.data.token, true);
      setHrUser(r.data.user);
      toast.success(t("Password updated"));
      nav("/hr");
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not change password"));
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
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-purple-700">
          {t("HR Portal · Account")}
        </div>
        <h1 className="font-display text-3xl font-black mt-1 mb-1">{t("Change Password")}</h1>
        <p className="text-sm text-slate-600 mb-6">
          {mustChange ? t("First-time sign in — pick a new password to continue.") : t("Pick a new password.")}
        </p>
        <Card className="p-6">
          <form onSubmit={submit} className="space-y-4">
            {!mustChange && (
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Current password")}
                </Label>
                <Input
                  type="password"
                  value={current}
                  onChange={(e) => setCurrent(e.target.value)}
                  autoComplete="current-password"
                  data-testid="hr-change-current"
                />
              </div>
            )}
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("New password")}
              </Label>
              <Input
                type="password"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                autoComplete="new-password"
                data-testid="hr-change-new"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Confirm new password")}
              </Label>
              <Input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
                data-testid="hr-change-confirm"
              />
            </div>
            <Button
              type="submit"
              disabled={busy}
              className="w-full bg-purple-700 hover:bg-purple-800 text-white"
              data-testid="hr-change-submit"
            >
              {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <KeyRound className="w-4 h-4 mr-2" />}
              {t("Save Password")}
            </Button>
          </form>
        </Card>
      </main>
    </div>
  );
}
