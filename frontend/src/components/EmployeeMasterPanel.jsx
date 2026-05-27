import React from "react";
import { Users } from "lucide-react";
import MasterListPanel from "@/components/MasterListPanel";
import { clearEmployeeCache } from "@/components/EmployeeCombo";

/**
 * MASCI Employee Roster — single-add + table + edit + delete + bulk XLSX.
 * Drives every employee dropdown across the app.
 */
const EmployeeMasterPanel = ({ readOnly = false }) => (
  <MasterListPanel
    title="MASCI Employee Roster"
    icon={Users}
    accent="amber"
    testIdPrefix="employee-master"
    readOnly={readOnly}
    listEndpoint="/employees"
    statusEndpoint="/admin/employees/status"
    createEndpoint="/admin/employees"
    updateEndpoint="/admin/employees/{id}"
    deleteEndpoint="/admin/employees/{id}"
    uploadEndpoint="/admin/employees/upload"
    exportEndpoint="/admin/employees/export"
    archiveEndpoint="/admin/employees/archive"
    restoreEndpoint="/admin/employees/{id}/restore"
    uploadAccept=".xlsx,.xlsm,.csv"
    uploadHint="XLSX or CSV (Name, Employee ID, Trade, Role, Crew, Email, Phone) · max 25 MB"
    fields={[
      { key: "name",        label: "Name",        required: true, placeholder: "Last, First" },
      { key: "employee_id", label: "Employee ID", placeholder: "EMP-1234" },
      { key: "trade",       label: "Trade",       placeholder: "Operator" },
      { key: "role",        label: "Role",        placeholder: "Foreman" },
      { key: "crew",        label: "Crew",        placeholder: "Crew A" },
      { key: "email",       label: "Email",       placeholder: "name@mascigc.com" },
      { key: "phone",       label: "Phone",       placeholder: "555-0123" },
    ]}
    itemLabel={(r) => r.name}
    emptyState="No employees yet — add one above or upload an .xlsx."
    entitySingular="employee"
    onChange={clearEmployeeCache}
  />
);

export default EmployeeMasterPanel;
