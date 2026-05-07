// Single Field Leadership record viewer.
// Renders metadata + every detail key + photos + signatures, with a
// "Download PDF" button. Read-only; archive (admin) goes through the
// records table.

import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FileDown } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import { getLeadershipToken } from "@/lib/leadershipAuth";
import { FIELD_LEADERSHIP_FORMS } from "@/lib/fieldLeadershipSchemas";

export default function FieldLeadershipView() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const { id } = useParams();
  const [rec, setRec] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getLeadershipToken() && !isAdmin()) {
      navigate("/leadership", { replace: true });
      return;
    }
    api.get(`/field-leadership/${id}`)
      .then((r) => setRec(r.data))
      .catch((err) => toast.error(err?.response?.data?.detail || t("Could not load record")))
      .finally(() => setLoading(false));
    // eslint-disable-next-line
  }, [id]);

  const kindLabel = (k) => {
    const f = FIELD_LEADERSHIP_FORMS.find((x) => x.kind === k);
    if (!f) return k;
    return f.title[lang] || f.title.en;
  };

  const downloadPdf = async () => {
    try {
      const r = await api.get(`/field-leadership/${id}/pdf`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    } catch {
      toast.error(t("Could not open PDF"));
    }
  };

  if (loading) return <main className="min-h-screen bg-slate-50 p-8 text-center text-slate-500">{t("Loading…")}</main>;
  if (!rec) return <main className="min-h-screen bg-slate-50 p-8 text-center text-slate-500">{t("Not found")}</main>;

  const details = rec.details_en || rec.details || {};
  const meta = [
    [t("Form Type"), kindLabel(rec.kind)],
    [t("Employee"), rec.employee_name],
    [t("Position"), rec.employee_position],
    [t("Supervisor"), rec.supervisor_name],
    [t("Job"), rec.project_number ? `${rec.project_number} · ${rec.project_name || ""}` : rec.project_name],
    [t("Location"), rec.location || rec.work_area],
    [t("Assigned PM"), rec.assigned_pm],
    [t("Date / Time"), (rec.occurred_at || "").replace("T", " ").slice(0, 16)],
    [t("Submitted via"), rec.submitted_via_role],
    [t("Language"), rec.language === "es" ? "Español → English" : "English"],
  ];

  return (
    <main className="min-h-screen bg-slate-50 pb-16">
      <header className="bg-slate-900 text-white px-5 sm:px-8 py-5 flex items-center justify-between">
        <Link to="/leadership/records" className="text-xs font-mono uppercase tracking-[0.2em] text-slate-300 hover:text-white">
          <ArrowLeft className="inline w-3 h-3 mr-1" /> {t("Records")}
        </Link>
        <Button onClick={downloadPdf} variant="outline" className="h-9 border-2 border-slate-600 bg-slate-800 text-white hover:border-amber-500 text-xs font-bold uppercase tracking-wide" data-testid="leadership-view-pdf">
          <FileDown className="w-3.5 h-3.5 mr-1" />{t("Download PDF")}
        </Button>
      </header>

      <section className="max-w-3xl mx-auto px-5 sm:px-8 pt-6">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">{t("Field Leadership")}</div>
        <h1 className="font-display text-2xl sm:text-3xl font-black mt-1">{kindLabel(rec.kind)}</h1>

        <Card className="mt-5 p-5">
          <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Summary")}</h3>
          <table className="w-full text-sm">
            <tbody>
              {meta.map(([k, v]) => (
                <tr key={k} className="border-b border-slate-100">
                  <th className="text-left py-1.5 pr-3 font-semibold text-slate-700 w-1/3">{k}</th>
                  <td className="py-1.5">{v || <span className="text-slate-400">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {Object.keys(details).length > 0 && (
          <Card className="mt-4 p-5">
            <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Details")}</h3>
            <dl className="space-y-3">
              {Object.entries(details).map(([k, v]) => (
                <div key={k}>
                  <dt className="font-semibold text-sm text-slate-700">{k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</dt>
                  <dd className="text-sm text-slate-800 whitespace-pre-wrap mt-0.5">
                    {v === null || v === undefined || v === "" ? <span className="text-slate-400">—</span>
                      : typeof v === "object" ? (
                        <table className="w-full mt-1">
                          <tbody>
                            {Object.entries(v).map(([kk, vv]) => (
                              <tr key={kk}><th className="text-left text-xs text-slate-500 pr-3 py-0.5 font-mono">{kk}</th><td className="text-xs py-0.5">{String(vv)}</td></tr>
                            ))}
                          </tbody>
                        </table>
                      ) : String(v)}
                  </dd>
                </div>
              ))}
            </dl>
          </Card>
        )}

        {Array.isArray(rec.photos) && rec.photos.length > 0 && (
          <Card className="mt-4 p-5">
            <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Photos")}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {rec.photos.map((p, i) => (
                <img key={i} src={p} alt={`photo ${i}`} className="w-full rounded border border-slate-200 object-contain max-h-48 bg-slate-50" />
              ))}
            </div>
          </Card>
        )}

        {(rec.supervisor_signature || rec.employee_signature || rec.witness_signature) && (
          <Card className="mt-4 p-5">
            <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-b border-slate-200 pb-2 mb-3">{t("Signatures")}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {rec.supervisor_signature && (
                <div className="border-2 border-slate-200 rounded p-3 bg-white">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500">{t("Supervisor")}</div>
                  <img src={rec.supervisor_signature} alt="sig" className="max-h-20 mt-1" />
                  <div className="font-bold mt-1 text-sm">{rec.supervisor_name}</div>
                </div>
              )}
              {rec.employee_refused ? (
                <div className="border-2 border-red-200 rounded p-3 bg-red-50">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-red-700">{t("Employee Refused")}</div>
                  <div className="font-bold mt-1 text-sm">{rec.employee_name}</div>
                </div>
              ) : rec.employee_signature && (
                <div className="border-2 border-slate-200 rounded p-3 bg-white">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500">{t("Employee")}</div>
                  <img src={rec.employee_signature} alt="sig" className="max-h-20 mt-1" />
                  <div className="font-bold mt-1 text-sm">{rec.employee_name}</div>
                </div>
              )}
              {rec.witness_signature && (
                <div className="border-2 border-slate-200 rounded p-3 bg-white">
                  <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500">{t("Witness")}</div>
                  <img src={rec.witness_signature} alt="sig" className="max-h-20 mt-1" />
                  <div className="font-bold mt-1 text-sm">{rec.witness_name}</div>
                </div>
              )}
            </div>
          </Card>
        )}
      </section>
    </main>
  );
}
