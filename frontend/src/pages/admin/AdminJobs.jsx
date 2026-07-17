// AdminJobs.jsx — /admin/jobs section page (iter83)
import React from "react";
import { Link } from "react-router-dom";
import AdminShell from "@/components/AdminShell";
import AdminJobMasterPanel from "@/components/AdminJobMasterPanel";
import SitePostersPanel from "@/components/SitePostersPanel";
import AdminBannersPanel from "@/components/AdminBannersPanel";
import LocationIntelligencePanel from "@/components/admin/LocationIntelligencePanel";

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
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" data-testid="admin-jobs-cost-registry-link-card">
          Enterprise Spine foundation is live. Manage the universal cost-code library in the dedicated registry.
          <Link to="/admin/cost-registry" className="ml-2 font-semibold underline" data-testid="admin-jobs-cost-registry-link">Open cost registry</Link>
        </div>
        <AdminJobMasterPanel />
        <LocationIntelligencePanel />
        <SitePostersPanel />
        <AdminBannersPanel />
      </div>
    </AdminShell>
  );
}
