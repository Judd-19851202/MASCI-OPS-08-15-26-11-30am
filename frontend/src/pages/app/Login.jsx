import React, { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MasciLogo } from "@/components/MasciLogo";
import { useAuth } from "@/lib/authContext";

function apiErr(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || JSON.stringify(e)).join(" ");
  return detail?.msg || String(detail);
}

export default function Login() {
  const nav = useNavigate();
  const loc = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const user = await login(email.trim().toLowerCase(), password);
      toast.success(`Welcome back, ${user.name.split(" ")[0] || user.email}`);
      const target = user.must_change_password ? "/app/change-password" : (loc.state?.from || "/app");
      nav(target, { replace: true });
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Login failed"));
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
              Crew Hub · Sign in
            </div>
            <h1 className="font-display text-2xl font-black text-slate-900 tracking-tight">
              Welcome back.
            </h1>
            <p className="text-sm text-slate-600 mt-1.5">
              Use the email address MASCI issued you.
            </p>
            <form onSubmit={onSubmit} className="mt-6 space-y-4" data-testid="login-form">
              <div>
                <Label htmlFor="email" className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@mascigc.com"
                  className="mt-1.5 h-11"
                  data-testid="login-email"
                />
              </div>
              <div>
                <Label htmlFor="password" className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1.5 h-11"
                  data-testid="login-password"
                />
              </div>
              <Button
                type="submit"
                disabled={submitting}
                className="w-full h-11 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
                data-testid="login-submit"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><LogIn className="w-4 h-4 mr-2" /> Sign in</>)}
              </Button>
            </form>
            <p className="mt-6 text-xs text-slate-500 leading-relaxed">
              Not on the list yet? Ask David, Chris, Ramon, or Jaymn to invite you. Forgot your password? An owner can reset it from the Users panel.
            </p>
          </div>
          <div className="mt-4 text-center">
            <Link to="/" className="text-xs font-mono uppercase tracking-[0.2em] text-slate-400 hover:text-red-400" data-testid="back-to-hub">
              ← Back to Safety Hub
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
