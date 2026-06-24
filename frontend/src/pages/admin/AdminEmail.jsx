// AdminEmail.jsx — /admin/email section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import AdminEmailRoutingPanel from "@/components/AdminEmailRoutingPanel";
import EmailRoutingV2Panel from "@/components/EmailRoutingV2Panel";
import RoutingStatusPanel from "@/components/RoutingStatusPanel";
import PlatformTrustValidator from "@/components/PlatformTrustValidator";
import PlatformTrustDashboard from "@/components/PlatformTrustDashboard";
import TenantBrandingPanel from "@/components/TenantBrandingPanel";

export default function AdminEmail() {
  return (
    <AdminShell
      title="Email & Routing"
      section="email"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Every record (Daily Reports, Pre-Op fails, incidents, QA/QC, etc.) is auto-emailed when
          submitted. Configure who gets what — auto-routing rules (e.g. PM by job number) live in
          the first panel, plain distribution lists in the second, and the new 19-route catalog
          (Track 15.66) in the third.
        </p>
      }
    >
      <div className="space-y-4">
        <PlatformTrustDashboard />
        <PlatformTrustValidator />
        <RoutingStatusPanel />
        <TenantBrandingPanel />
        <EmailRoutingV2Panel />
        <AutoEmailRoutingPanel />
        <AdminEmailRoutingPanel />
      </div>
    </AdminShell>
  );
}
