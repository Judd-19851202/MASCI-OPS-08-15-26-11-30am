// AdminJobs.jsx — /admin/jobs section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import AdminJobMasterPanel from "@/components/AdminJobMasterPanel";
import SitePostersPanel from "@/components/SitePostersPanel";
import AdminBannersPanel from "@/components/AdminBannersPanel";

export default function AdminJobs() {
  return (
    <AdminShell
      title="Jobs & Field"
      section="jobs"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Manage the job master list (number, name, PM assignment, status), printable site posters
          that get pinned in every job trailer, and the Hub banner system that broadcasts
          announcements to the entire crew.
        </p>
      }
    >
      <div className="space-y-4">
        <AdminJobMasterPanel />
        <SitePostersPanel />
        <AdminBannersPanel />
      </div>
    </AdminShell>
  );
}
