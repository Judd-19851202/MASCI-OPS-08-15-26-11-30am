// AdminLogin.jsx — iter85 rewrite
//
// Parity with PM/Shop/HR login pages: email + password fields, "Forgot
// password?" link, "Remember me on this device" checkbox. Authenticates
// via the unified `/api/auth/multi-login` directory endpoint (same one
// /sign-in uses), so an admin's user_directory record drives the
// session.
//
// The legacy single-password `POST /api/admin/login` endpoint is left
// intact server-side as an API-only break-glass path (callable via
// curl / scripts) but the human-facing UI now matches every other
// portal's sign-in chrome.
import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ShieldAlert, Loader2, ArrowLeft, Mail, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import { PortalLoginHelp } from "@/components/PortalLoginHelp";
import { api } from "@/lib/api";
import { applyMultiLoginResponse, landingFor } from "@/lib/directoryAuth";
import { clearAdminToken } from "@/lib/adminAuth";
import { clearPmToken } from "@/lib/pmAuth";
import { clearShopToken } from "@/lib/shopAuth";
import { clearHrToken } from "@/lib/hrAuth";
import { toast } from "sonner";

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  useEffect(() => {
    // Iter88 — DO NOT wipe tokens on mount.
    //
    // Previous behavior cleared every portal token here so a stale
    // session couldn't poison the next login. That was hostile to
    // multi-portal users: if a route-guard race transiently bounced
    // them to this page, the mount wipe killed their entire session,
    // making the bounce permanent.
    //
    // Tokens are now cleared ONLY on:
    //   • Explicit "Sign Out" (handled elsewhere)
    //   • Right before a successful login response is applied (the new
    //     bundle overwrites the old tokens via setX(), no clear needed)
    // Reaching this page with a live multi-portal session is a transient
    // hiccup — the page-guards' hydration hook will rescue it.
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      toast.error("Enter your work email and admin password");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post(
        "/auth/multi-login",
        { email: email.trim().toLowerCase(), password },
        { timeout: 90000 } // backend cold-start can take ~60s
      );
      if (res?.data?.ok) {
        applyMultiLoginResponse(res.data, rememberMe);
        const user = res.data.user;
        const portals = user?.portals || [];
        if (!portals.includes("admin")) {
          // Authenticated, but this directory user doesn't have admin scope.
          // Redirect them to whatever portal they DO have access to.
          toast.warning(
            `Welcome ${user?.name || ""} — this account doesn't have Admin access. Routing you to ${portals[0]?.toUpperCase() || "the Hub"}.`,
            { duration: 6000 }
          );
          navigate(landingFor(user), { replace: true });
          return;
        }
        toast.success(`Welcome back, ${user?.name || "admin"}`);
        const from = location.state?.from || "/admin";
        navigate(from, { replace: true });
      } else {
        toast.error("Sign-in failed — server did not return a session");
      }
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      let msg;
      if (status === 401) {
        msg = "Wrong email or password";
      } else if (status === 423) {
        msg = "Account is locked — call the office";
      } else if (status === 429) {
        msg = detail || "Too many attempts — wait a minute and try again";
      } else if (status === 520 || status === 521 || status === 522 || status === 523 || status === 524) {
        msg = "Server is waking up — give it ~60 seconds and try again";
      } else if (status >= 500 && status < 600) {
        msg = `Server error (${status}) — try again in a moment`;
      } else if (err?.code === "ECONNABORTED" || /timeout/i.test(err?.message || "")) {
        msg = "Request timed out — server is cold-starting, try again";
      } else if (!err?.response) {
        msg = "Can't reach server — check your internet";
      } else {
        msg = typeof detail === "string" ? detail : `Sign-in failed (${status || "unknown"})`;
      }
      toast.error(msg, { duration: 6000 });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="admin-login-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Home
          </Link>
          <MasciLogo variant="mark" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                Restricted Area
              </div>
              <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                Admin Sign In
              </h1>
            </div>
          </div>
          <p className="text-slate-600 text-sm mt-3 mb-6">
            Office sign-in for managers and supervisors. Field crews don't need
            to sign in to fill out forms — they can start a new one straight
            from the{" "}
            <Link to="/" className="text-red-700 font-bold hover:underline">
              Hub
            </Link>
            .
          </p>

          <form onSubmit={onSubmit} className="space-y-4" data-testid="admin-login-form">
            {/* Email */}
            <div>
              <Label htmlFor="admin-email" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                Work Email
              </Label>
              <div className="relative mt-2">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <Input
                  id="admin-email"
                  type="email"
                  inputMode="email"
                  autoComplete="username"
                  autoFocus
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@mascigc.com"
                  className="h-12 pl-9 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                  data-testid="admin-email-input"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <Label htmlFor="admin-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1">
                <KeyRound className="w-3 h-3" /> Password
              </Label>
              <PasswordInput
                id="admin-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                data-testid="admin-password-input"
                toggleTestId="admin-password-toggle"
              />
            </div>

            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 accent-red-700"
                  data-testid="admin-remember-me"
                />
                <span className="text-xs font-mono uppercase tracking-wide text-slate-700 font-bold">
                  Remember me on this device
                </span>
              </label>
              <span className="text-[11px] text-slate-500">
                Forgot password? Call the office.
              </span>
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="admin-login-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Verifying…
                </>
              ) : (
                <>Sign In</>
              )}
            </Button>
          </form>
          <PortalLoginHelp portal="admin" />

          <p className="mt-5 pt-4 border-t border-slate-200 text-[11px] text-slate-500 leading-relaxed text-center">
            Access multiple portals?{" "}
            <Link to="/sign-in" className="text-slate-900 font-bold hover:underline" data-testid="admin-login-master-link">
              Use the master sign-in
            </Link>{" "}
            to land on any portal in one step.
          </p>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 flex flex-col items-center gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          MASCI · Office Use Only
        </div>
        <ForgedOpsAttribution variant="login" />
      </footer>
    </div>
  );
}
