// HrSafetyRecords — HR read-only view of the safety document library
// and training records. Uses the existing /api/safety/* read endpoints
// that accept X-HR-Token via the multi-role read gate.
//
// HR cannot upload/edit/delete — those buttons are intentionally
// omitted. For mutations, HR users sign into the Safety Portal.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  FolderArchive, Award, Loader2, Download, Filter, AlertTriangle,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { Button } from "@/components/ui/button";
import HrPageShell from "@/components/HrPageShell";
import { getHrToken } from "@/lib/hrAuth";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-HR-Token": getHrToken() } });

function bytes(n) {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0; let v = n;
  while (v > 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(1)} ${u[i]}`;
}

function expStatus(rec) {
  if (!rec.expiration_date) return "none";
  const today = new Date().toISOString().slice(0, 10);
  const thirty = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  if (rec.expiration_date < today) return "expired";
  if (rec.expiration_date <= thirty) return "soon";
  return "ok";
}

const EXP_PILL = {
  expired: "bg-red-100 text-red-900 border-red-300",
  soon: "bg-amber-100 text-amber-900 border-amber-300",
  ok: "bg-emerald-100 text-emerald-900 border-emerald-300",
  none: "bg-slate-100 text-slate-700 border-slate-300",
};

export default function HrSafetyRecords() {
  const { t } = useT();
  const [docs, setDocs] = useState([]);
  const [training, setTraining] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [d, tr] = await Promise.all([
          axios.get(`${API}/safety/documents`, auth()),
          axios.get(`${API}/safety/training-records`, auth()),
        ]);
        setDocs(Array.isArray(d.data) ? d.data : []);
        setTraining(Array.isArray(tr.data) ? tr.data : []);
      } catch (err) {
        toast.error(err?.response?.data?.detail || "Could not load safety records");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filteredDocs = useMemo(() => {
    if (!search.trim()) return docs;
    const s = search.trim().toLowerCase();
    return docs.filter((d) =>
      (d.title || "").toLowerCase().includes(s)
      || (d.category || "").toLowerCase().includes(s)
      || (d.description || "").toLowerCase().includes(s)
      || (d.tags || []).join(",").toLowerCase().includes(s),
    );
  }, [docs, search]);

  const filteredTraining = useMemo(() => {
    if (!search.trim()) return training;
    const s = search.trim().toLowerCase();
    return training.filter((r) =>
      (r.employee_name || "").toLowerCase().includes(s)
      || (r.training_name || "").toLowerCase().includes(s)
      || (r.certification_type || "").toLowerCase().includes(s),
    );
  }, [training, search]);

  const downloadDoc = async (doc) => {
    try {
      const r = await axios.get(`${API}/safety/documents/${doc.id}/download`, {
        ...auth(),
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.filename || `${doc.id}.bin`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Download failed");
    }
  };

  return (
    <HrPageShell title="Safety Records (Read-Only)" kicker="HR · SAFETY DOCUMENTS & TRAINING">
      <p className="text-slate-600 text-sm max-w-2xl leading-relaxed mb-4">
        {t("Cross-portal read access to the Safety Document Library and per-employee training records. Read-only — uploads and edits live in the Safety Portal.")}
      </p>

      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <Input
          placeholder={t("Search title, employee, training, tags…")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700 max-w-md"
          data-testid="hr-safety-search"
        />
      </div>

      {loading ? (
        <LoadingState label={t("Loading…")} testId="hr-safety-loading" />
      ) : (
        <Tabs defaultValue="docs">
          <TabsList>
            <TabsTrigger value="docs" data-testid="hr-safety-tab-docs">
              <FolderArchive className="w-4 h-4 mr-1" /> {t("Documents")} ({docs.length})
            </TabsTrigger>
            <TabsTrigger value="training" data-testid="hr-safety-tab-training">
              <Award className="w-4 h-4 mr-1" /> {t("Training")} ({training.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="docs">
            {filteredDocs.length === 0 ? (
              <EmptyState
                icon={FolderArchive}
                title={t("No documents yet")}
                body={t("Documents uploaded by the Safety team appear here.")}
                testId="hr-safety-docs-empty"
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="hr-safety-doc-list">
                {filteredDocs.map((d) => (
                  <div key={d.id} className="bg-white border-2 border-slate-200 rounded-md p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <span className="inline-block px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-mono uppercase tracking-[0.18em] font-bold mb-1">{d.category}</span>
                        <h3 className="font-display text-lg font-black text-slate-900 truncate">{d.title}</h3>
                        <div className="text-xs text-slate-500 mt-0.5 truncate">{d.filename} · {bytes(d.file_size)}</div>
                        {d.description && <p className="text-sm text-slate-600 mt-1 line-clamp-2">{d.description}</p>}
                      </div>
                      <Button size="sm" variant="outline" onClick={() => downloadDoc(d)} className="h-9 border-purple-300 text-purple-800" data-testid={`hr-safety-doc-download-${d.id}`}>
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="training">
            {filteredTraining.length === 0 ? (
              <EmptyState
                icon={Award}
                title={t("No training records yet")}
                body={t("Training records appear here as Safety enters them.")}
                testId="hr-safety-training-empty"
              />
            ) : (
              <div className="overflow-x-auto" data-testid="hr-safety-training-list">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                    <tr>
                      <th className="text-left px-3 py-2">Employee</th>
                      <th className="text-left px-3 py-2">Training</th>
                      <th className="text-left px-3 py-2">Type</th>
                      <th className="text-left px-3 py-2">Completed</th>
                      <th className="text-left px-3 py-2">Expires</th>
                      <th className="text-center px-3 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTraining.map((r) => {
                      const st = expStatus(r);
                      const label = st === "expired" ? "Expired" : st === "soon" ? "Expiring 30d" : st === "ok" ? "Current" : "No expiry";
                      return (
                        <tr key={r.id} className={`border-t border-slate-100 ${st === "expired" ? "bg-red-50" : ""}`}>
                          <td className="px-3 py-2 font-semibold">{r.employee_name}</td>
                          <td className="px-3 py-2">{r.training_name}</td>
                          <td className="px-3 py-2 text-slate-600 text-xs font-mono">{r.certification_type || "—"}</td>
                          <td className="px-3 py-2">{r.completed_date || "—"}</td>
                          <td className="px-3 py-2">
                            {r.expiration_date || <span className="text-slate-400">—</span>}
                            {st === "expired" && <AlertTriangle className="w-3.5 h-3.5 text-red-600 inline ml-1" />}
                          </td>
                          <td className="px-3 py-2 text-center">
                            <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-[0.15em] font-bold ${EXP_PILL[st]}`}>{label}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}
    </HrPageShell>
  );
}
