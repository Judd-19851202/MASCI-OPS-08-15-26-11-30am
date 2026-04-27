import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Printer, Loader2, Trash2, Mail, AlertOctagon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { formatDateLong } from "@/lib/utils";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import { EmailReportDialog } from "@/components/EmailReportDialog";

const KV = ({ label, value, full = false }) => (
  <div className={full ? "sm:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      {label}
    </div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
      {value || "—"}
    </div>
  </div>
);

const StatusPill = ({ status }) => {
  const map = {
    pass: { cls: "bg-emerald-600 text-white", label: "PASS" },
    fail: { cls: "bg-red-700 text-white", label: "FAIL" },
    na: { cls: "bg-slate-500 text-white", label: "N/A" },
  };
  const v = map[status] || { cls: "bg-slate-300 text-slate-700", label: "—" };
  return (
    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded text-[10px] font-mono font-black tracking-[0.1em] ${v.cls}`}>
      {v.label}
    </span>
  );
};

export default function ViewEquipmentInspection() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emailOpen, setEmailOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/equipment-inspections/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error("Inspection not found");
        navigate("/admin/equipment");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [id, navigate]);

  useEffect(() => {
    if (!loading && data) maybeAutoPrint();
  }, [loading, data]);

  const onDelete = async () => {
    if (!window.confirm("Permanently delete this equipment inspection?")) return;
    try {
      await api.delete(`/equipment-inspections/${id}`);
      toast.success("Deleted");
      navigate("/admin/equipment");
    } catch {
      toast.error("Could not delete");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 animate-spin text-red-700" />
      </div>
    );
  }
  if (!data) return null;

  const fail = (data.fail_count || 0) > 0;

  return (
    <div className="min-h-screen bg-slate-50 print:bg-white pb-32 print:pb-0">
      <PrintWatermark />
      <div className="caution-stripe print:hidden" />

      <header className="bg-slate-900 border-b-4 border-red-700 print:hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link
            to="/admin/equipment"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> All Inspections
          </Link>
          <MasciLogo variant="mark" size="md" />
          <div className="flex items-center gap-2">
            <Button onClick={() => setEmailOpen(true)} className="h-10 px-3 bg-slate-700 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="email-btn">
              <Mail className="w-4 h-4 mr-1" /> Email
            </Button>
            <Button onClick={() => printReport()} className="h-10 px-3 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="print-btn">
              <Printer className="w-4 h-4 mr-1" /> Print
            </Button>
            <Button onClick={onDelete} variant="outline" className="h-10 px-3 border-2 border-red-700 text-red-700 hover:bg-red-50 font-bold uppercase tracking-wide text-xs" data-testid="delete-btn">
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 print:py-0 space-y-5">
        <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">Equipment Pre-Op Inspection</span>
              <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
                {data.equipment_type} · {data.equipment_unit}
              </h1>
              <div className="text-sm text-slate-600 mt-2">
                {formatDateLong(data.inspection_date)} · {data.inspection_time} · {data.location}
              </div>
            </div>
            {fail && (
              <div className="bg-red-50 border-2 border-red-700 rounded px-4 py-2 flex items-center gap-2">
                <AlertOctagon className="w-5 h-5 text-red-700" />
                <span className="font-display font-black text-red-700 text-sm uppercase tracking-wide">
                  Fail — Out of Service
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
          <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">Project & Operator</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label="Project" value={data.project_name} />
            <KV label="Project #" value={data.project_number} />
            <KV label="Location" value={data.location} full />
            <KV label="Operator" value={data.operator_name} />
            <KV label="Date / Time" value={`${data.inspection_date} ${data.inspection_time}`} />
          </div>
        </div>

        <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
          <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">Equipment</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label="Type" value={data.equipment_type} />
            <KV label="Unit" value={data.equipment_unit} />
            <KV label="Make" value={data.equipment_make} />
            <KV label="Model" value={data.equipment_model} />
            <KV label="Serial #" value={data.equipment_serial} />
            <KV label="Hour Meter / Odometer" value={data.hour_meter || data.odometer} />
          </div>
        </div>

        {/* Tally */}
        <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
          <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">Inspection Summary</h2>
          <div className="flex flex-wrap items-center gap-4">
            <div className="text-center">
              <div className="font-display text-3xl font-black text-emerald-700" data-testid="view-pass-count">{data.pass_count || 0}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">Pass</div>
            </div>
            <div className="text-center">
              <div className="font-display text-3xl font-black text-red-700" data-testid="view-fail-count">{data.fail_count || 0}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">Fail</div>
            </div>
            <div className="text-center">
              <div className="font-display text-3xl font-black text-slate-600" data-testid="view-na-count">{data.na_count || 0}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">N/A</div>
            </div>
            <div className="ml-auto">
              <div className={`px-4 py-2 rounded font-mono text-xs font-black uppercase tracking-[0.2em] ${
                fail ? "bg-red-700 text-white" : "bg-emerald-600 text-white"
              }`}>
                {fail ? "Out of Service" : "Cleared to Operate"}
              </div>
            </div>
          </div>
        </div>

        {/* Checklist sections */}
        {Object.entries(data.checklist || {}).map(([sectionTitle, items]) => (
          <div key={sectionTitle} className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
            <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">{sectionTitle}</h2>
            <div className="space-y-2">
              {Object.entries(items).map(([item, res]) => (
                <div key={item} className="flex items-start justify-between gap-3 py-1.5 border-b border-slate-100 last:border-0">
                  <div className="flex-1 text-sm text-slate-800">
                    {item}
                    {res?.note && (
                      <div className="text-xs text-slate-500 italic mt-0.5">↳ {res.note}</div>
                    )}
                    {res?.photo && (
                      <img
                        src={res.photo}
                        alt="Failure evidence"
                        className="mt-2 w-32 h-24 object-cover rounded border-2 border-red-300"
                      />
                    )}
                  </div>
                  <StatusPill status={res?.status} />
                </div>
              ))}
            </div>
          </div>
        ))}

        {(data.deficiency_notes || data.corrective_actions) && (
          <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
            <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">Notes & Corrective Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <KV label="Deficiencies" value={data.deficiency_notes} />
              <KV label="Corrective Actions" value={data.corrective_actions} />
            </div>
          </div>
        )}

        {data.photos && data.photos.length > 0 && (
          <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
            <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">Photos ({data.photos.length})</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {data.photos.map((p, i) => (
                <img key={i} src={p} alt={`Photo ${i + 1}`} className="w-full aspect-[4/3] object-cover rounded border border-slate-200" />
              ))}
            </div>
          </div>
        )}

        {data.operator_signature && (
          <div className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 print-section">
            <h2 className="font-display text-xl font-black text-slate-900 mb-4 pb-2 border-b-2 border-slate-200">Sign-Off</h2>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">Operator: {data.operator_name}</div>
            <img src={data.operator_signature} alt="Operator signature" className="max-h-32 border-b-2 border-slate-300" />
          </div>
        )}
      </main>

      <EmailReportDialog
        open={emailOpen}
        onOpenChange={setEmailOpen}
        kind="equipment-inspection"
        recordId={id}
        record={data}
      />
    </div>
  );
}
