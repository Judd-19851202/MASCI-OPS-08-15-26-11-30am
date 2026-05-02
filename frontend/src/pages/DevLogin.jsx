import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Terminal, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { api } from "@/lib/api";
import { setDevToken, clearDevToken } from "@/lib/devAuth";
import { toast } from "sonner";

/**
 * Developer portal login — vendor-only entry point (The Judd Group LLC).
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
      else if (status >= 500 && status < 600) msg = `Server error (${status})`;
      else if (!err?.response) msg = "Can't reach server";
      else msg = `Login failed (${status || "unknown"})`;
      toast.error(msg, { duration: 5000 });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col" data-testid="dev-login-page">
      <header className="border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-slate-400 hover:text-white text-xs font-mono uppercase tracking-[0.2em]"
            data-testid="dev-login-back"
          >
            <ArrowLeft className="w-3 h-3 mr-1" /> Home
          </Link>
          <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500">
            The Judd Group LLC
          </span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-md p-7 sm:p-9">
          <div className="flex items-center gap-3 mb-5">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-800 text-emerald-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
                Vendor Access
              </div>
              <h1 className="font-mono text-lg font-bold text-white leading-none mt-1">
                dev.portal
              </h1>
            </div>
          </div>
          <p className="text-slate-500 text-xs font-mono mb-6">
            Restricted. For The Judd Group LLC use only.
          </p>

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
                className="mt-2 h-11 text-base bg-slate-950 border border-slate-700 text-white placeholder:text-slate-600 focus-visible:ring-1 focus-visible:ring-emerald-500"
                data-testid="dev-password-input"
                toggleTestId="dev-password-toggle"
              />
            </div>
            <Button
              type="submit"
              disabled={submitting}
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
      </main>

      <footer className="max-w-3xl mx-auto px-5 sm:px-8 py-5 text-center">
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600">
          Confidential · The Judd Group LLC
        </span>
      </footer>
    </div>
  );
}
