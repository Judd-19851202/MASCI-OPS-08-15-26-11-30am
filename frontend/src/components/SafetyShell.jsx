import React from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { PortalShell } from "@/design-system/PortalShell";
import { useT } from "@/lib/i18n";
import { getSafetyUser } from "@/lib/safetyAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { api } from "@/lib/api";
import SafetySideNavV2 from "@/components/safety/sidebar/SafetySideNavV2";

export default function SafetyShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const user = getSafetyUser();

  const signOut = async () => {
    try { await api.post("/auth/multi-logout"); } catch { /* ignore */ }
    await clearAllSessions();
    nav("/safety-portal/login");
  };

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Safety Operations"
      portalSwitcherCurrent="safety"
      pageTitle={t(title)}
      subtitle={`${kicker || t("Safety Operations")} ${user?.name ? `· ${user.name}` : ""}`.trim()}
      sideNav={<SafetySideNavV2 />}
      showBack
      backHref="/safety-portal"
      onSignOut={signOut}
      experienceTone="safety"
    >
      <div className="space-y-5" data-testid="safety-page-shell-body">
        <section className="wp17-mission-banner" data-testid="safety-page-shell-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">Portal mission</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">Act on risk before it spreads into the field.</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                Safety surfaces now follow the same shell, navigation hierarchy, and glass/grid system as the rest of the platform while keeping operational risk clear.
              </p>
            </div>
            <div className="wp17-chip-row">
              <span className="wp17-chip" data-testid="safety-page-shell-focus-chip">
                <ShieldAlert className="h-3.5 w-3.5" /> {t("Incidents, CAPAs, and field records first")}
              </span>
            </div>
          </div>
        </section>
        <div data-testid="safety-page-shell-content">{children}</div>
      </div>
    </PortalShell>
  );
}