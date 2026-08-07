// SafetyReports — Reports & Exports landing page. Each tile triggers
// the equivalent /api/exports/{...} endpoint that already exists, or
// a print-friendly view. Lightweight — no analytics rendered here,
// just operational launchpad to the data Safety needs to hand to
// insurance, OSHA, or executives.
import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3, FileText, Download, Loader2, ClipboardCheck,
  ShieldAlert, Award, Flame, Users, FolderArchive, Building2, Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import SafetyShell from "@/components/SafetyShell";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: buildScopedPortalAuthHeaders(["safety", "admin", "pm"]) });

const REPORTS = [
  {
    key: "incidents",
    label: "Incident & Near-Miss Summary",
    desc: "All filed incidents and near misses in the period. CSV or PDF.",
    icon: ClipboardCheck,
    accent: "bg-amber-600",
    endpoint: "/safety/exports/incidents",
    link: "/safety-portal/incidents",
    formats: ["csv", "pdf"],
  },
  {
    key: "corrective_actions",
    label: "Corrective Actions Report",
    desc: "Every CA with status, owner, due date, and resolution notes.",
    icon: ShieldAlert,
    accent: "bg-red-700",
    endpoint: "/safety/exports/corrective-actions",
    link: "/safety-portal/corrective-actions",
    formats: ["csv", "pdf"],
  },
  {
    key: "audits",
    label: "Audit & Inspection Report",
    desc: "Site audits and jobsite inspections with deficiencies and result.",
    icon: ShieldAlert,
    accent: "bg-emerald-700",
    endpoint: "/safety/exports/inspections",
    link: "/safety-portal/audits",
    formats: ["csv", "pdf"],
  },
  {
    key: "training",
    label: "Training & Certification Roll-Up",
    desc: "Every active training record with expiration status.",
    icon: Award,
    accent: "bg-indigo-700",
    endpoint: "/safety/exports/training-records",
    link: "/safety-portal/training",
    formats: ["csv", "pdf"],
  },
  {
    key: "training_expired",
    label: "Expired / Expiring Training Report",
    desc: "Only expired and expiring-within-30-days certifications.",
    icon: Award,
    accent: "bg-red-700",
    endpoint: "/safety/exports/training-expired",
    link: "/safety-portal/training",
    formats: ["csv", "pdf"],
  },
  {
    key: "fire_extinguishers",
    label: "Fire Extinguisher Inspection Report",
    desc: "Unit-level inspection log + overdue list.",
    icon: Flame,
    accent: "bg-red-800",
    endpoint: "/safety/exports/fire-extinguishers",
    link: "/safety-portal/fire-extinguishers",
    formats: ["csv", "pdf"],
  },
  {
    key: "employee_safety",
    label: "Employee Safety Profile Export",
    desc: "Per-employee training, incidents, PPE, and meeting attendance.",
    icon: Users,
    accent: "bg-slate-700",
    endpoint: "/safety/exports/employee-profiles",
    link: "/safety-portal/employees",
    formats: ["csv"],
  },
  {
    key: "documents",
    label: "Safety Document Library Index",
    desc: "Catalog of every uploaded safety document with metadata.",
    icon: FolderArchive,
    accent: "bg-cyan-700",
    endpoint: "/safety/exports/documents",
    link: "/safety-portal/documents",
    formats: ["csv"],
  },
  {
    key: "project_safety",
    label: "Project Safety Roll-Up",
    desc: "Safety record by job — incidents, audits, training compliance.",
    icon: Building2,
    accent: "bg-amber-700",
    endpoint: "/safety/exports/project-safety",
    link: "/safety-portal",
    formats: ["csv", "pdf"],
  },
  {
    key: "executive",
    label: "Executive Safety Summary",
    desc: "Single-page roll-up suitable for the leadership team / insurer.",
    icon: BarChart3,
    accent: "bg-purple-700",
    endpoint: "/safety/exports/executive",
    link: "/safety-portal",
    formats: ["pdf"],
  },
];

export default function SafetyReports() {
  const { t } = useT();
  const [busy, setBusy] = useState({});

  const run = async (r, fmt) => {
    setBusy((b) => ({ ...b, [`${r.key}:${fmt}`]: true }));
    try {
      const res = await axios.get(`${API}${r.endpoint}?format=${fmt}`, {
        ...auth(),
        responseType: "blob",
      });
      const blob = new Blob([res.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${r.key}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(t("Export ready"));
    } catch (e) {
      const code = e?.response?.status;
      if (code === 404) {
        toast.message(t("Export pending"), {
          description: t("This export is still being prepared. The same live information is already available in the linked page if you need it now."),
        });
      } else {
        toast.error(operationalError(e,
          t("Export temporarily unavailable. Try again in a moment."),
          t("Your Safety session expired. Please sign in again.")));
      }
    } finally {
      setBusy((b) => ({ ...b, [`${r.key}:${fmt}`]: false }));
    }
  };

  return (
    <SafetyShell title={t("Reports & Exports")} kicker={t("Compliance")}>
      <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-4" data-testid="safety-reports-page">
        <header className="bg-white border border-slate-200 rounded-md p-5 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-purple-700 text-white shrink-0">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-purple-700 font-bold">
              Safety Portal
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              {t("Reports & Exports")}
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              {t("Operational reports the team hands to insurance, OSHA, the leadership team, and project owners. Each export pulls from the same live data the portal displays — never a stale snapshot.")}
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {REPORTS.map((r) => (
            <ReportTile
              key={r.key}
              report={r}
              busy={busy}
              onRun={run}
              t={t}
            />
          ))}
        </div>

        <div className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-md p-4 text-xs text-slate-600">
          <strong className="block mb-1 font-mono uppercase tracking-[0.15em] text-slate-700">{t("Need a custom report?")}</strong>
          {t("All exports use the same live information shown in the linked pages. For anything not listed here, open the related page and use its built-in print or PDF option, or ask Admin to add a new export to this page.")}
        </div>
      </div>
    </SafetyShell>
  );
}

function ReportTile({ report: r, busy, onRun, t }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4 flex flex-col" data-testid={`report-tile-${r.key}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`inline-flex items-center justify-center w-9 h-9 rounded-md ${r.accent} text-white`}>
          <r.icon className="w-4 h-4" />
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">
          {r.formats.map((f) => f.toUpperCase()).join(" · ")}
        </div>
      </div>
      <div className="font-display text-base font-black leading-tight">{r.label}</div>
      <p className="text-xs text-slate-600 mt-1 flex-1">{r.desc}</p>
      <div className="flex flex-wrap gap-1 mt-3">
        {r.formats.map((fmt) => (
          <Button
            key={fmt}
            size="sm"
            variant="outline"
            disabled={!!busy[`${r.key}:${fmt}`]}
            onClick={() => onRun(r, fmt)}
            className="text-xs"
            data-testid={`report-${r.key}-${fmt}`}
          >
            {busy[`${r.key}:${fmt}`]
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <Download className="w-3.5 h-3.5 mr-1" />} {fmt.toUpperCase()}
          </Button>
        ))}
        <Link to={r.link}>
          <Button size="sm" variant="ghost" className="text-xs" data-testid={`report-${r.key}-open`}>
            <FileText className="w-3.5 h-3.5 mr-1" /> {t("Open module")}
          </Button>
        </Link>
      </div>
    </div>
  );
}
