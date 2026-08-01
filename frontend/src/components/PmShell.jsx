import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { LayoutDashboard } from "lucide-react";
import SideNavV2 from "@/components/pm/sidebar/SideNavV2";
import { PortalShell } from "@/design-system/PortalShell";
import { clearAllSessions } from "@/lib/sessionReset";
import { toast } from "sonner";

export default function PmShell({
  title,
  section,
  children,
  intro,
  showPageHeader = true,
  showMissionBanner = true,
  subtitle,
}) {
  const navigate = useNavigate();

  const signOut = async () => {
    await clearAllSessions();
    toast.success("Signed out");
    navigate("/pm/login", { replace: true });
  };

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Project Management"
      portalSwitcherCurrent="pm"
      pageTitle={title}
      subtitle={subtitle || "Project execution, blockers, due work, and field coordination in one canonical shell."}
      sideNav={<SideNavV2 />}
      onSignOut={signOut}
      experienceTone="pm"
      showPageHeader={showPageHeader}
    >
      <div className="space-y-5" data-testid="pm-section-body">
        {showMissionBanner ? (
          <section className="wp17-mission-banner" data-testid="pm-section-banner">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="wp17-kicker text-white/70">Portal mission</div>
                <h2 className="mt-2 font-display text-xl font-black text-white">Turn project noise into the next useful action.</h2>
                <p className="mt-2 max-w-3xl text-sm text-white/80">
                  PM work now shares the same shell, hierarchy, and responsive behavior across details, lists, forms, and dashboards.
                </p>
              </div>
            </div>
          </section>
        ) : null}

        {section !== "overview" && (
          <div className="flex items-center gap-2 flex-wrap">
            <Link
              to="/pm"
              className="wp17-public-link max-w-fit"
              data-testid="pm-back-to-overview"
            >
              <span className="inline-flex items-center gap-2"><LayoutDashboard className="w-4 h-4" /> Back to PM Overview</span>
            </Link>
          </div>
        )}

        {intro ? (
          <div className="wp17-panel" data-testid="pm-section-intro">
            {intro}
          </div>
        ) : null}

        <div data-testid="pm-section-content">{children}</div>
      </div>
    </PortalShell>
  );
}