import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import OperationsControlCases from "@/pages/OperationsControlCases";

export default function OperationsControlCasesRoute() {
  return (
    <section className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8" data-testid="occ-cases-route-page">
      <Link to="/admin/operations-control" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-950" data-testid="occ-cases-route-back-link">
        <ArrowLeft className="h-4 w-4" /> Back to Operations Control Center
      </Link>
      <div className="mt-4">
        <OperationsControlCases />
      </div>
    </section>
  );
}
