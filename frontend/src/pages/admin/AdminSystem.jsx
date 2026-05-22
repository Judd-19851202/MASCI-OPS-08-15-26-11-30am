// AdminSystem.jsx — /admin/system section page (iter83 + iter84)
//
// iter84 cleanup: the persistence-health banner (the "your data will be
// deleted on next redeploy" warning) was moved here from the Admin
// Overview top so the dashboard reads as a glance and all
// disaster-recovery surface area lives in one place.
//
// Also dropped from render in iter84:
//   - StoredBackupsPanel (on-server disk backups — superseded by R2)
//   - AdminSignatureMigrationPanel (one-time DB→R2 migration, complete)
// Their component files remain in the repo and can be re-mounted if
// needed, but they're no longer part of the day-to-day admin surface.
import React from "react";
import AdminShell from "@/components/AdminShell";
import PersistenceHealthBanner from "@/components/PersistenceHealthBanner";
import PreDeploySnapshotPanel from "@/components/PreDeploySnapshotPanel";
import BackupHeroPanel from "@/components/BackupHeroPanel";
import CloudArchivesPanel from "@/components/CloudArchivesPanel";
import AdminBackupVerificationPanel from "@/components/AdminBackupVerificationPanel";
import RestoreBackupPanel from "@/components/RestoreBackupPanel";
import CrewRecoveryPanel from "@/components/CrewRecoveryPanel";
import AdminReferenceLookup from "@/components/AdminReferenceLookup";

export default function AdminSystem() {
  return (
    <AdminShell
      title="System & Backups"
      section="system"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Disaster-recovery toolkit. Trigger a backup, browse the Cloudflare R2 cloud archive
          library, run weekly verification on demand, restore from a file or directly from a
          cloud archive, and recover terminated crew data. Keep the verification cron green and
          you'll get a positive weekly heartbeat email.
        </p>
      }
    >
      <div className="space-y-4">
        {/* iter338 · Admin Reference Lookup — top of System tools */}
        <AdminReferenceLookup />
        {/* Pre-deploy snapshot freshness — top priority */}
        <PreDeploySnapshotPanel />
        {/* Persistence banner — auto-renders only on ephemeral Mongo */}
        <PersistenceHealthBanner />
        <BackupHeroPanel />
        <CloudArchivesPanel />
        <AdminBackupVerificationPanel />
        <RestoreBackupPanel />
        <CrewRecoveryPanel />
      </div>
    </AdminShell>
  );
}
