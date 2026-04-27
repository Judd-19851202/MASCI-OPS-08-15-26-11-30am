import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, KeyRound } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { useAuth } from "@/lib/authContext";

function apiErr(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || JSON.stringify(e)).join(" ");
  return detail?.msg || String(detail);
}

export default function ChangePassword() {
  const nav = useNavigate();
  const { user, refresh, logout } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (next !== confirm) {
      toast.error("Passwords don't match.");
      return;
    }
    if (next.length < 10) {
      toast.error("Use at least 10 characters.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/change-password", {
        current_password: current,
        new_password: next,
      });
      toast.success("Password updated.");
      await refresh();
      nav("/app", { replace: true });
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Change failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      <div className="caution-stripe" />
      <main className="flex-1 flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-md">
          <div className="flex justify-center mb-6">
            <MasciLogo variant="lockup" size="2xl" homeLink="/" />
          </div>
          <div className="bg-white border-2 border-slate-200 rounded-md p-7 shadow-2xl">
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold mb-1">
              Crew Hub · Set your password
            </div>
            <h1 className="font-display text-2xl font-black text-slate-900 tracking-tight">
              {user?.must_change_password ? "First login — pick a new password." : "Change your password."}
            </h1>
            <p className="text-sm text-slate-600 mt-1.5">Minimum 10 characters.</p>
            <form onSubmit={onSubmit} className="mt-6 space-y-4" data-testid="change-password-form">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                  Current password
                </Label>
                <PasswordInput
                  autoComplete="current-password"
                  required
                  value={current}
                  onChange={(e) => setCurrent(e.target.value)}
                  className="mt-1.5 h-11"
                  data-testid="change-password-current"
                  toggleTestId="change-password-current-toggle"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                  New password
                </Label>
                <PasswordInput
                  autoComplete="new-password"
                  minLength={10}
                  required
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                  className="mt-1.5 h-11"
                  data-testid="change-password-new"
                  toggleTestId="change-password-new-toggle"
                />
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                  Confirm new password
                </Label>
                <PasswordInput
                  autoComplete="new-password"
                  minLength={10}
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="mt-1.5 h-11"
                  data-testid="change-password-confirm"
                  toggleTestId="change-password-confirm-toggle"
                />
              </div>
              <Button
                type="submit"
                disabled={submitting}
                className="w-full h-11 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
                data-testid="change-password-submit"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><KeyRound className="w-4 h-4 mr-2" /> Update password</>)}
              </Button>
              <button
                type="button"
                onClick={async () => { await logout(); nav("/app/login", { replace: true }); }}
                className="w-full text-xs font-mono uppercase tracking-[0.15em] text-slate-500 hover:text-red-700"
              >
                Sign out instead
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
