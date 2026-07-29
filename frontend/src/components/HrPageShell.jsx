import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { getHrUser } from "@/lib/hrAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { api } from "@/lib/api";
import HrSideNavV2, { useHrSidebarV2Enabled } from "@/components/hr/sidebar/HrSideNavV2";
import { PortalShell } from "@/design-system";

export default function HrPageShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const location = useLocation();
  const user = getHrUser();
  const sidebarV2 = useHrSidebarV2Enabled();
  const showBack = location.pathname !== "/hr";

  const signOut = async () => {
    try {
      await api.post("/auth/multi-logout");
    } catch {
      /* ignore */
    }
    await clearAllSessions();
    nav("/hr/login");
  };

  const subtitleParts = [kicker || t("Human Resources")];
  if (user?.name) subtitleParts.push(user.name);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Human Resources"
      pageTitle={t(title)}
      subtitle={subtitleParts.join(" · ")}
      homeHref="/hr"
      backHref="/hr"
      showBack={showBack}
      onSignOut={signOut}
      portalSwitcherCurrent="hr"
      sideNav={sidebarV2 ? <HrSideNavV2 /> : null}
    >
      {children}
    </PortalShell>
  );
}