import React, { useState } from "react";
import { Download, FileText, FileType2 } from "lucide-react";

/**
 * OpsManualPanel — admin-only download of the Internal System Owner &
 * Operations Manual in both PDF and DOCX format.
 *
 * The manual is generated on-demand by the backend (ops_manual.py) so
 * future edits to the source data re-flow into every fresh download
 * without needing to rebuild or redeploy static assets.
 *
 * Auth: both endpoints require X-Admin-Token. This panel is rendered
 * only inside AdminHub so the token is already in localStorage.
 */

const API = process.env.REACT_APP_BACKEND_URL;

async function downloadManual(format) {
  const token = localStorage.getItem("adminToken");
  if (!token) {
    alert("Admin session expired — please log in again.");
    return;
  }
  const res = await fetch(`${API}/api/admin/ops-manual.${format}`, {
    headers: { "X-Admin-Token": token },
  });
  if (!res.ok) {
    alert(`Download failed (${res.status}) — contact The Judd Group LLC.`);
    return;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `MASCI_HUB_Operations_Manual.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function OpsManualPanel() {
  const [pending, setPending] = useState(null);

  const click = async (format) => {
    setPending(format);
    try {
      await downloadManual(format);
    } finally {
      setPending(null);
    }
  };

  return (
    <section
      className="bg-white border-2 border-slate-900 rounded-md p-6 sm:p-8"
      data-testid="ops-manual-panel"
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-md bg-slate-900 text-white flex items-center justify-center shrink-0">
          <FileText className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
            Admin Only · Internal Document
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900 mt-1">
            System Owner &amp; Operations Manual
          </h2>
          <p className="text-slate-600 text-sm mt-2 max-w-2xl">
            Full architecture, cost breakdown, deployment procedures, failure
            points, maintenance checklist, and V2 recommendations. For The
            Judd Group LLC use only — not for distribution to MASCI staff or
            customers.
          </p>
        </div>
      </div>

      <div className="mt-5 flex flex-col sm:flex-row gap-3">
        <button
          type="button"
          onClick={() => click("pdf")}
          disabled={pending !== null}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md bg-slate-900 text-white font-bold tracking-wide text-sm uppercase hover:bg-slate-800 disabled:opacity-60 disabled:cursor-wait"
          data-testid="ops-manual-download-pdf"
        >
          <Download className="w-4 h-4" />
          {pending === "pdf" ? "Generating…" : "Download PDF"}
        </button>
        <button
          type="button"
          onClick={() => click("docx")}
          disabled={pending !== null}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md bg-white text-slate-900 border-2 border-slate-900 font-bold tracking-wide text-sm uppercase hover:bg-slate-50 disabled:opacity-60 disabled:cursor-wait"
          data-testid="ops-manual-download-docx"
        >
          <FileType2 className="w-4 h-4" />
          {pending === "docx" ? "Generating…" : "Download Word (.docx)"}
        </button>
      </div>

      <div className="mt-4 text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500">
        Classification: CONFIDENTIAL · The Judd Group LLC
      </div>
    </section>
  );
}

export default OpsManualPanel;
