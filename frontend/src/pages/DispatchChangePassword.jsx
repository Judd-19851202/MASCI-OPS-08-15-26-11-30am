// DispatchChangePassword — first-login + admin-reset rotation page.
// Mirrors HrChangePassword chrome but with the orange-700 accent. Posts
// to /api/dispatch/change-password and swaps the freshly-issued token in
// so the session keeps going without bouncing to /login.
import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { ShieldCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { useT } from "@/lib/i18n";
import { setMustChange } from "@/lib/mustChangePassword";
import {
  getDispatchToken,
  setDispatchToken,
  setDispatchUser,
  clearDispatchToken,
} from "@/lib/dispatchAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const authHdr = () => ({ "X-Dispatch-Token": getDispatchToken() });

export default function DispatchChangePassword() {
  const { t } = useT();
  const navigate = useNavigate();
  const location = useLocation();
  const originalFrom = location.state?.from || "/dispatch-portal";
  const [me, setMe] = useState(null);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await axios.get(`${API}/dispatch/me`, { headers: authHdr() });
        if (!alive) return;
        setMe(r.data?.user || null);
      } catch {
        clearDispatchToken();
        navigate("/dispatch-portal/login", { replace: true });
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
      const r = await axios.post(
        `${API}/dispatch/change-password`,
        { current_password: oldPw, new_password: newPw },
        { headers: authHdr() },
      );
      if (r.data?.ok && r.data?.token) {
        setDispatchToken(r.data.token, true);
        setDispatchUser(r.data.user || {});
        setMustChange("dispatch", false);
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
    <PortalLoginShell
      homeLink="/dispatch-portal"
      headerBorderClass="border-orange-700"
      backHoverClass="hover:text-orange-300"
      backTestId="dispatch-change-pw-back"
      rootTestId="dispatch-change-pw-page"
      footerLabel={t("MASCI · Dispatch")}
    >
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
        <div className="flex items-center gap-3 mb-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-700 text-white">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-700">
              {t("Operations · Fleet Movement")}
            </div>
            <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1" data-testid="dispatch-change-pw-title">
              {t("Choose your password")}
            </h1>
          </div>
        </div>
        {me && (
          <p className="text-slate-600 text-sm mb-1" data-testid="dispatch-change-pw-identity">
            {t("Signed in as")} <span className="font-mono text-slate-900 font-bold">{me.email}</span>
          </p>
        )}
        <p className="text-slate-600 text-sm mb-6">{t("Pick something at least 8 characters.")}</p>

        <form onSubmit={onSubmit} className="space-y-4" data-testid="dispatch-change-pw-form">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
              {t("Current (or temporary) password")}
            </Label>
            <PasswordInput
              value={oldPw}
              onChange={(e) => setOldPw(e.target.value)}
              autoFocus
              autoComplete="current-password"
              className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-700"
              data-testid="dispatch-change-pw-old"
              toggleTestId="dispatch-change-pw-old-toggle"
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
              className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-700"
              data-testid="dispatch-change-pw-new"
              toggleTestId="dispatch-change-pw-new-toggle"
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
              className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-orange-700"
              data-testid="dispatch-change-pw-confirm"
              toggleTestId="dispatch-change-pw-confirm-toggle"
            />
          </div>
          <Button
            type="submit"
            disabled={submitting}
            className="w-full h-12 bg-orange-700 hover:bg-orange-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-orange-900"
            data-testid="dispatch-change-pw-submit"
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
    </PortalLoginShell>
  );
}