import { useEffect, useRef, useState } from "react";
import { Users, UploadCloud, Loader2, RefreshCw, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { clearEmployeeCache } from "@/components/EmployeeCombo";

/**
 * Admin-only panel for uploading the MASCI employee roster.
 * Mirrors EquipmentMasterPanel — drop in an .xlsx (or .csv) → every
 * employee dropdown across the app picks up the new roster.
 *
 * Expected columns (case-insensitive):
 *   Name (required) · Employee ID · Trade · Role · Crew · Email · Phone
 */
const EmployeeMasterPanel = () => {
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const loadStatus = async () => {
    try {
      const r = await api.get("/admin/employees/status");
      setStatus(r.data);
    } catch (e) {
      console.error("employees status failed", e);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/\.(xlsx?|csv)$/i.test(file.name)) {
      toast.error("Please pick a .xlsx or .csv file");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File too big — max 10 MB");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post("/admin/employees/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`Roster updated — ${r.data.count} employees.`);
      clearEmployeeCache();
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

  const total = status?.count || 0;
  const lastUpdated = status?.last_updated
    ? new Date(status.last_updated)
    : null;

  return (
    <div
      className="mb-8 bg-white border-2 border-slate-200 rounded-md overflow-hidden shadow-sm"
      data-testid="employee-master-panel"
    >
      <div className="bg-slate-900 text-white px-5 py-3 flex items-center gap-3">
        <Users className="w-5 h-5 text-amber-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold">
          MASCI Employee Roster
        </span>
      </div>

      <div className="p-5 grid md:grid-cols-[1.2fr_1fr] gap-5 items-start">
        <div>
          <div className="flex items-baseline gap-3">
            <span
              className="font-display text-5xl font-black text-slate-900"
              data-testid="employee-master-total"
            >
              {total}
            </span>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              employees on roster
            </span>
          </div>
          {lastUpdated && (
            <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Last updated {lastUpdated.toLocaleString()}
            </div>
          )}
          <p className="text-sm text-slate-600 mt-4 max-w-md">
            Upload an .xlsx or .csv with columns: <code>Name</code>,{" "}
            <code>Employee ID</code>, <code>Trade</code>, <code>Role</code>,{" "}
            <code>Crew</code>, <code>Email</code>, <code>Phone</code>. Only{" "}
            <strong>Name</strong> is required. Foremen will pick from this list
            in Daily Reports + every other crew dropdown.
          </p>
        </div>

        <div className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-md p-5 text-center">
          <UploadCloud className="w-8 h-8 text-red-700 mx-auto mb-2" />
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold mb-1">
            Replace roster
          </div>
          <p className="text-[11px] text-slate-500 mb-3">
            .xlsx or .csv · max 10 MB.
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xlsm,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
            onChange={onFile}
            className="hidden"
            data-testid="employee-master-file-input"
          />
          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <Button
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs h-10 px-5"
              data-testid="employee-master-upload-btn"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                  Uploading…
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4 mr-1.5" /> Pick file
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={loadStatus}
              disabled={uploading}
              className="h-10 px-3 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 font-mono uppercase tracking-wide text-[11px]"
              data-testid="employee-master-refresh-btn"
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

export default EmployeeMasterPanel;
