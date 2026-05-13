// AdminTraining.jsx — /admin/training section page (iter83)
import React from "react";
import AdminShell from "@/components/AdminShell";
import AdminTrainingResourcesPanel from "@/components/AdminTrainingResourcesPanel";
import AdminSafetyFormsPanel from "@/components/AdminSafetyFormsPanel";

export default function AdminTraining() {
  return (
    <AdminShell
      title="Training & Forms"
      section="training"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Bilingual training resources surfaced on the Training Hub, and the printable safety-forms
          library (issuance, training acknowledgments, returns) used by Field Leadership.
        </p>
      }
    >
      <div className="space-y-4">
        <AdminTrainingResourcesPanel />
        <AdminSafetyFormsPanel />
      </div>
    </AdminShell>
  );
}
