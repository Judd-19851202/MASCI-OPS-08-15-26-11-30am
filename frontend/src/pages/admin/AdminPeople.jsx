// AdminPeople.jsx — /admin/people section page
// iter505 · OMEGA Admin IAM Screen Completion Sprint
//
// Hierarchy (per directive):
//   LEVEL 1 — Access Control Center (dominant)
//   LEVEL 2 — Unified Directory     (searchable identity table)
//   LEVEL 3 — Portal-specific panels (collapsed accordion · counts shown · expand on demand)
//
// Zero behaviour change to underlying panels. Read-only re-ordering + accordion wrap.
import React from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import AdminPMPanel from "@/components/AdminPMPanel";
import AdminShopUsersPanel from "@/components/AdminShopUsersPanel";
import AdminHRUsersPanel from "@/components/AdminHRUsersPanel";
import AdminFieldLeadershipUsersPanel from "@/components/AdminFieldLeadershipUsersPanel";
import AdminSafetyUsersPanel from "@/components/AdminSafetyUsersPanel";
import AdminDispatchUsersPanel from "@/components/AdminDispatchUsersPanel";
import AdminAccessControlPanel from "@/components/AdminAccessControlPanel";
import AdminAccessStatsTile from "@/components/AdminAccessStatsTile";
import AdminUnifiedDirectoryPanel from "@/components/AdminUnifiedDirectoryPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";
import PortalUsersAccordion from "@/components/iam/PortalUsersAccordion";
import { IamUserDetailDrawerHost } from "@/components/iam/IamUserDetailDrawer";

export default function AdminPeople() {
  return (
    <LegacyAdminModernShell
      title="People & Access"
      subtitle="Access Control Center · Unified Directory · portal accounts. Modernize IAM across every portal from one screen."
      experienceLevel="wp17c"
      experienceTone="admin"
      breadcrumb={[
        { label: "Identity & Security", to: "/admin/identity-security" },
        { label: "People & Access" },
      ]}
      testidPrefix="admin-people"
    >
      <div className="mb-5 wp17-list-intro">
        <p className="text-sm text-slate-600 leading-relaxed" data-testid="admin-people-intro">
          <strong>Access Control Center</strong> is the source of truth for multi-portal accounts.
          <strong> Unified Directory</strong> is the searchable identity index.
          Portal-specific panels below are secondary views — expand only the one you need.
        </p>
      </div>
      <div className="space-y-3" data-testid="admin-people-stack">
        {/* LEVEL 0 — at-a-glance stats */}
        <AdminAccessStatsTile />

        {/* LEVEL 1 — Access Control Center (dominant) */}
        <AdminAccessControlPanel />

        {/* LEVEL 2 — Unified Directory (searchable identity index) */}
        <AdminUnifiedDirectoryPanel />

        {/* LEVEL 3 — Portal-specific panels (collapsed by default · counts shown) */}
        <PortalUsersAccordion portalKey="hr" title="HR Users & Logins">
          <AdminHRUsersPanel />
        </PortalUsersAccordion>
        <PortalUsersAccordion portalKey="pm" title="PM Users & Logins">
          <AdminPMPanel />
        </PortalUsersAccordion>
        <PortalUsersAccordion portalKey="safety" title="Safety Users & Logins">
          <AdminSafetyUsersPanel />
        </PortalUsersAccordion>
        <PortalUsersAccordion portalKey="dispatch" title="Dispatch Users & Logins">
          <AdminDispatchUsersPanel />
        </PortalUsersAccordion>
        <PortalUsersAccordion portalKey="shop" title="Shop Users & Logins">
          <AdminShopUsersPanel />
        </PortalUsersAccordion>
        <PortalUsersAccordion portalKey="field_leadership" title="Field Leadership Users & Logins">
          <AdminFieldLeadershipUsersPanel />
        </PortalUsersAccordion>

        {/* Employee master roster — peripheral, kept at the bottom */}
        <EmployeeMasterPanel />
      </div>

      {/* iter506 · OMEGA Unified User Detail Drawer — host mounted once;
          every <IamStandardCells> row opens it via window.__openIamUserDrawer */}
      <IamUserDetailDrawerHost />
    </LegacyAdminModernShell>
  );
}
