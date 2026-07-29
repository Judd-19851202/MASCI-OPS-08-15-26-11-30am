import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { getSafetyUser } from "@/lib/safetyAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { api } from "@/lib/api";
import SafetySideNavV2, { useSafetySidebarV2Enabled } from "@/components/safety/sidebar/SafetySideNavV2";
import { PortalShell } from "@/design-system";

export default function SafetyShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const location = useLocation();
  const user = getSafetyUser();
  const sidebarV2 = useSafetySidebarV2Enabled();
  const showBack = location.pathname !== "/safety-portal";

  const signOut = async () => {
    try {
      await api.post("/auth/multi-logout");
    } catch {
      /* ignore */
    }
    await clearAllSessions();
    nav("/safety-portal/login");
  };

  const subtitleParts = [kicker || t("Safety Operations")];
  if (user?.name) subtitleParts.push(user.name);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Safety Operations"
      pageTitle={title ? t(title) : t("Safety Operations")}
      subtitle={subtitleParts.join(" · ")}
      homeHref="/safety-portal"
      backHref="/safety-portal"
      showBack={showBack}
      onSignOut={signOut}
      portalSwitcherCurrent="safety"
      sideNav={sidebarV2 ? <SafetySideNavV2 /> : null}
    >
      {children}
    </PortalShell>
  );
}