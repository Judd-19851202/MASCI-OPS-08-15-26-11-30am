// AdminDriverIntel.jsx — DCP-1 · Admin view of the Driver Command Profile.
// Replaces the legacy OIS-1C single-panel; the shared component now
// renders identity, operations, safety, training, equipment, motive,
// and mapping health (admin-only) all in one place.
import React from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import DriverCommandProfile from "@/components/DriverCommandProfile";
import { usePageTitle } from "@/lib/usePageTitle";

export default function AdminDriverIntel() {
  const { driverKey } = useParams();
  const nav = useNavigate();
  usePageTitle("Driver Command Profile · Admin · MASCI");

  return (
    <AdminShell title="Driver Command Profile">
      <div className="max-w-5xl mx-auto" data-testid="admin-driver-intel-page">
        <div className="flex items-center justify-between gap-3 mb-4">
          <Button variant="outline" size="sm" onClick={() => nav(-1)} data-testid="admin-driver-intel-back">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back
          </Button>
          <Link
            to="/admin/integrations"
            className="text-xs font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800"
            data-testid="admin-driver-intel-mapping-link"
          >
            Open Integration Center →
          </Link>
        </div>
        <DriverCommandProfile driverKey={driverKey} />
      </div>
    </AdminShell>
  );
}
