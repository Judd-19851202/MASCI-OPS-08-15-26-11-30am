import React, { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Lock, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { MasciLogo } from "@/components/MasciLogo";
import { api } from "@/lib/api";
import { setAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { toast } from "sonner";

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Landing on /admin/login means any prior session is over.
  // Wipe any stale admin token so a bad token can't poison the next call
  // and so the password field starts from a clean state.
  useEffect(() => {
    clearAdminToken();
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!password) {
      toast.error("Enter the admin password");
      return;
    }
    setSubmitting(true);
    // Defensive: clear any token immediately before the POST so the
    // request interceptor doesn't attach a stale X-Admin-Token header.
    clearAdminToken();
    try {
      const res = await api.post("/admin/login", { password });
      if (res?.data?.ok && res?.data?.token) {
        setAdminToken(res.data.token);
        toast.success("Welcome back, admin");
        const from = location.state?.from || "/admin";
        navigate(from, { replace: true });
      } else {
        toast.error("Login failed");
      }
    } catch (err) {
      const msg =
        err?.response?.status === 401
          ? "Wrong password"
          : "Login failed — check connection";
      toast.error(msg);
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
            <ArrowLeft className="w-4 h-4 mr-1" /> Hub
          </Link>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/admin" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/admin" />
          <span className="hidden sm:inline-block w-20" />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <div className="w-full max-w-md bg-white border-2 border-slate-300 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700">
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
            <div>
              <Label htmlFor="admin-password" className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700">
                Admin Password
              </Label>
              <PasswordInput
                id="admin-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoFocus
                autoComplete="current-password"
                className="mt-2 h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                data-testid="admin-password-input"
                toggleTestId="admin-password-toggle"
              />
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
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
        MASCI · Office Use Only
      </footer>
    </div>
  );
}
