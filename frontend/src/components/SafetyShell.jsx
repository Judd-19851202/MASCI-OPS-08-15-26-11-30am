// SafetyShell — shared layout chrome for /safety/* pages. Mirrors
// HrPageShell but with the cyan-700 accent so the portal is visually
// distinct from HR (purple), Field Leadership (red), PM (amber).
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogOut, ArrowLeft, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { clearSafetyToken, getSafetyUser } from "@/lib/safetyAuth";

export default function SafetyShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const user = getSafetyUser();

  const signOut = () => {
    clearSafetyToken();
    nav("/safety-portal/login");
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3 flex-wrap">
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
            <Button
              variant="outline"
              size="sm"
              onClick={signOut}
              className="text-xs"
              data-testid="safety-sign-out"
            >
              <LogOut className="w-3.5 h-3.5 mr-1" /> {t("Sign out")}
            </Button>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-5 sm:px-8 py-8">
        <Link
          to="/safety-portal"
          className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-cyan-700 font-bold mb-4"
          data-testid="safety-back-link"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> {t("Safety Portal")}
        </Link>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-700">
          <ShieldAlert className="w-3.5 h-3.5 inline mr-1" />{" "}
          {kicker || t("Safety Portal")}
          {user?.name ? ` · ${user.name}` : ""}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1 mb-6">
          {t(title)}
        </h1>
        {children}
      </main>
    </div>
  );
}
