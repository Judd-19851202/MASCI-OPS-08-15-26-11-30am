// AdminCompliance.jsx — /admin/compliance section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import ComplianceExportPanel from "@/components/ComplianceExportPanel";
import DateAuditPanel from "@/components/DateAuditPanel";

export default function AdminCompliance() {
  return (
    <AdminShell
      title="Compliance & Audits"
      section="compliance"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Bundle records into OSHA/DOT-ready compliance exports, and audit timestamp consistency
          across daily reports (catch back-dating, missed submissions, or device-clock skew before
          an auditor does).
        </p>
      }
    >
      <div className="space-y-4">
        <ComplianceExportPanel />
        <DateAuditPanel />
      </div>
    </AdminShell>
  );
}
