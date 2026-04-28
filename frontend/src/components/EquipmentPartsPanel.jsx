import { useEffect, useRef, useState } from "react";
import { Wrench, UploadCloud, Loader2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

/**
 * Admin-only panel for bulk-uploading the equipment parts catalog.
 * Accepts .xlsx or .csv with columns:
 *   Unit Number | Category | Name | Part Number | Qty | Size | Position | Ply | Brand | Notes
 * Category must be one of: filters / cutting_edges / wiper_blades / tires / other_wear_items
 * (case-insensitive, spaces or dashes accepted).
 */
const EquipmentPartsPanel = () => {
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const loadStatus = async () => {
    try {
      const r = await api.get("/admin/equipment-parts/status");
      setStatus(r.data);
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => { loadStatus(); }, []);

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/\.(xlsx|xls|csv)$/i.test(file.name)) {
      toast.error("Please pick a .xlsx or .csv file");
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
      const r = await api.post("/admin/equipment-parts/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(
        `Parts catalog updated — ${r.data.units_written} units (${r.data.rows_total - r.data.rows_skipped} parts).`
      );
      await loadStatus();
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message || "Upload failed";
      toast.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div
      className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-6"
      data-testid="equipment-parts-panel"
    >
      <div className="flex items-start gap-3 mb-3">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
          <Wrench className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h3 className="font-display text-lg font-black text-slate-900">
            Equipment Parts Catalog
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            Per-unit wearable parts (filters, cutting edges, wiper blades, tires, other) for field
            mechanics — they pull up a unit and order parts on the way to the PM service.
          </p>
        </div>
      </div>

      <div className="flex items-baseline gap-3 flex-wrap mb-3">
        <span className="font-display text-2xl font-black text-slate-900" data-testid="parts-count">
          {status?.count ?? "—"}
        </span>
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
          Units in catalog
        </span>
        {status?.last_updated && (
          <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            Updated {new Date(status.last_updated).toLocaleString()}
          </span>
        )}
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded p-3 text-xs text-slate-600 mb-3">
        <strong className="text-slate-800">Required columns:</strong>{" "}
        <code className="font-mono">Unit Number</code>, <code className="font-mono">Category</code>,
        <code className="font-mono">Name</code>, <code className="font-mono">Part Number</code>.{" "}
        <strong className="text-slate-800">Optional:</strong>{" "}
        <code className="font-mono">Qty, Size, Position, Ply, Brand, Notes</code>.{" "}
        <strong className="text-slate-800">Category</strong> must be one of:{" "}
        <code className="font-mono">filters · cutting_edges · wiper_blades · tires · other_wear_items</code>.
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={onFile}
          className="hidden"
          data-testid="parts-upload-input"
        />
        <Button
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="h-10 px-4 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-xs"
          data-testid="parts-upload-btn"
        >
          {uploading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <UploadCloud className="w-4 h-4 mr-1" />}
          {uploading ? "Uploading…" : "Pick .xlsx / .csv"}
        </Button>
        <Button
          onClick={loadStatus}
          variant="outline"
          className="h-10 px-3 text-xs uppercase font-bold tracking-wide"
          data-testid="parts-refresh-btn"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
        </Button>
      </div>
    </div>
  );
};

export default EquipmentPartsPanel;
