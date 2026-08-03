import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import OperationsControlCases from "@/pages/OperationsControlCases";
import { OperationsControlShell } from "@/components/operations/OperationsControlShell";

export default function OperationsControlCasesRoute() {
  return (
    <OperationsControlShell
      pageTitle="Operations Cases"
      subtitle="Review active cases, priorities, and next steps in one place."
      crumbs={[{ label: "Operations Control" }, { label: "Operations Cases" }]}
      primaryActions={(
        <Link to="/admin/operations-control" className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100" data-testid="occ-cases-route-back-link">
          <ArrowLeft className="h-4 w-4" /> Back to Operations Control
        </Link>
      )}
      testId="occ-cases-route-page"
    >
      <div className="w-full max-w-[1600px]">
        <OperationsControlCases />
      </div>
    </OperationsControlShell>
  );
}
