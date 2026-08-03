import React from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { PortalShell } from "@/design-system/PortalShell";
import { useT } from "@/lib/i18n";
import { getHrUser } from "@/lib/hrAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { api } from "@/lib/api";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";

export default function HrPageShell({ title, kicker, children }) {
  const { t } = useT();
  const nav = useNavigate();
  const user = getHrUser();
  const safeUserName = sanitizeOperatorReference(user?.name, "");

  const signOut = async () => {
    try { await api.post("/auth/multi-logout"); } catch { /* ignore */ }
    await clearAllSessions();
    nav("/hr/login");
  };

  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t("Human Resources")}
      portalSwitcherCurrent="hr"
      pageTitle={t(title)}
      subtitle={`${kicker || t("Human Resources")} ${safeUserName ? `· ${safeUserName}` : ""}`.trim()}
      sideNav={<HrSideNavV2 />}
      showBack
      backHref="/hr"
      onSignOut={signOut}
      experienceTone="hr"
    >
      <div className="space-y-5" data-testid="hr-page-shell-body">
        <section className="wp17-mission-banner" data-testid="hr-page-shell-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">{t("Today's focus")}</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">{t("Keep the workforce ready with fewer clicks and clearer operational context.")}</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                {t("See who needs action, open the right record, and keep the workforce ready.")}
              </p>
            </div>
            <div className="wp17-chip-row">
              <span className="wp17-chip" data-testid="hr-page-shell-focus-chip">
                <ShieldCheck className="h-3.5 w-3.5" /> {t("People operations first")}
              </span>
            </div>
          </div>
        </section>
        <div data-testid="hr-page-shell-content">{children}</div>
      </div>
    </PortalShell>
  );
}