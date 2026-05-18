// AdminTraining.jsx — /admin/training section page (iter83 + iter84)
//
// Houses both the configuration panels (training resources, safety forms)
// AND the field-adoption analytics cards (scans, bilingual usage,
// calculator usage). The analytics cards were relocated here from the
// Admin Overview page in iter84 — they're tightly coupled to "how is
// the field actually using our training/forms?", so they belong with
// the rest of training rather than crowding the dashboard glance.
import React from "react";
import AdminShell from "@/components/AdminShell";
import AdminTrainingResourcesPanel from "@/components/AdminTrainingResourcesPanel";
import AdminSafetyFormsPanel from "@/components/AdminSafetyFormsPanel";
import TrainingStatsStripe from "@/components/TrainingStatsStripe";
import BilingualAdoptionCard from "@/components/BilingualAdoptionCard";
import CalculatorUsageCard from "@/components/CalculatorUsageCard";

export default function AdminTraining() {
  return (
    <AdminShell
      title="Training & Forms"
      section="training"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Bilingual training resources surfaced on the Operational Guidance Center, the printable safety-forms
          library used by Field Leadership, and the field-adoption analytics that show how the
          crew is actually using each one.
        </p>
      }
    >
      <div className="space-y-4">
        {/* ── Field adoption analytics ── */}
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mt-1 mb-1">
          Field adoption
        </div>
        <TrainingStatsStripe />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BilingualAdoptionCard />
          <CalculatorUsageCard />
        </div>

        {/* ── Configuration ── */}
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mt-4 mb-1">
          Configuration
        </div>
        <AdminTrainingResourcesPanel />
        <AdminSafetyFormsPanel />
      </div>
    </AdminShell>
  );
}
