// AdminSystem.jsx — /admin/system section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import BackupHeroPanel from "@/components/BackupHeroPanel";
import StoredBackupsPanel from "@/components/StoredBackupsPanel";
import CloudArchivesPanel from "@/components/CloudArchivesPanel";
import AdminBackupVerificationPanel from "@/components/AdminBackupVerificationPanel";
import AdminSignatureMigrationPanel from "@/components/AdminSignatureMigrationPanel";
import RestoreBackupPanel from "@/components/RestoreBackupPanel";
import CrewRecoveryPanel from "@/components/CrewRecoveryPanel";

export default function AdminSystem() {
  return (
    <AdminShell
      title="System & Backups"
      section="system"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Disaster-recovery toolkit. Trigger a manual backup, browse stored archives (local + R2),
          run weekly verification on demand, restore a record, and recover terminated crew data.
          Keep the verification cron green and you'll get a positive weekly heartbeat email.
        </p>
      }
    >
      <div className="space-y-4">
        <BackupHeroPanel />
        <StoredBackupsPanel />
        <CloudArchivesPanel />
        <AdminBackupVerificationPanel />
        <AdminSignatureMigrationPanel />
        <RestoreBackupPanel />
        <CrewRecoveryPanel />
      </div>
    </AdminShell>
  );
}
