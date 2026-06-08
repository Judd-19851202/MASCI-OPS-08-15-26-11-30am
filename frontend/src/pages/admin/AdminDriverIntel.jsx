// AdminDriverIntel.jsx — OIS-1C · Driver Command Profile page
// Read-only Motive driver intelligence by mapping key (Motive user_id
// or MASCI employee_id). Reuses the shared MotiveDriverIntelPanel.
import React from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import MotiveDriverIntelPanel from "@/components/MotiveDriverIntelPanel";
import { usePageTitle } from "@/lib/usePageTitle";

export default function AdminDriverIntel() {
  const { driverKey } = useParams();
  const nav = useNavigate();
  usePageTitle("Driver Intel · Admin · MASCI");

  return (
    <AdminShell title="Driver Command Profile">
      <div className="max-w-4xl mx-auto" data-testid="admin-driver-intel-page">
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
        <MotiveDriverIntelPanel driverKey={driverKey} />
      </div>
    </AdminShell>
  );
}
