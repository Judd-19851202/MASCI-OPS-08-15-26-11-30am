import React, { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { FileText } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { useHubHome } from "@/components/HubBackLink";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { JOB_LIBRARY } from "@/lib/jobLibrary";
import { useBranding } from "@/lib/BrandingProvider";

/**
 * Pure printable card for the Job Hazard Plans QR poster. Renders no
 * toolbar, no <header>, no print <style> block — that's the page wrapper's
 * job. This shape lets the same card render inside the standalone
 * /admin/jha-plans/poster route AND inside the combined /admin/posters/print-all
 * page that stacks all three posters with page-break-after.
 */
export default function JhaPlansPosterCard() {
  const { t } = useT();
  const hubHome = useHubHome();
  const branding = useBranding();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  // Production-locked URL — printed posters keep working forever.
  const jhaUrl = `${(branding.marketing_url || "https://mascidocs.com").replace(/\/+$/, "")}/jha`;

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/job-hazard-plans");
        if (alive) setPlans(r.data || []);
      } catch {
        if (alive) setPlans([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const planSet = new Set(plans.map((p) => p.project_number));
  const uploadedJobs = JOB_LIBRARY.filter((j) => planSet.has(j.project_number));
  const showJobs = uploadedJobs.length > 0 ? uploadedJobs : JOB_LIBRARY.slice(0, 12);

  return (
    <div className="bg-white border-2 border-slate-300 print:border-0 rounded-md p-8 sm:p-10 print:p-6 shadow-xl print:shadow-none">
      {/* Top banner */}
      <div className="flex items-start justify-between gap-6 pb-5 border-b-4 border-amber-600">
        <div className="flex-1">
          <MasciLogo variant="mark" size="2xl" onLight homeLink={hubHome} />
          <div className="mt-3 font-mono text-[11px] uppercase tracking-[0.3em] text-amber-700 font-bold">
            {t("Job Hazard Plans · One per active job")}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
            {t("Office")}
          </div>
          <div className="font-display font-black text-slate-900 text-xl leading-none mt-1">
            386-322-4500
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
            {branding.safety_email || branding.support_email || ""}
          </div>
        </div>
      </div>

      {/* Hero */}
      <div className="grid grid-cols-1 sm:grid-cols-[auto,1fr] gap-6 mt-7 items-center">
        <div className="bg-slate-900 p-4 rounded-md inline-flex items-center justify-center">
          <QRCodeSVG
            value={jhaUrl}
            size={200}
            bgColor="#0F172A"
            fgColor="#FFFFFF"
            level="M"
            marginSize={1}
            data-testid="jha-poster-qr"
          />
        </div>
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-amber-700 font-bold inline-flex items-center gap-2">
            <FileText className="w-4 h-4" /> {t("Read the plan before crew breaks ground.")}
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 leading-[0.95] mt-2">
            {t("Every active MASCI job. Its own Hazard Plan PDF. One scan.")}
          </h1>
          <p className="text-slate-700 text-base mt-3 leading-relaxed">
            {t(
              "Open your phone camera. Point at the QR. Pick your job. Read the Hazard Plan before the first shovel moves. No service? Save the PDF to your phone and read it offline."
            )}
          </p>
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-500 mt-3 break-all">
            {jhaUrl.replace(/^https?:\/\//, "")}
          </div>
        </div>
      </div>

      {/* What to look for in the plan */}
      <div className="mt-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-amber-700 font-black mb-3">
          {t("What's in a Hazard Plan")}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
          {[
            {
              title: t("Site-specific hazards"),
              body: t("Traffic, utilities, deep cuts, water, overhead lines."),
            },
            {
              title: t("PPE & permits"),
              body: t("What gets worn, what gets pulled before the crew steps in."),
            },
            {
              title: t("Emergency response"),
              body: t("Nearest hospital, muster point, who calls 911 first."),
            },
          ].map((item) => (
            <div
              key={item.title}
              className="border-2 border-slate-300 bg-amber-50 rounded-md p-4"
            >
              <div className="font-display text-sm font-black text-slate-900 leading-tight">
                {item.title}
              </div>
              <div className="text-xs text-slate-700 mt-1.5 leading-relaxed">{item.body}</div>
            </div>
          ))}
        </div>
        <p className="text-slate-700 text-sm mt-3 leading-relaxed">
          <span className="font-black text-amber-700">·</span>{" "}
          {t(
            "If you can't find your job's plan in the list — STOP and call your PM. Don't break ground without one."
          )}
        </p>
      </div>

      {/* Job list snapshot */}
      <div className="mt-8">
        <div className="flex items-baseline justify-between mb-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-amber-700 font-black">
            {uploadedJobs.length > 0
              ? t("Plans currently uploaded")
              : t("Active MASCI jobs")}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            {loading
              ? t("Loading…")
              : `${uploadedJobs.length} / ${JOB_LIBRARY.length} ${t("jobs covered")}`}
          </div>
        </div>
        <div className="border border-slate-200 rounded-md overflow-hidden">
          <table className="w-full text-sm" data-testid="jha-poster-job-table">
            <thead>
              <tr className="bg-slate-900 text-white font-mono text-[10px] uppercase tracking-[0.2em]">
                <th className="text-left px-3 py-2">{t("Project #")}</th>
                <th className="text-left px-3 py-2">{t("Project Name")}</th>
                <th className="text-left px-3 py-2">{t("Location")}</th>
              </tr>
            </thead>
            <tbody>
              {showJobs.map((j, idx) => (
                <tr
                  key={j.project_number}
                  className={idx % 2 === 0 ? "bg-white" : "bg-slate-50 print:bg-white"}
                >
                  <td className="px-3 py-2 font-mono font-bold text-amber-700">
                    {j.project_number}
                  </td>
                  <td className="px-3 py-2 font-display font-bold text-slate-900">
                    {j.project_name}
                  </td>
                  <td className="px-3 py-2 text-slate-700">{j.location || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500 italic mt-2">
          {uploadedJobs.length > 0
            ? t("List shows only jobs that have a plan uploaded. Scan the QR for the live, complete list.")
            : t("Sample of MASCI active jobs. Scan the QR for the live, complete list with download links.")}
        </p>
      </div>

      {/* Footer */}
      <div className="mt-8 pt-5 border-t-2 border-black flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-700">
          {t("Post inside every job trailer.")}
        </div>
      </div>
    </div>
  );
}
