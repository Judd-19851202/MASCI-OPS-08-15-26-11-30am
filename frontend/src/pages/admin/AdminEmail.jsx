// AdminEmail.jsx — /admin/email
import React from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import AdminEmailRoutingPanel from "@/components/AdminEmailRoutingPanel";
import EmailRoutingV2Panel from "@/components/EmailRoutingV2Panel";
import RoutingStatusPanel from "@/components/RoutingStatusPanel";
import PlatformTrustValidator from "@/components/PlatformTrustValidator";
import OperationsTrustCenter from "@/components/OperationsTrustCenter";
import TenantBrandingPanel from "@/components/TenantBrandingPanel";

export default function AdminEmail() {
  return (
    <LegacyAdminModernShell
      title="Email & Routing"
      subtitle="Auto-routing rules · distribution lists · route catalog."
      breadcrumb={[
        { label: "Communications", to: "/admin/communications" },
        { label: "Email & Routing" },
      ]}
      testidPrefix="admin-email"
    >
      <div className="mb-5 rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-sm text-slate-600 leading-relaxed">
          Every record (Daily Reports, Pre-Op fails, incidents, QA/QC, etc.) is auto-emailed when
          submitted. Configure who gets what — auto-routing rules (e.g. PM by job number) live in
          the first panel, plain distribution lists in the second, and the route catalog
          in the third.
        </p>
      </div>
      <div className="space-y-4">
        <OperationsTrustCenter />
        <PlatformTrustValidator />
        <RoutingStatusPanel />
        <TenantBrandingPanel />
        <EmailRoutingV2Panel />
        <AutoEmailRoutingPanel />
        <AdminEmailRoutingPanel />
      </div>
    </LegacyAdminModernShell>
  );
}
