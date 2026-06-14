// HrFieldLeadershipUsers.jsx — HR-side host for the Field Leadership
// Portal user-management panel (iter314). Same component as Admin uses;
// the backend route accepts either X-Admin-Token or X-HR-Token.
// UXS-11E: wrapped in PortalShell (HR Portal).
import React from "react";
import { Users } from "lucide-react";
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
        <HelpTipBlock formKey="field-leadership.user-management" showCounter />
        <div className="mb-4 mt-3 flex items-center gap-2 text-sm text-slate-600">
          <Users className="h-4 w-4 text-purple-700" />
          <span>
            {t(
              "Manage MASCI Field Leadership Portal accounts. Issue per-user temporary passwords, reset passwords, and deactivate field leaders. This is the governed per-user portal — distinct from the legacy shared-password document gate."
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
