import React from "react";
import { FileDown, Download, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

/**
 * DR-UNIFY-002 · Approved Daily Reports · Export Panel
 * -----------------------------------------------------
 * Management-side panel that lists APPROVED Daily Reports (legacy +
 * modern in one unified list) and exposes an EN-only canonical PDF
 * download for each row.
 *
 * Rules baked in:
 *   • Only approved records are ever surfaced — backend enforces via
 *     lifecycle state (legacy) or an `accept` audit entry (modern).
 *   • PM tokens see only their scoped projects (backend enforces).
 *   • Admin/HR/Exec see all approved reports (backend enforces).
 *   • This component is used ONLY on management dashboards
 *     (PM/Admin Operational Intelligence). It must NEVER be mounted
 *     inside the field Daily Report form. That contract is enforced
 *     by a pytest guardrail.
 */
export function DrV2ApprovedReportsPanel({
  audience = "management",
  emptyLabel = "No approved Daily Reports yet in scope.",
}) {
  const [items, setItems] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [downloading, setDownloading] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const { data } = await api.get("/daily-reports/approved", { params: { limit: 50 } });
        if (!alive) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
      } catch (e) {
        if (!alive) return;
        const status = e?.response?.status;
        setError(status === 401 ? "Sign in required." : (e?.message || "Load failed"));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  async function downloadPdf(reportId) {
    setDownloading(reportId);
    try {
      const resp = await api.get(
        `/daily-reports/${encodeURIComponent(reportId)}/pdf`,
        { responseType: "blob" },
      );
      const blob = new Blob([resp.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `MASCI_Daily_Report_${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) {
      const status = e?.response?.status;
      let msg;
      if (status === 409) msg = "Report is not yet approved — export blocked.";
      else if (status === 404) msg = "Report not found or outside your project scope.";
      else if (status === 401) msg = "Sign in required.";
      else msg = e?.message || "Download failed";
      setError(msg);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <section
      data-testid={`approved-daily-reports-panel-${audience}`}
      className="rounded-lg border border-neutral-200 bg-white"
    >
      <header className="px-4 py-3 border-b border-neutral-200 flex items-baseline justify-between gap-3 flex-wrap">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-neutral-500">
            Approved Daily Reports · Export
          </div>
          <div className="text-sm text-neutral-700">
            Canonical English record-of-truth PDF · legacy + modern records · management access only
          </div>
        </div>
        <FileDown className="w-4 h-4 text-neutral-400" aria-hidden />
      </header>

      {loading ? (
        <div
          className="px-4 py-6 text-sm text-neutral-500 flex items-center gap-2"
          data-testid={`approved-daily-reports-loading-${audience}`}
        >
          <Loader2 className="w-4 h-4 animate-spin" /> Loading approved reports…
        </div>
      ) : error ? (
        <div
          className="px-4 py-6 text-sm text-red-700 flex items-center gap-2"
          data-testid={`approved-daily-reports-error-${audience}`}
        >
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      ) : items.length === 0 ? (
        <div
          className="px-4 py-6 text-sm text-neutral-500"
          data-testid={`approved-daily-reports-empty-${audience}`}
        >
          {emptyLabel}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid={`approved-daily-reports-table-${audience}`}>
            <thead className="text-[10px] uppercase text-neutral-500 bg-neutral-50">
              <tr>
                <th className="text-left px-4 py-2">Project</th>
                <th className="text-left px-4 py-2">Report Date</th>
                <th className="text-left px-4 py-2">Supervisor</th>
                <th className="text-left px-4 py-2">Source</th>
                <th className="text-right px-4 py-2">Export</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr
                  key={it.report_id}
                  className="border-t border-neutral-100"
                  data-testid={`approved-daily-reports-row-${it.report_id}`}
                >
                  <td className="px-4 py-2 font-mono text-neutral-800">
                    {it.project_number || "—"}
                    {it.project_name ? (
                      <div className="text-[11px] text-neutral-500 font-sans">
                        {it.project_name}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-2 tabular-nums text-neutral-700">
                    {it.report_date || "—"}
                  </td>
                  <td className="px-4 py-2 text-neutral-700">
                    {it.supervisor_name || "—"}
                  </td>
                  <td className="px-4 py-2 text-[11px] uppercase tracking-wider text-neutral-500">
                    <span
                      className={
                        "inline-block rounded-sm px-1.5 py-0.5 " +
                        (it.source === "legacy"
                          ? "bg-neutral-100 text-neutral-700"
                          : "bg-emerald-50 text-emerald-800")
                      }
                    >
                      {it.source === "legacy" ? "Historical" : "Modern"}
                    </span>
                    {it.field_language && it.field_language !== "en" ? (
                      <span className="ml-2 text-neutral-400">
                        {it.field_language.toUpperCase()} → EN
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      type="button"
                      onClick={() => downloadPdf(it.report_id)}
                      disabled={downloading === it.report_id}
                      className="inline-flex items-center gap-1.5 rounded-md border border-neutral-300 bg-white px-2.5 py-1 text-xs font-semibold text-neutral-800 hover:bg-neutral-50 disabled:opacity-60"
                      data-testid={`approved-daily-reports-download-${it.report_id}`}
                    >
                      {downloading === it.report_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                      PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default DrV2ApprovedReportsPanel;
