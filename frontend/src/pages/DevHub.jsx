import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Terminal,
  Download,
  FileText,
  FileType2,
  LogOut,
  Camera,
  Loader2,
  Trash2,
  History,
  ArrowLeft,
  Package,
} from "lucide-react";
import { api } from "@/lib/api";
import { getDevToken, clearDevToken } from "@/lib/devAuth";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

async function downloadWithDevToken(path, fallbackName) {
  const token = getDevToken();
  if (!token) {
    toast.error("Developer session expired — please sign in again.");
    return false;
  }
  const res = await fetch(`${API}${path}`, {
    headers: { "X-Dev-Token": token },
  });
  if (!res.ok) {
    toast.error(`Download failed (${res.status})`);
    return false;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fallbackName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return true;
}

function Section({ title, eyebrow, children }) {
  return (
    <section className="bg-slate-900 border border-slate-800 rounded-md p-5 sm:p-6" data-testid={`dev-section-${(title||"").toLowerCase().replace(/\s+/g,"-")}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-400 font-bold mb-1">
        {eyebrow}
      </div>
      <h2 className="font-mono text-lg font-bold text-white tracking-tight mb-5">
        {title}
      </h2>
      {children}
    </section>
  );
}

export default function DevHub() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(null); // "pdf" | "docx" | "snap" | "bundle" | null
  const [snaps, setSnaps] = useState([]);
  const [loadingSnaps, setLoadingSnaps] = useState(false);
  const [note, setNote] = useState("");
  const [bundleInfo, setBundleInfo] = useState(null);

  const loadSnaps = useCallback(async () => {
    setLoadingSnaps(true);
    try {
      const { data } = await api.get("/dev/ops-manual/snapshots");
      setSnaps(data.snapshots || []);
    } catch (err) {
      if (err?.response?.status === 401) {
        navigate("/dev/login", { replace: true });
        return;
      }
      toast.error("Failed to load snapshots");
    } finally {
      setLoadingSnaps(false);
    }
  }, [navigate]);

  const loadBundleInfo = useCallback(async () => {
    try {
      const { data } = await api.get("/dev/source-bundle.info");
      setBundleInfo(data);
    } catch {
      // silent — info probe is just a size hint
    }
  }, []);

  useEffect(() => {
    loadSnaps();
    loadBundleInfo();
  }, [loadSnaps, loadBundleInfo]);

  const onDownload = async (format) => {
    setBusy(format);
    try {
      await downloadWithDevToken(
        `/api/dev/ops-manual.${format}`,
        `MASCI_HUB_Operations_Manual.${format}`
      );
    } finally {
      setBusy(null);
    }
  };

  const onSnapshot = async () => {
    setBusy("snap");
    try {
      const { data } = await api.post("/dev/ops-manual/snapshot", {
        note: note.trim(),
      });
      toast.success(`Snapshot saved · ${data.pdf_bytes} + ${data.docx_bytes} bytes`);
      setNote("");
      loadSnaps();
    } catch (err) {
      toast.error("Failed to create snapshot");
    } finally {
      setBusy(null);
    }
  };

  const onDelete = async (id) => {
    if (!window.confirm("Delete this snapshot? This cannot be undone.")) return;
    try {
      await api.delete(`/dev/ops-manual/snapshots/${id}`);
      toast.success("Snapshot deleted");
      loadSnaps();
    } catch (err) {
      toast.error("Delete failed");
    }
  };

  const onSnapDownload = async (id, created, format) => {
    const stamp = (created || "").replace(/[:.]/g, "-").split("T").join("_").split("+")[0];
    await downloadWithDevToken(
      `/api/dev/ops-manual/snapshots/${id}.${format}`,
      `MASCI_HUB_Operations_Manual_${stamp}.${format}`
    );
  };

  const onLogout = () => {
    clearDevToken();
    toast.success("Signed out");
    navigate("/dev/login", { replace: true });
  };

  const onDownloadBundle = async () => {
    setBusy("bundle");
    try {
      const stamp = new Date()
        .toISOString()
        .replace(/[:.]/g, "-")
        .split("Z")[0];
      await downloadWithDevToken(
        "/api/dev/source-bundle.zip",
        `MASCI_HUB_Source_Bundle_${stamp}.zip`
      );
      // refresh info after download in case source changed
      loadBundleInfo();
    } finally {
      setBusy(null);
    }
  };

  const fmtBytes = (n) => {
    if (!n && n !== 0) return "—";
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / 1024 / 1024).toFixed(2)} MB`;
  };

  const fmtDate = (iso) => {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white" data-testid="dev-hub-page">
      <header className="border-b border-slate-800">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-slate-800 text-emerald-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500">
                ForgedOps™ · Vendor Portal
              </div>
              <h1 className="font-mono text-base font-bold text-white leading-none mt-0.5">
                dev.portal / ops-manual
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-700 text-slate-300 hover:bg-slate-800 font-mono text-xs uppercase tracking-wide"
              data-testid="dev-hub-home"
            >
              <ArrowLeft className="w-3 h-3" /> Home
            </Link>
            <button
              type="button"
              onClick={onLogout}
              className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-700 text-slate-300 hover:bg-slate-800 font-mono text-xs uppercase tracking-wide"
              data-testid="dev-hub-logout"
            >
              <LogOut className="w-3 h-3" /> Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 space-y-6">
        {/* Section: Live manual download */}
        <Section title="System Owner & Operations Manual" eyebrow="Live · Renders from current source">
          <p className="text-slate-400 text-sm mb-5 max-w-2xl">
            Full architecture, cost breakdown, deployment procedures, failure
            points, maintenance checklist, and V2 recommendations. Regenerated
            on every request from <span className="font-mono text-slate-300">ops_manual.py</span> so
            edits ship without a redeploy.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              type="button"
              onClick={() => onDownload("pdf")}
              disabled={busy !== null}
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs uppercase tracking-wide disabled:opacity-50"
              data-testid="dev-ops-manual-pdf"
            >
              <Download className="w-4 h-4" />
              {busy === "pdf" ? "Generating…" : "Download PDF"}
            </button>
            <button
              type="button"
              onClick={() => onDownload("docx")}
              disabled={busy !== null}
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 font-mono text-xs uppercase tracking-wide disabled:opacity-50"
              data-testid="dev-ops-manual-docx"
            >
              <FileType2 className="w-4 h-4" />
              {busy === "docx" ? "Generating…" : "Download Word (.docx)"}
            </button>
          </div>
        </Section>

        {/* Section: Pin a snapshot */}
        <Section title="Pin a Snapshot" eyebrow="Archive · Mongo collection · ops_manual_snapshots">
          <p className="text-slate-400 text-sm mb-4 max-w-2xl">
            Save the current manual (PDF + DOCX) as an immutable record. Useful
            for pinning the exact revision handed to an auditor, insurance, or
            a contract counter-party.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={500}
              placeholder="Optional note — e.g. &quot;v1.0 delivered to counsel 2026-05-02&quot;"
              className="flex-1 h-11 px-3 rounded-md bg-slate-950 border border-slate-700 text-white placeholder:text-slate-600 font-mono text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
              data-testid="dev-snapshot-note"
            />
            <button
              type="button"
              onClick={onSnapshot}
              disabled={busy !== null}
              className="inline-flex items-center justify-center gap-2 h-11 px-5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs uppercase tracking-wide disabled:opacity-50"
              data-testid="dev-snapshot-save"
            >
              {busy === "snap" ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
              ) : (
                <><Camera className="w-4 h-4" /> Save Snapshot</>
              )}
            </button>
          </div>
        </Section>

        {/* Section: Source bundle download */}
        <Section title="Full Source Bundle" eyebrow="Due-Diligence · Live zip of the code tree">
          <p className="text-slate-400 text-sm mb-4 max-w-2xl">
            One-click download of the entire application source tree —
            backend, frontend, scripts, memory docs. Pair with a pinned Ops
            Manual snapshot to hand a byte-exact code + documentation
            package to counsel, an auditor, or an acquirer.
          </p>
          <div className="mb-4 flex flex-wrap items-center gap-3 font-mono text-[11px] text-slate-500">
            <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800">
              {bundleInfo ? `${bundleInfo.file_count} files` : "…"}
            </span>
            <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800">
              {bundleInfo ? `${(bundleInfo.bytes / 1024 / 1024).toFixed(1)} MB` : "…"}
            </span>
            <span className="px-2 py-1 rounded bg-slate-950 border border-slate-800">
              hash {bundleInfo ? (bundleInfo.source_hash || "").slice(0, 10) : "—"}
            </span>
          </div>
          <button
            type="button"
            onClick={onDownloadBundle}
            disabled={busy !== null}
            className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs uppercase tracking-wide disabled:opacity-50"
            data-testid="dev-source-bundle-download"
          >
            {busy === "bundle" ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Building…</>
            ) : (
              <><Package className="w-4 h-4" /> Download Source Bundle</>
            )}
          </button>
          <div className="mt-4 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-600">
            Excluded: /backups · /storage · node_modules · build · .env · .git · *.pyc · *.bak.json
          </div>
        </Section>

        {/* Section: Snapshot archive */}
        <Section title="Snapshot Archive" eyebrow={`History · ${snaps.length} pinned`}>
          {loadingSnaps ? (
            <div className="flex items-center gap-2 text-slate-500 text-sm font-mono">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading…
            </div>
          ) : snaps.length === 0 ? (
            <div className="flex items-start gap-3 bg-slate-950 border border-slate-800 rounded-md p-4 text-slate-500 text-sm">
              <History className="w-4 h-4 mt-0.5 text-slate-600" />
              <span>No snapshots yet. Pin one above when you want to lock in a specific revision of the manual.</span>
            </div>
          ) : (
            <div className="border border-slate-800 rounded-md overflow-hidden">
              <table className="w-full text-sm" data-testid="dev-snapshot-table">
                <thead className="bg-slate-950/50 border-b border-slate-800">
                  <tr className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    <th className="text-left px-4 py-2.5">Created</th>
                    <th className="text-left px-4 py-2.5">Note</th>
                    <th className="text-left px-4 py-2.5">Source Hash</th>
                    <th className="text-left px-4 py-2.5">Size</th>
                    <th className="text-right px-4 py-2.5">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {snaps.map((s) => (
                    <tr key={s.id} className="border-t border-slate-800 hover:bg-slate-900/50" data-testid={`dev-snapshot-row-${s.id}`}>
                      <td className="px-4 py-3 font-mono text-xs text-slate-300 whitespace-nowrap">
                        {fmtDate(s.created_at)}
                      </td>
                      <td className="px-4 py-3 text-slate-200 max-w-xs truncate">
                        {s.note || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">
                        {(s.source_hash || "").slice(0, 10)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">
                        {fmtBytes(s.pdf_bytes)} · {fmtBytes(s.docx_bytes)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => onSnapDownload(s.id, s.created_at, "pdf")}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-mono text-[10px] uppercase tracking-wide"
                            title="Download PDF"
                            data-testid={`dev-snapshot-pdf-${s.id}`}
                          >
                            <FileText className="w-3 h-3" /> PDF
                          </button>
                          <button
                            type="button"
                            onClick={() => onSnapDownload(s.id, s.created_at, "docx")}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-mono text-[10px] uppercase tracking-wide"
                            title="Download DOCX"
                            data-testid={`dev-snapshot-docx-${s.id}`}
                          >
                            <FileType2 className="w-3 h-3" /> DOCX
                          </button>
                          <button
                            type="button"
                            onClick={() => onDelete(s.id)}
                            className="inline-flex items-center gap-1 px-2 py-1.5 rounded border border-red-900 text-red-400 hover:bg-red-950/50 font-mono text-[10px]"
                            title="Delete snapshot"
                            data-testid={`dev-snapshot-delete-${s.id}`}
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 text-center pt-4">
          Classification: CONFIDENTIAL · ForgedOps™ · Not for MASCI staff distribution
        </div>
      </main>
    </div>
  );
}
