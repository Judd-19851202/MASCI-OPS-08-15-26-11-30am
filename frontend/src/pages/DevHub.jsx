import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
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
  Package,
  ShieldAlert,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PortalShell } from "@/design-system";
import { DataTable } from "@/design-system/DataTable";
import EmptyState from "@/components/EmptyState";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
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
  const res = await fetch(`${API}${path}`, { headers: { "X-Dev-Token": token } });
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

function Section({ title, eyebrow, children, testId }) {
  return (
    <section className="bg-white border border-slate-200 rounded-[1.5rem] p-5 sm:p-6 shadow-[0_16px_40px_rgba(15,23,42,0.05)]" data-testid={testId || `dev-section-${(title || "").toLowerCase().replace(/\s+/g, "-")}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-700 font-bold mb-1">{eyebrow}</div>
      <h2 className="font-display text-lg font-black text-slate-900 mb-4">{title}</h2>
      {children}
    </section>
  );
}

export default function DevHub() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(null);
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
      // silent size hint
    }
  }, []);

  useEffect(() => {
    loadSnaps();
    loadBundleInfo();
  }, [loadSnaps, loadBundleInfo]);

  const onDownload = async (format) => {
    setBusy(format);
    try {
      await downloadWithDevToken(`/api/dev/ops-manual.${format}`, `MASCI_HUB_Operations_Manual.${format}`);
    } finally {
      setBusy(null);
    }
  };

  const onSnapshot = async () => {
    setBusy("snap");
    try {
      const { data } = await api.post("/dev/ops-manual/snapshot", { note: note.trim() });
      toast.success(`Snapshot saved · ${data.pdf_bytes} + ${data.docx_bytes} bytes`);
      setNote("");
      loadSnaps();
    } catch {
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
    } catch {
      toast.error("Delete failed");
    }
  };

  const onSnapDownload = async (id, created, format) => {
    const stamp = (created || "").replace(/[:.]/g, "-").split("T").join("_").split("+")[0];
    await downloadWithDevToken(`/api/dev/ops-manual/snapshots/${id}.${format}`, `MASCI_HUB_Operations_Manual_${stamp}.${format}`);
  };

  const onLogout = () => {
    clearDevToken();
    toast.success("Signed out");
    navigate("/dev/login", { replace: true });
  };

  const onDownloadBundle = async () => {
    setBusy("bundle");
    try {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-").split("Z")[0];
      await downloadWithDevToken("/api/dev/source-bundle.zip", `MASCI_HUB_Source_Bundle_${stamp}.zip`);
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
      return new Date(iso).toLocaleString(undefined, {
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

  const snapshotColumns = useMemo(() => ([
    { key: "created", header: "Created", render: (row) => <span className="font-mono text-xs text-slate-700 whitespace-nowrap">{fmtDate(row.created_at)}</span> },
    { key: "note", header: "Note", wrap: true, render: (row) => row.note || <span className="text-slate-400">—</span> },
    { key: "hash", header: "Source Hash", render: (row) => <span className="font-mono text-xs text-slate-500">{(row.source_hash || "").slice(0, 10)}</span> },
    { key: "size", header: "Size", render: (row) => <span className="font-mono text-xs text-slate-500">{fmtBytes(row.pdf_bytes)} · {fmtBytes(row.docx_bytes)}</span> },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <div className="inline-flex flex-wrap justify-end gap-1.5">
          <button type="button" onClick={() => onSnapDownload(row.id, row.created_at, "pdf")} className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-3 py-1.5 text-[10px] font-mono uppercase tracking-wide text-white hover:bg-slate-800" data-testid={`dev-snapshot-pdf-${row.id}`}>
            <FileText className="w-3 h-3" /> PDF
          </button>
          <button type="button" onClick={() => onSnapDownload(row.id, row.created_at, "docx")} className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-3 py-1.5 text-[10px] font-mono uppercase tracking-wide text-white hover:bg-slate-800" data-testid={`dev-snapshot-docx-${row.id}`}>
            <FileType2 className="w-3 h-3" /> DOCX
          </button>
          <button type="button" onClick={() => onDelete(row.id)} className="inline-flex items-center gap-1 rounded-full border border-red-200 px-3 py-1.5 text-[10px] font-mono uppercase tracking-wide text-red-700 hover:bg-red-50" data-testid={`dev-snapshot-delete-${row.id}`}>
            <Trash2 className="w-3 h-3" /> Delete
          </button>
        </div>
      ),
    },
  ]), []);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Dev Operations"
      pageTitle="Ops Manual & Source Vault"
      subtitle="Confidential developer-facing export and snapshot controls."
      homeHref="/"
      showHome
      showBack={false}
      showSearch={false}
      showNotifications={false}
      showPortalSwitcher={false}
      sideNav={null}
      contentWidth="max-w-none"
      showPageHeader={false}
      primaryActions={(
        <Button onClick={onLogout} variant="outline" className="h-10 border-white/18 bg-white/10 text-white hover:bg-white/18 font-mono text-xs uppercase tracking-wide" data-testid="dev-hub-logout">
          <LogOut className="w-3.5 h-3.5 mr-1.5" /> Sign Out
        </Button>
      )}
    >
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6" data-testid="dev-hub-page">
        <section className="wp17-public-hero" data-testid="dev-hub-hero">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr),18rem] lg:items-start">
            <div>
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/12 text-emerald-700 shadow-[0_16px_32px_rgba(15,23,42,0.10)]">
                <Terminal className="h-7 w-7" />
              </div>
              <div className="wp17-kicker mt-4 text-emerald-700">Dev operations · Controlled exports</div>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">Ops manual, snapshots, and source bundle from one governed surface.</h1>
              <p className="text-slate-600 text-sm sm:text-base mt-3 max-w-3xl">Download the live manual, pin exact revisions for counsel or auditors, and export the current source tree without leaving the MASCI operating shell.</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <OperationalStatusBadge tone="emerald" testId="dev-badge-live">Live exports</OperationalStatusBadge>
                <OperationalStatusBadge tone="amber" testId="dev-badge-confidential">Confidential surface</OperationalStatusBadge>
                <OperationalStatusBadge tone="cyan" testId="dev-badge-source">Source bundle ready</OperationalStatusBadge>
              </div>
            </div>
            <div className="wp17-panel p-4" data-testid="dev-attention-panel">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-700 font-bold mb-2">What needs attention now</div>
              <p className="text-sm text-slate-700 leading-6">Pin a snapshot before handing material to any outside party, and pair it with the source bundle only when you need a byte-exact diligence package.</p>
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr),18rem]">
          <div className="space-y-6">
            <Section title="System Owner & Operations Manual" eyebrow="Live · Renders from current source" testId="dev-section-manual">
              <p className="text-slate-600 text-sm mb-5 max-w-2xl">Full architecture, cost breakdown, deployment procedures, failure points, maintenance checklist, and V2 recommendations. Every download regenerates from the current source so documentation stays current without a redeploy.</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Button type="button" onClick={() => onDownload("pdf")} disabled={busy !== null} className="h-11 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs uppercase tracking-wide" data-testid="dev-ops-manual-pdf">
                  <Download className="w-4 h-4 mr-2" />
                  {busy === "pdf" ? "Generating…" : "Download PDF"}
                </Button>
                <Button type="button" onClick={() => onDownload("docx")} disabled={busy !== null} variant="outline" className="h-11 border-slate-300 bg-white text-slate-900 hover:bg-slate-50 font-mono text-xs uppercase tracking-wide" data-testid="dev-ops-manual-docx">
                  <FileType2 className="w-4 h-4 mr-2" />
                  {busy === "docx" ? "Generating…" : "Download Word (.docx)"}
                </Button>
              </div>
            </Section>

            <Section title="Pin a Snapshot" eyebrow="Archive · Immutable revision" testId="dev-section-snapshot">
              <p className="text-slate-600 text-sm mb-4 max-w-2xl">Save the current manual as an immutable PDF + DOCX pair when you need to lock the exact revision delivered to an auditor, insurer, or counterpart.</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  maxLength={500}
                  placeholder="Optional note — e.g. delivered to counsel on 2026-05-02"
                  className="flex-1 h-11 border-slate-300 text-sm"
                  data-testid="dev-snapshot-note"
                />
                <Button type="button" onClick={onSnapshot} disabled={busy !== null} className="h-11 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs uppercase tracking-wide" data-testid="dev-snapshot-save">
                  {busy === "snap" ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving…</> : <><Camera className="w-4 h-4 mr-2" /> Save Snapshot</>}
                </Button>
              </div>
            </Section>

            <Section title="Full Source Bundle" eyebrow="Due diligence · Live zip of the code tree" testId="dev-section-source-bundle">
              <p className="text-slate-600 text-sm mb-4 max-w-2xl">One-click export of the entire application source tree — backend, frontend, scripts, and memory docs — to pair with a pinned manual snapshot when the recipient needs code + documentation together.</p>
              <div className="mb-4 flex flex-wrap items-center gap-3 font-mono text-[11px] text-slate-500">
                <span className="px-2 py-1 rounded-full bg-slate-100 border border-slate-200">{bundleInfo ? `${bundleInfo.file_count} files` : "…"}</span>
                <span className="px-2 py-1 rounded-full bg-slate-100 border border-slate-200">{bundleInfo ? `${(bundleInfo.bytes / 1024 / 1024).toFixed(1)} MB` : "…"}</span>
                <span className="px-2 py-1 rounded-full bg-slate-100 border border-slate-200">hash {bundleInfo ? (bundleInfo.source_hash || "").slice(0, 10) : "—"}</span>
              </div>
              <Button type="button" onClick={onDownloadBundle} disabled={busy !== null} className="h-11 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs uppercase tracking-wide" data-testid="dev-source-bundle-download">
                {busy === "bundle" ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Building…</> : <><Package className="w-4 h-4 mr-2" /> Download Source Bundle</>}
              </Button>
              <div className="mt-4 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">Excluded: /backups · /storage · node_modules · build · .env · .git · *.pyc · *.bak.json</div>
            </Section>

            <Section title="Snapshot Archive" eyebrow={`History · ${snaps.length} pinned`} testId="dev-section-archive">
              <DataTable
                columns={snapshotColumns}
                rows={snaps}
                rowKey={(row) => row.id}
                loading={loadingSnaps}
                density="compact"
                tableMinWidth="980px"
                empty={<EmptyState title="No snapshots yet." message="Pin one above when you need an immutable revision of the ops manual." icon={History} data-testid="dev-snapshot-empty" />}
                data-testid="dev-snapshot-table"
              />
            </Section>
          </div>

          <div className="space-y-6">
            <Section title="Handling rules" eyebrow="Controlled material" testId="dev-section-handling">
              <div className="space-y-3 text-sm text-slate-700">
                <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 flex gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
                  <p>Do not distribute this surface or its exports to general MASCI staff. Use it only for governed documentation, diligence, or counsel workflows.</p>
                </div>
                <p>Snapshots are the fastest way to prove exactly what manual revision was provided. The source bundle should be paired with the same moment in time whenever legal or diligence workflows require it.</p>
              </div>
            </Section>

            <Section title="Session state" eyebrow="Developer access" testId="dev-section-session">
              <div className="space-y-2 text-sm text-slate-700">
                <div className="flex justify-between gap-3"><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Portal</span><span className="text-slate-900 font-medium">Dev Operations</span></div>
                <div className="flex justify-between gap-3"><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Snapshot count</span><span className="text-slate-900 font-medium">{snaps.length}</span></div>
                <div className="flex justify-between gap-3"><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Bundle status</span><span className="text-slate-900 font-medium">{bundleInfo ? "Ready" : "Probe pending"}</span></div>
              </div>
            </Section>
          </div>
        </div>

        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-center pt-2">Classification: CONFIDENTIAL · ForgedOps™ · Not for MASCI staff distribution</div>
      </main>
    </PortalShell>
  );
}