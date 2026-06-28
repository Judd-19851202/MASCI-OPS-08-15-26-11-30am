// SafetyShell — shared layout chrome for /safety/* pages. Mirrors
// HrPageShell but with the cyan-700 accent so the portal is visually
// distinct from HR (purple), Field Leadership (red), PM (amber).
//
// iter437 IV-BETA.5A-P6 · Sidebar V2 is now the DEFAULT layout after a
// clean stabilization review (Safety trendline direction=stable for 28
// consecutive records). Operators can opt out via `?safetySidebarV2=0`
// (URL · sticky), localStorage `masci.safety.sidebar.v2=0`, or env
// `REACT_APP_SAFETY_SIDEBAR_V2=0`. Legacy single-column layout remains
// one keystroke away — full reversibility, no destructive change.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogOut, ArrowLeft, ShieldAlert, Home, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import NotificationBell from "@/components/NotificationBell";
import { OfflineIndicator } from "@/lib/resiliency";
import GlobalSearch from "@/components/GlobalSearch";
import { useT } from "@/lib/i18n";
import { clearSafetyToken, getSafetyUser } from "@/lib/safetyAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import SafetySideNavV2, { useSafetySidebarV2Enabled } from "@/components/safety/sidebar/SafetySideNavV2";

export default function SafetyShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const user = getSafetyUser();
  const sidebarV2 = useSafetySidebarV2Enabled();

  const signOut = async () => {
    // P0 (iter179): wipe every auth artifact, not just Safety.
    await clearAllSessions();
    nav("/safety-portal/login");
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link to="/" className="inline-flex items-center text-white hover:text-cyan-300 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="safety-nav-home" title="Home">
            <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
          </Link>
          <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-cyan-300 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="safety-nav-back" title="Back">
            <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Back</span>
          </button>
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex-1" />
          {/* iter203 — Mobile header collapse */}
          <div className="flex flex-wrap items-center justify-end gap-1.5 sm:gap-2 min-w-0">
            <div className="hidden sm:flex items-center gap-2">
              <GlobalSearch accent="dark" />
            </div>
            <NotificationBell accent="white" />
            <OfflineIndicator />
            <LangToggle />
            <div className="hidden sm:flex"><CompanyInfoDialog /></div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => nav("/safety-portal/change-password")}
              className="hidden sm:inline-flex text-xs"
              data-testid="safety-change-password"
              title="Change My Password"
            >
              <KeyRound className="w-3.5 h-3.5 sm:mr-1" /><span className="hidden sm:inline">{t("Password")}</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={signOut}
              className="text-xs h-8 px-2 sm:px-2.5"
              data-testid="safety-sign-out"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5 sm:mr-1" /><span className="hidden sm:inline">{t("Sign out")}</span>
            </Button>
          </div>
        </div>
      </header>
      <div className={sidebarV2 ? "max-w-7xl mx-auto flex" : ""}>
        {sidebarV2 && (
          <SafetySideNavV2 className="hidden lg:block w-64 flex-shrink-0 min-h-[calc(100vh-200px)]" />
        )}
        <main className={`${sidebarV2 ? "flex-1 px-5 sm:px-8 py-8" : "max-w-7xl mx-auto px-5 sm:px-8 py-8"}`}>
          <Link
            to="/safety-portal"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-cyan-700 font-bold mb-4"
            data-testid="safety-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Safety Operations")}
          </Link>
          <div className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-700">
            <ShieldAlert className="w-3.5 h-3.5 inline mr-1" />{" "}
            {kicker || t("Safety Operations")}
            {user?.name ? ` · ${user.name}` : ""}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black mt-1 mb-6">
            {t(title)}
          </h1>
          {children}
        </main>
      </div>
    </div>
  );
}
