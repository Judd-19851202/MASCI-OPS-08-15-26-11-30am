import React from "react";
import { Building2 } from "lucide-react";
import MasterListPanel from "@/components/MasterListPanel";
import { clearSupplierCache } from "@/components/SupplierCombo";

/**
 * MASCI Supplier / Subcontractor List — single-add + table + edit + delete +
 * bulk XLSX. Feeds Daily-Report Sections 05 (Subcontractors) and 08
 * (Material Deliveries) plus every other supplier dropdown.
 */
const SupplierMasterPanel = () => (
  <MasterListPanel
    title="MASCI Supplier & Subcontractor List"
    icon={Building2}
    accent="amber"
    testIdPrefix="supplier-master"
    listEndpoint="/suppliers"
    statusEndpoint="/admin/suppliers/status"
    createEndpoint="/admin/suppliers"
    updateEndpoint="/admin/suppliers/{id}"
    deleteEndpoint="/admin/suppliers/{id}"
    uploadEndpoint="/admin/suppliers/upload"
    uploadAccept=".xlsx,.xlsm,.csv"
    uploadHint="XLSX or CSV — first column is the company name · max 10 MB"
    fields={[
      { key: "name", label: "Company Name", required: true, placeholder: "Acme Asphalt LLC" },
    ]}
    itemLabel={(r) => r.name}
    emptyState="No suppliers / subs yet — add one above or upload an .xlsx."
    entitySingular="supplier"
    onChange={clearSupplierCache}
  />
);

export default SupplierMasterPanel;
