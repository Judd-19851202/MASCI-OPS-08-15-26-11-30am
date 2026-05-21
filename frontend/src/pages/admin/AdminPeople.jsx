// AdminPeople.jsx — /admin/people section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import AdminPMPanel from "@/components/AdminPMPanel";
import AdminShopUsersPanel from "@/components/AdminShopUsersPanel";
import AdminHRUsersPanel from "@/components/AdminHRUsersPanel";
import AdminFieldLeadershipUsersPanel from "@/components/AdminFieldLeadershipUsersPanel";
import AdminSafetyUsersPanel from "@/components/AdminSafetyUsersPanel";
import AdminDispatchUsersPanel from "@/components/AdminDispatchUsersPanel";
import AdminAccessControlPanel from "@/components/AdminAccessControlPanel";
import AdminUnifiedDirectoryPanel from "@/components/AdminUnifiedDirectoryPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";

export default function AdminPeople() {
  return (
    <AdminShell
      title="People & Access"
      section="people"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          <strong>Multi-Portal accounts</strong> let one person sign in across multiple portals with a
          single master password — manage them in the <em>Access Control Center</em>. <strong>Single-portal users</strong> (one PM, one Shop user,
          one HR user) live in their own panels below.
        </p>
      }
    >
      <div className="space-y-4">
        <AdminAccessControlPanel />
        <AdminUnifiedDirectoryPanel />
        <AdminPMPanel />
        <AdminShopUsersPanel />
        <AdminHRUsersPanel />
        <AdminFieldLeadershipUsersPanel />
        <AdminSafetyUsersPanel />
        <AdminDispatchUsersPanel />
        <EmployeeMasterPanel />
      </div>
    </AdminShell>
  );
}
