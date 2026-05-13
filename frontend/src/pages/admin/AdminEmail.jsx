// AdminEmail.jsx — /admin/email section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import AdminEmailRoutingPanel from "@/components/AdminEmailRoutingPanel";

export default function AdminEmail() {
  return (
    <AdminShell
      title="Email & Routing"
      section="email"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Every record (Daily Reports, Pre-Op fails, incidents, QA/QC, etc.) is auto-emailed when
          submitted. Configure who gets what — auto-routing rules (e.g. PM by job number) live in
          the first panel, plain distribution lists in the second.
        </p>
      }
    >
      <div className="space-y-4">
        <AutoEmailRoutingPanel />
        <AdminEmailRoutingPanel />
      </div>
    </AdminShell>
  );
}
