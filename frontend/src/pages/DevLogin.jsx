import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Terminal, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { api } from "@/lib/api";
import { setDevToken, clearDevToken } from "@/lib/devAuth";
import { toast } from "sonner";

/**
 * Developer portal login — vendor-only entry point (ForgedOps™).
 *
 * Deliberately plain, not branded to MASCI. Reached via a tiny
 * "Developer" link in the Hub footer so MASCI staff and field crews
 * don't stumble on it. Issues an X-Dev-Token that ONLY opens the
 * /api/dev/* routes — admin/PM surfaces remain untouched.
 */
export default function DevLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [envDisabled, setEnvDisabled] = useState(false);

  useEffect(() => {
    // Never inherit a stale dev token from the previous session on this
    // browser — always force a fresh password entry.
    clearDevToken();
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error("Enter the developer password");
      return;
    }
    if (envDisabled) {
      toast.error("Developer access is disabled in this environment");
      return;
    }
    setSubmitting(true);
    clearDevToken();
    try {
      const res = await api.post(
        "/dev/login",
        { password, _t: Date.now() },
        { timeout: 60000 }
      );
      if (res?.data?.ok && res?.data?.token) {
        setDevToken(res.data.token);
        toast.success("Developer session active");
        const from = location.state?.from || "/dev";
        navigate(from, { replace: true });
      } else {
        toast.error("Login failed — server didn't return a token");
      }
    } catch (err) {
      const status = err?.response?.status;
      let msg;
      if (status === 401) msg = "Wrong password";
      else if (status === 404) {
        setEnvDisabled(true);
        msg = "Developer access is disabled in this environment";
      }
      else if (status >= 500 && status < 600) msg = `Server error (${status})`;
      else if (!err?.response) msg = "Can't reach server";
      else msg = `Login failed (${status || "unknown"})`;
      toast.error(msg, { duration: 5000 });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalLoginShell
      homeLink="/"
      headerBorderClass="border-emerald-700"
      backHoverClass="hover:text-emerald-300"
      backTestId="dev-login-back"
      rootTestId="dev-login-page"
      footerLabel="ForgedOps™ · Confidential"
    >
      <div className="w-full max-w-sm rounded-md border border-slate-800 bg-slate-900 p-7 sm:p-9 shadow-2xl shadow-emerald-950/20">
          <div className="flex items-center gap-3 mb-5">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-800 text-emerald-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
                Vendor Access
              </div>
              <h1 className="font-mono text-lg font-bold text-white leading-none mt-1" data-testid="dev-login-title">
                dev.portal
              </h1>
            </div>
          </div>
          <p className="text-slate-500 text-xs font-mono mb-6">
            Restricted. For ForgedOps™ use only.
          </p>

          {envDisabled && (
            <div
              className="mb-5 rounded-md border border-amber-700 bg-amber-950/50 px-3 py-2 text-[11px] font-mono uppercase tracking-[0.18em] text-amber-200"
              data-testid="dev-login-disabled-alert"
            >
              Developer access is disabled in this environment.
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-4" data-testid="dev-login-form">
            <div>
              <Label
                htmlFor="dev-password"
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400"
              >
                Password
              </Label>
              <PasswordInput
                id="dev-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
                autoComplete="current-password"
                disabled={envDisabled}
                className="mt-2 h-11 text-base bg-slate-950 border border-slate-700 text-white placeholder:text-slate-600 focus-visible:ring-1 focus-visible:ring-emerald-500"
                data-testid="dev-password-input"
                toggleTestId="dev-password-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting || envDisabled}
              className="w-full h-11 bg-emerald-600 hover:bg-emerald-500 text-white font-mono uppercase tracking-wide text-xs"
              data-testid="dev-login-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3 h-3 mr-2 animate-spin" /> Verifying…
                </>
              ) : (
                <>Unlock</>
              )}
            </Button>
          </form>
      </div>
    </PortalLoginShell>
  );
}
