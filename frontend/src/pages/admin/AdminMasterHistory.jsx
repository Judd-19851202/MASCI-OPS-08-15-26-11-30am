// AdminMasterHistory — Iter141. Dedicated full-page route for OSHA/
// insurance audit. Renders AssetHistoryTimeline with CSV + PDF export
// buttons. One component drives both equipment and employee views.
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, FileDown, Printer, Loader2, Truck, User } from "lucide-react";
import axios from "axios";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import AssetHistoryTimeline from "@/components/AssetHistoryTimeline";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminMasterHistory({ kind }) {
  const { id } = useParams();
  const [master, setMaster] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    const url = kind === "equipment"
      ? `${API}/master-lookup/equipment/${id}/where-used`
      : `${API}/master-lookup/employees/${id}/where-used`;
    axios.get(url)
      .then((r) => setMaster(r.data?.master || null))
      .catch(() => setMaster(null))
      .finally(() => setLoading(false));
  }, [id, kind]);

  const downloadUrl = (ext) => kind === "equipment"
    ? `${API}/master-lookup/equipment/${id}/history.${ext}`
    : `${API}/master-lookup/employees/${id}/history.${ext}`;

  const masterTitle = kind === "equipment"
    ? (master?.unit_number || master?.make_model || id)
    : (master?.name || [master?.first_name, master?.last_name].filter(Boolean).join(" ") || master?.employee_id || id);

  const kicker = kind === "equipment"
    ? "ADMIN · ASSET HISTORY"
    : "ADMIN · EMPLOYEE HISTORY";

  const backTo = kind === "equipment" ? "/admin/equipment" : "/admin/people";

  return (
    <AdminShell title={`${kind === "equipment" ? "Asset" : "Employee"} History`} kicker={kicker}>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <Link to={backTo}>
          <Button variant="outline" className="border-2" data-testid="master-history-back">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back
          </Button>
        </Link>
        <div className="flex gap-2">
          <a href={downloadUrl("csv")} download data-testid="master-history-csv">
            <Button variant="outline" className="border-2 border-emerald-700 text-emerald-800 hover:bg-emerald-50">
              <FileDown className="w-4 h-4 mr-1" /> Export CSV
            </Button>
          </a>
          <a href={downloadUrl("pdf")} target="_blank" rel="noreferrer" data-testid="master-history-pdf">
            <Button className="bg-red-700 hover:bg-red-800 text-white">
              <Printer className="w-4 h-4 mr-1" /> Export PDF
            </Button>
          </a>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>
      ) : !master ? (
        <div className="border-2 border-red-200 bg-red-50 rounded-md p-4 text-red-800 text-sm" data-testid="master-history-notfound">
          Master record not found.
        </div>
      ) : (
        <>
          <div className="bg-white border-2 border-slate-300 rounded-md p-5 mb-5" data-testid="master-history-header">
            <div className="flex items-start gap-3">
              {kind === "equipment"
                ? <Truck className="w-8 h-8 text-slate-400 mt-1" />
                : <User className="w-8 h-8 text-slate-400 mt-1" />}
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-700 font-bold">
                  {kind === "equipment" ? "Equipment Master" : "Employee Master"}
                </div>
                <h2 className="font-display text-3xl font-black text-slate-900 leading-tight mt-1 break-words">{masterTitle}</h2>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600 mt-2">
                  {kind === "equipment" ? (
                    <>
                      {master.make_model && <span><strong>Make/Model:</strong> {master.make_model}</span>}
                      {master.category && <span><strong>Category:</strong> {master.category}</span>}
                      {(master.vin || master.serial_number) && <span><strong>VIN/Serial:</strong> {master.vin || master.serial_number}</span>}
                    </>
                  ) : (
                    <>
                      {master.employee_id && <span><strong>Emp ID:</strong> {master.employee_id}</span>}
                      {master.role && <span><strong>Role:</strong> {master.role}</span>}
                      {master.trade && <span><strong>Trade:</strong> {master.trade}</span>}
                      {master.email && <span><strong>Email:</strong> {master.email}</span>}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <AssetHistoryTimeline kind={kind} masterId={id} />
        </>
      )}
    </AdminShell>
  );
}
