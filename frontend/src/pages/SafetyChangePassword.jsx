// SafetyChangePassword — first-login + admin-reset rotation page.
// Mirrors HrChangePassword chrome but with the cyan-700 accent. Posts
// to /api/safety/change-password and swaps the freshly-issued token in
// so the session keeps going without bouncing to /login.
import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import axios from "axios";
import { ShieldCheck, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import {
  getSafetyToken,
  setSafetyToken,
  setSafetyUser,
  clearSafetyToken,
} from "@/lib/safetyAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const authHdr = () => ({ "X-Safety-Token": getSafetyToken() });

export default function SafetyChangePassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const location = useLocation();
  const originalFrom = location.state?.from || "/safety-portal";
  const [me, setMe] = useState(null);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await axios.get(`${API}/safety/me`, { headers: authHdr() });
        if (!alive) return;
        setMe(r.data?.user || null);
      } catch {
        clearSafetyToken();
        navigate("/safety-portal/login", { replace: true });
      }
    })();
    return () => { alive = false; };
  }, [navigate]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (newPw.length < 8) {
      toast.error(t("New password must be at least 8 characters"));
      return;
    }
    if (newPw !== confirmPw) {
      toast.error(t("Passwords don't match"));
      return;
    }
    if (newPw === oldPw) {
      toast.error(t("New password must be different from the old one"));
      return;
    }
    setSubmitting(true);
    try {
      const r = await axios.post(
        `${API}/safety/change-password`,
        { current_password: oldPw, new_password: newPw },
        { headers: authHdr() },
      );
      if (r.data?.ok && r.data?.token) {
        setSafetyToken(r.data.token, true);
        setSafetyUser(r.data.user || {});
        toast.success(t("Password updated"));
        navigate(originalFrom, { replace: true });
      } else {
        toast.error(t("Update failed"));
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("Update failed"));
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
            to="/safety-portal"
            className="inline-flex items-center text-white hover:text-cyan-300 text-sm font-bold uppercase tracking-wide"
            data-testid="safety-change-pw-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Safety Portal")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/safety-portal" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/safety-portal" />
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
                {t("Choose your password")}
              </h1>
            </div>
          </div>
          {me && (
            <p className="text-slate-600 text-sm mb-1">
              {t("Signed in as")}{" "}
              <span className="font-mono text-slate-900 font-bold">{me.email}</span>
            </p>
          )}
          <p className="text-slate-600 text-sm mb-6">
            {t("Pick something at least 8 characters. The temporary password the admin issued will stop working as soon as you save.")}
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="safety-change-pw-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Current (or temporary) password")}
              </Label>
              <PasswordInput
                value={oldPw}
                onChange={(e) => setOldPw(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700"
                data-testid="safety-change-pw-old"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("New password (8+ characters)")}
              </Label>
              <PasswordInput
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                autoComplete="new-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700"
                data-testid="safety-change-pw-new"
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
                data-testid="safety-change-pw-confirm"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-cyan-700 hover:bg-cyan-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-cyan-900"
              data-testid="safety-change-pw-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Saving…")}
                </>
              ) : (
                t("Save new password")
              )}
            </Button>
          </form>
        </div>
      </main>
    </div>
  );
}
