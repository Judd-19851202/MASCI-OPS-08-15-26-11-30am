// Shared layout for /hr/* sub-pages. Header with logo + sign-out,
// "← HR Hub" back link, language toggle. Mirrors PmHub / ShopHub chrome
// for visual consistency.
//
// iter437 IV-BETA.3B · optional Sidebar V2 mounts behind ?hrSidebarV2=1
// — when off, the legacy single-column layout renders unchanged.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogOut, ArrowLeft, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { clearHrToken, getHrUser } from "@/lib/hrAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import HrSideNavV2, { useHrSidebarV2Enabled } from "@/components/hr/sidebar/HrSideNavV2";

export default function HrPageShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const user = getHrUser();
  const sidebarV2 = useHrSidebarV2Enabled();

  const signOut = async () => {
    // P0 (iter179): wipe every auth artifact, not just HR.
    await clearAllSessions();
    nav("/hr/login");
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-purple-700">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3 flex-wrap">
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
            <Button variant="outline" size="sm" onClick={signOut} className="text-xs bg-transparent text-white border-white/30 hover:bg-white/10" data-testid="hr-sign-out">
              <LogOut className="w-3.5 h-3.5 mr-1" /> {t("Sign out")}
            </Button>
          </div>
        </div>
      </header>
      <div className={sidebarV2 ? "max-w-7xl mx-auto flex" : ""}>
        {sidebarV2 && (
          <HrSideNavV2 className="hidden lg:block w-64 flex-shrink-0 min-h-[calc(100vh-200px)]" />
        )}
        <main className={`${sidebarV2 ? "flex-1 px-5 sm:px-8 py-8" : "max-w-7xl mx-auto px-5 sm:px-8 py-8"}`}>
          <Link to="/hr" className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-purple-700 font-bold mb-4">
            <ArrowLeft className="w-3.5 h-3.5" /> {t("HR Hub")}
          </Link>
          <div className="font-mono text-xs uppercase tracking-[0.2em] text-purple-700">
            <ShieldCheck className="w-3.5 h-3.5 inline mr-1" /> {kicker || t("HR Portal")} {user?.name ? `· ${user.name}` : ""}
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black mt-1 mb-6">{t(title)}</h1>
          {children}
        </main>
      </div>
    </div>
  );
}
