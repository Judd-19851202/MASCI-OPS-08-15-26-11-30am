// AdminPeople.jsx — /admin/people section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import AdminPMPanel from "@/components/AdminPMPanel";
import AdminShopUsersPanel from "@/components/AdminShopUsersPanel";
import AdminHRUsersPanel from "@/components/AdminHRUsersPanel";
import AdminSafetyUsersPanel from "@/components/AdminSafetyUsersPanel";
import AdminAccessControlPanel from "@/components/AdminAccessControlPanel";
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
        <AdminPMPanel />
        <AdminShopUsersPanel />
        <AdminHRUsersPanel />
        <AdminSafetyUsersPanel />
        <EmployeeMasterPanel />
      </div>
    </AdminShell>
  );
}
