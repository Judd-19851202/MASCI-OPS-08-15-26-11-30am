import { useEffect, useRef, useState } from "react";
import { Truck, UploadCloud, Loader2, RefreshCw, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

/**
 * Admin-only panel for replacing the MASCI Equipment List.xlsx.
 * One click → upload → reseeds equipment_master + equipment_units → all the
 * dropdowns across the app refresh with the new fleet.
 */
const EquipmentMasterPanel = () => {
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const loadStatus = async () => {
    try {
      const r = await api.get("/admin/equipment-master/status");
      setStatus(r.data);
    } catch (e) {
      console.error("equipment-master status failed", e);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/\.xlsx?$/i.test(file.name)) {
      toast.error("Please pick a .xlsx file");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      toast.error("File too big — max 25 MB");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post("/admin/equipment-master/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const cats = Object.keys(r.data?.category_counts || {}).length;
      toast.success(
        `Fleet updated — ${r.data.count} units across ${cats} categories.`
      );
      await loadStatus();
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Upload failed";
      toast.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const cats = status?.categories || {};
  const total = status?.count || 0;
  const top = Object.entries(cats).slice(0, 6);
  const lastUpdated = status?.last_updated
    ? new Date(status.last_updated)
    : null;

  return (
    <div
      className="mb-8 bg-white border-2 border-slate-200 rounded-md overflow-hidden shadow-sm"
      data-testid="equipment-master-panel"
    >
      <div className="bg-slate-900 text-white px-5 py-3 flex items-center gap-3">
        <Truck className="w-5 h-5 text-amber-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold">
          MASCI Equipment Master Fleet
        </span>
      </div>

      <div className="p-5 grid md:grid-cols-[1.2fr_1fr] gap-5 items-start">
        {/* Left — stats */}
        <div>
          <div className="flex items-baseline gap-3">
            <span
              className="font-display text-5xl font-black text-slate-900"
              data-testid="equipment-master-total"
            >
              {total}
            </span>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              units in fleet
            </span>
          </div>
          {lastUpdated && (
            <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Last updated {lastUpdated.toLocaleString()}
            </div>
          )}
          {top.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {top.map(([c, n]) => (
                <span
                  key={c}
                  className="text-[11px] font-mono bg-slate-100 border border-slate-200 px-2 py-0.5 rounded"
                >
                  {c}{" "}
                  <span className="text-red-700 font-bold">{n}</span>
                </span>
              ))}
              {Object.keys(cats).length > top.length && (
                <span className="text-[11px] font-mono text-slate-500 px-2 py-0.5">
                  +{Object.keys(cats).length - top.length} more
                </span>
              )}
            </div>
          )}
          <p className="text-sm text-slate-600 mt-4 max-w-md">
            Drop in an updated <code>Equipment List.xlsx</code> to refresh every
            equipment dropdown across the Hub — Pre-Op, Daily Reports, etc.
            Operators can still type custom values not in the fleet.
          </p>
        </div>

        {/* Right — upload */}
        <div className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-md p-5 text-center">
          <UploadCloud className="w-8 h-8 text-red-700 mx-auto mb-2" />
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold mb-1">
            Replace fleet from XLSX
          </div>
          <p className="text-[11px] text-slate-500 mb-3">
            Reads the <strong>Louis</strong> sheet by default · max 25&nbsp;MB.
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xlsm,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={onFile}
            className="hidden"
            data-testid="equipment-master-file-input"
          />
          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <Button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs h-10 px-5"
              data-testid="equipment-master-upload-btn"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                  Uploading…
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4 mr-1.5" /> Pick .xlsx
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={loadStatus}
              disabled={uploading}
              className="h-10 px-3 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 font-mono uppercase tracking-wide text-[11px]"
              data-testid="equipment-master-refresh-btn"
              title="Refresh status"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EquipmentMasterPanel;
