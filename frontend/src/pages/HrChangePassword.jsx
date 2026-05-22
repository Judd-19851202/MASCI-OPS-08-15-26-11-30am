import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ShieldCheck, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { setHrToken, setHrUser, clearHrToken } from "@/lib/hrAuth";
import { toast } from "sonner";

/**
 * HrChangePassword — first-login + admin-reset rotation page.
 *
 * Mirrors PmChangePassword.jsx exactly so the cross-portal UX is
 * identical. Lives at /hr/change-password. Reachable two ways:
 *   1. HrLogin detects must_change_password=true and redirects here.
 *   2. HR user clicks "Change my password" from the HR hub later.
 *
 * IMPORTANT: always require the current/temp password — no
 * special-case "first-login" branch. This avoids brittle state
 * dependencies and matches PM/Shop behavior. The page does a fresh
 * /hr/me on mount so a stale/missing token bounces back to login
 * immediately instead of letting the user fill the form first.
 *
 * On success, swaps the stored token for the freshly-issued one and
 * bounces to /hr (or the original target if PMChangePassword forwarded
 * a `from` state).
 */
export default function HrChangePassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const location = useLocation();
  const originalFrom = location.state?.from || "/hr";
  const [me, setMe] = useState(null);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/hr/me");
        if (!alive) return;
        setMe(r.data?.user || null);
      } catch {
        // Token invalid / not present → bounce to login.
        clearHrToken();
        navigate("/hr/login", { replace: true });
      }
    })();
    return () => {
      alive = false;
    };
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
      const r = await api.post("/hr/change-password", {
        current_password: oldPw,
        new_password: newPw,
      });
      if (r.data?.ok && r.data?.token) {
        setHrToken(r.data.token, true);
        setHrUser(r.data.user || {});
        toast.success(t("Password updated"));
        navigate(originalFrom, { replace: true });
      } else {
        toast.error(t("Update failed"));
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      let msg;
      if (status === 401) {
        // Could be either: bad current password OR expired session
        msg = typeof detail === "string" ? detail : t("Current password is incorrect");
      } else {
        msg = typeof detail === "string" ? detail : t("Update failed");
      }
      toast.error(msg, { duration: 6000 });
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
            to="/hr"
            className="inline-flex items-center text-white hover:text-purple-300 text-sm font-bold uppercase tracking-wide"
            data-testid="hr-change-pw-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("HR Portal")}
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/hr" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/hr" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-purple-700 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-purple-700">
                {t("Human Resources")}
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

          <form onSubmit={onSubmit} className="space-y-4" data-testid="hr-change-pw-form">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                {t("Current (or temporary) password")}
              </Label>
              <PasswordInput
                value={oldPw}
                onChange={(e) => setOldPw(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700"
                data-testid="hr-change-pw-old"
                toggleTestId="hr-change-pw-old-toggle"
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
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700"
                data-testid="hr-change-pw-new"
                toggleTestId="hr-change-pw-new-toggle"
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
                data-testid="hr-change-pw-confirm"
                toggleTestId="hr-change-pw-confirm-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-purple-700 hover:bg-purple-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-purple-900"
              data-testid="hr-change-pw-submit"
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

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          {t("MASCI · Human Resources Portal")}
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
