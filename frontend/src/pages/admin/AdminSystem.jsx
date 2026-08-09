import React from "react";
import { AlertTriangle, Database, HardDrive, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";

import CrewRecoveryPanel from "@/components/CrewRecoveryPanel";
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";

export default function AdminSystem() {
  return (
    <div className="min-h-screen bg-slate-50" data-testid="admin-system-recovery-root">
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        shellTheme="admin"
        pageTitle="System Recovery"
        subtitle="Exceptional reconstruction only. Canonical backup and diagnostics truth lives elsewhere."
        sideNav={<SideNavV3 variant="admin" onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
    >
        <AdminBreadcrumb crumbs={[{ label: "System Recovery" }]} testidPrefix="admin-system-breadcrumb" />

        <section className="mb-6 rounded-[var(--radius-card)] border border-amber-200 bg-amber-50 px-4 py-4 shadow-sm" data-testid="admin-system-recovery-banner">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5 text-amber-700" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-800">Progressive disclosure</div>
              <h2 className="mt-1 font-display text-xl font-black tracking-tight text-slate-900">This page is not the Admin OS landing.</h2>
              <p className="mt-2 text-sm text-slate-700">
                Backup integrity, R2 posture, restore evidence, and runtime diagnostics now belong to their governed canonical surfaces.
                Keep this page for exceptional recovery and destructive reconstruction only.
              </p>
            </div>
          </div>
        </section>

        <section className="mb-6 grid gap-4 lg:grid-cols-3" data-testid="admin-system-recovery-links">
          <Link
            to="/admin/storage-recovery"
            className="rounded-[var(--radius-card)] border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:shadow-md transition-all"
            data-testid="admin-system-link-storage"
          >
            <HardDrive className="h-5 w-5 text-sky-700" />
            <div className="mt-3 font-semibold text-slate-900">Storage & Recovery</div>
            <p className="mt-1 text-sm text-slate-600">Backups, manifests, retention, restore drills, and integrity verification.</p>
          </Link>
          <Link
            to="/admin/diagnostics"
            className="rounded-[var(--radius-card)] border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:shadow-md transition-all"
            data-testid="admin-system-link-diagnostics"
          >
            <Database className="h-5 w-5 text-teal-700" />
            <div className="mt-3 font-semibold text-slate-900">Diagnostics</div>
            <p className="mt-1 text-sm text-slate-600">System health, workers, deploy readiness, and governed technical probes.</p>
          </Link>
          <Link
            to="/admin/maintenance"
            className="rounded-[var(--radius-card)] border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:shadow-md transition-all"
            data-testid="admin-system-link-maintenance"
          >
            <AlertTriangle className="h-5 w-5 text-rose-700" />
            <div className="mt-3 font-semibold text-slate-900">Maintenance</div>
            <p className="mt-1 text-sm text-slate-600">Safe maintenance and reviewed operations. Start there before any destructive recovery.</p>
          </Link>
        </section>

        <CrewRecoveryPanel />
      </PortalShell>
    </div>
  );
}
