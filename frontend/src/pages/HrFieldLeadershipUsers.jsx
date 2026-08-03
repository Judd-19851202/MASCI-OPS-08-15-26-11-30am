// HrFieldLeadershipUsers.jsx — HR-side host for the Field Leadership
// Portal user-management panel (iter314). Same component as Admin uses;
// the backend route accepts either X-Admin-Token or X-HR-Token.
// UXS-11E: wrapped in PortalShell (HR Portal).
import React from "react";
import { Link } from "react-router-dom";
import { Users, ScrollText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import AdminFieldLeadershipUsersPanel from "@/components/AdminFieldLeadershipUsersPanel";
import { HelpTipBlock } from "@/components/HelpTip";
import { IamUserDetailDrawerHost } from "@/components/iam/IamUserDetailDrawer";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";

export default function HrFieldLeadershipUsers() {
  const { t } = useT();
  usePageTitle("Field Leadership Users · HR");
  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Field Leadership"
      pageTitle={t("Field Leadership Users")}
      subtitle={t("Issue per-user temporary passwords, reset passwords, and deactivate field leaders.")}
      sideNav={<HrSideNavV2 />}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6" data-testid="hr-fl-users-page">
        {/* Track 15.14B — paired surface anchor. Records ↔ Users. */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 p-3 rounded-md border-2 border-purple-200 bg-purple-50/60">
          <div className="text-sm text-slate-700">
            <span className="font-semibold text-slate-900">{t("Field Leadership Users")}</span>{" "}
            <span className="text-slate-600">
              {t("· create, disable, and rotate passwords for portal logins.")}
            </span>
          </div>
          <Link to="/hr/field-leadership" data-testid="hr-fl-users-to-records">
            <Button size="sm" variant="outline" className="border-purple-700 text-purple-700 hover:bg-purple-50">
              <ScrollText className="w-3.5 h-3.5 mr-1.5" />
              {t("View Field Leadership Records")}
            </Button>
          </Link>
        </div>
        <HelpTipBlock formKey="field-leadership.user-management" showCounter />
        <div className="mb-4 mt-3 flex items-center gap-2 text-sm text-slate-600">
          <Users className="h-4 w-4 text-purple-700" />
          <span>
            {t(
              "Manage MASCI Field Leadership Portal accounts. Issue per-user temporary passwords, reset passwords, and deactivate field leaders. This is the dedicated per-user sign-in area — separate from the legacy shared-password document gate."
            )}
          </span>
        </div>
        <AdminFieldLeadershipUsersPanel />
      </div>
      {/* iter506 · OMEGA Unified User Detail Drawer — HR Field Leadership parity */}
      <IamUserDetailDrawerHost />
    </PortalShell>
  );
}
