// AdminEquipment.jsx — /admin/equipment section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import EquipmentStatusBoard from "@/components/EquipmentStatusBoard";
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import EquipmentPartsPanel from "@/components/EquipmentPartsPanel";
import SupplierMasterPanel from "@/components/SupplierMasterPanel";

export default function AdminEquipment() {
  return (
    <AdminShell
      title="Equipment & Suppliers"
      section="equipment"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Two distinct governed populations live here: the <strong>Equipment Status</strong> board counts
          <strong> inspection / status units</strong> (what has an inspection identity), while the
          <strong> Equipment Master</strong> is the canonical <strong>all-assets</strong> fleet. They are
          intentionally different denominators. Also: the unit master, parts catalog, and suppliers /
          vendors directory. Failed Pre-Op inspections auto-tag a unit out-of-service and route it to your
          Shop Portal.
        </p>
      }
    >
      <div className="space-y-4">
        <EquipmentStatusBoard />
        <EquipmentMasterPanel />
        <EquipmentPartsPanel />
        <SupplierMasterPanel />
      </div>
    </AdminShell>
  );
}
