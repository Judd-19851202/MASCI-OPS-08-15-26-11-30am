import React, { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useLocation, useParams } from "react-router-dom";
import {
  FileText,
  Loader2,
  Download,
  CheckCircle2,
  PackageCheck,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { PortalShell } from "@/design-system";
import { DataTable } from "@/design-system/DataTable";
import EmptyState from "@/components/EmptyState";
import { DetailPageHero } from "@/components/detail/DetailPageHero";
import { RefKicker } from "@/components/RefKicker";
import { useT } from "@/lib/i18n";
import { api, API } from "@/lib/api";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { isSafetyForms, getSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isSafety } from "@/lib/safetyAuth";
import { fmtMoney } from "@/lib/safetyFormsSchema";
import { formatDateLong } from "@/lib/utils";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { toast } from "sonner";
import { formatPlatformTime } from "@/lib/platformTime";

const STATUS_TONES = {
  returned: { bg: "bg-emerald-100", fg: "text-emerald-800", border: "border-emerald-300", label: "Returned OK" },
  damaged: { bg: "bg-amber-100", fg: "text-amber-800", border: "border-amber-300", label: "Damaged" },
  lost: { bg: "bg-red-100", fg: "text-red-800", border: "border-red-300", label: "Lost" },
};

function CenterState({ message, loading = false, testId = "view-safety-form-state" }) {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <div className="wp17-panel flex min-h-[16rem] items-center justify-center text-center" data-testid={testId}>
        <div>
          {loading ? <Loader2 className="w-6 h-6 animate-spin mx-auto mb-3 text-red-700" /> : null}
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Safety Records</div>
          <div className="mt-2 text-sm text-slate-600">{message}</div>
        </div>
      </div>
    </div>
  );
}

function wrapWithShell({ isAdminRoute, pageTitle, recordLabel, children, subjectLabel }) {
  if (isAdminRoute) {
    return (
      <AdminRouteShell
        pageTitle={pageTitle}
        subtitle="Admin review for safety equipment issuance and training acknowledgements."
        portalRole="Admin · Safety Records"
        crumbs={[{ label: "Field Operations" }, { label: "Safety Records" }, { label: subjectLabel || "Record" }]}
        showShellHeader={false}
        showBreadcrumbs={false}
        contentClassName="px-0 py-0"
        testId="admin-view-safety-form-shell"
      >
        {children}
      </AdminRouteShell>
    );
  }

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Safety Records"
      pageTitle={recordLabel}
      subtitle="Safety equipment accountability and training records."
      homeHref="/"
      showHome
      showBack={false}
      showSearch={false}
      showNotifications={false}
      showPortalSwitcher={false}
      sideNav={null}
      contentWidth="max-w-none"
      showPageHeader={false}
    >
      {children}
    </PortalShell>
  );
}

function SectionCard({ title, children, testId }) {
  return (
    <section className="bg-white border border-slate-200 rounded-[1.5rem] p-5 sm:p-6 shadow-[0_16px_40px_rgba(15,23,42,0.05)]" data-testid={testId}>
      <div className="font-display text-lg font-black text-slate-900 mb-4 border-b border-slate-200 pb-2">{title}</div>
      {children}
    </section>
  );
}

function KvBlock({ title, rows, testId }) {
  return (
    <SectionCard title={title} testId={testId}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
        {rows.map(([k, v], i) => (
          <div key={i} className="flex gap-3 items-start border-b border-slate-100 py-2">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold w-32 shrink-0 pt-0.5">{k}</span>
            <span className="text-slate-900 break-words">{v ?? "—"}</span>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function SigBlock({ label, sig }) {
  return (
    <div>
      {sig ? (
        <img src={sig} alt="" className="max-h-24 max-w-full border-b-2 border-slate-900 pb-1" />
      ) : (
        <div className="border-b-2 border-slate-900 h-20" />
      )}
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-600 mt-2">{label}</div>
    </div>
  );
}

export default function ViewSafetyForm({ kind = "issuance" }) {
  const { id } = useParams();
  const { pathname } = useLocation();
  const { t } = useT();
  const isAdminRoute = pathname.startsWith("/admin/");
  const [doc, setDoc] = useState(null);
  const [err, setErr] = useState("");
  const [downloading, setDownloading] = useState(false);

  const authed = isSafety() || isSafetyForms() || isAdmin();
  const isTraining = kind === "training";
  const apiBase = isTraining ? "/safety-forms/equipment-trainings" : "/safety-forms/equipment-issuances";
  const pageTitle = isTraining ? t("Safety Training Record") : t("Safety Issuance Record");
  const backHref = isAdminRoute ? "/admin/safety" : "/safety/forms";

  useEffect(() => {
    if (!authed) return;
    api
      .get(`${apiBase}/${id}`)
      .then((r) => setDoc(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Not found"));
  }, [authed, apiBase, id]);

  const downloadPdf = async (subPath = "/pdf", suffix = "") => {
    setDownloading(true);
    try {
      const sfTok = getSafetyFormsToken();
      const headers = {
        ...buildScopedPortalAuthHeaders(["admin", "safety"]),
        ...(sfTok ? { "X-Safety-Forms-Token": sfTok } : {}),
      };
      const res = await fetch(`${API}${apiBase}/${id}${subPath}`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const cd = res.headers.get("content-disposition") || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      a.href = url;
      a.download = m ? m[1] : `MASCI_safety_form${suffix}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(e?.message || t("Could not download PDF"));
    } finally {
      setDownloading(false);
    }
  };

  if (!authed) {
    return <Navigate to="/safety-portal/login?from=safety-forms" replace />;
  }

  if (err) {
    return wrapWithShell({
      isAdminRoute,
      pageTitle,
      recordLabel: pageTitle,
      subjectLabel: "Record",
      children: <CenterState message={err} testId="view-safety-form-error" />,
    });
  }

  if (!doc) {
    return wrapWithShell({
      isAdminRoute,
      pageTitle,
      recordLabel: pageTitle,
      subjectLabel: "Record",
      children: <CenterState message={t("Loading record…")} loading testId="view-safety-form-loading" />,
    });
  }

  const items = doc.items || [];
  const total = items.reduce((sum, it) => sum + (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_value) || 0), 0);
  const recordId = doc.issuance_number || doc.training_number || doc.id;

  const issuanceColumns = [
    { key: "idx", header: "#", width: 48, render: (row) => row.idx },
    { key: "item", header: t("Item"), wrap: true, render: (row) => row.item },
    { key: "description", header: t("Description"), wrap: true, render: (row) => row.description || "—" },
    { key: "asset", header: t("Asset / Serial"), render: (row) => row.asset_id || "—" },
    { key: "qty", header: t("Qty"), align: "right", render: (row) => row.quantity || "—" },
    { key: "unit", header: t("Unit $"), align: "right", render: (row) => fmtMoney(row.unit_value) },
    { key: "line", header: t("Line $"), align: "right", render: (row) => fmtMoney((parseFloat(row.quantity) || 0) * (parseFloat(row.unit_value) || 0)) },
  ];

  const trainingColumns = [
    { key: "idx", header: "#", width: 48, render: (row) => row.idx },
    { key: "item", header: t("Item"), wrap: true, render: (row) => row.item },
    { key: "description", header: t("Description"), wrap: true, render: (row) => row.description || "—" },
    { key: "type", header: t("Type"), render: (row) => row.training_type || "—" },
    { key: "model", header: t("Mfr / Model"), wrap: true, render: (row) => row.manufacturer_model || "—" },
    { key: "notes", header: t("Notes"), wrap: true, render: (row) => row.notes || "—" },
  ];

  const tableRows = items.map((it, i) => {
    const itemKey = isTraining ? "equipment_type" : "item_type";
    const otherKey = isTraining ? "equipment_type_other" : "item_type_other";
    const itemLabel = it[itemKey] === "Other" && it[otherKey] ? `Other — ${it[otherKey]}` : it[itemKey];
    return { ...it, idx: i + 1, item: itemLabel };
  });

  const returnRows = ((doc.return?.items) || []).map((it, i) => {
    const sq = parseFloat(it.source_quantity) || 0;
    const rq = parseFloat(it.returned_quantity) || 0;
    const uv = parseFloat(it.source_unit_value) || 0;
    const cb = it.status === "lost"
      ? sq * uv
      : it.status === "damaged"
        ? sq * uv
        : it.status === "returned" && rq < sq
          ? (sq - rq) * uv
          : 0;
    const itemLabel = it.source_item_type === "Other" && it.source_item_type_other
      ? `Other — ${it.source_item_type_other}`
      : it.source_item_type;
    return { ...it, idx: i + 1, itemLabel, sq, rq, cb };
  });

  const returnColumns = [
    { key: "itemLabel", header: t("Item"), wrap: true, render: (row) => <div><div className="font-medium">{row.itemLabel}</div><div className="text-xs text-slate-500">{row.source_description || "—"}</div></div> },
    { key: "sq", header: t("Issued"), align: "right", render: (row) => row.sq },
    { key: "rq", header: t("Returned"), align: "right", render: (row) => row.rq },
    {
      key: "status",
      header: t("Status"),
      wrap: true,
      render: (row) => {
        const tone = STATUS_TONES[row.status] || STATUS_TONES.returned;
        return (
          <div>
            <span className={`inline-block px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wide border ${tone.bg} ${tone.fg} ${tone.border}`}>
              {t(tone.label)}
            </span>
            {row.note ? <div className="text-xs text-slate-600 mt-1">{row.note}</div> : null}
          </div>
        );
      },
    },
    { key: "cb", header: t("Chargeback"), align: "right", render: (row) => <span className={row.cb > 0 ? "font-bold text-red-700" : "text-slate-600"}>{fmtMoney(row.cb)}</span> },
  ];

  const content = (
    <div className="min-h-screen bg-slate-50 print:bg-white">
      <div className="caution-stripe print:hidden" />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
        <DetailPageHero
          backHref={backHref}
          backLabel={isAdminRoute ? t("Admin · Safety") : t("Safety Forms")}
          kicker={t("Safety Records · Equipment Accountability")}
          title={isTraining ? t("Equipment Use & Care Training") : t("Safety Equipment Issuance & Accountability")}
          description={[doc.employee_name, doc.project_name, isTraining ? formatDateLong(doc.training_date) : formatDateLong(doc.issued_date)].filter(Boolean).join(" · ")}
          actions={(
            <>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-800" data-testid="view-safety-form-submitted">
                <CheckCircle2 className="w-3.5 h-3.5" /> {t("Submitted")}
              </span>
              <RefKicker recordId={recordId} testId="view-safety-form-ref" />
            </>
          )}
          toolbar={(
            <Button
              onClick={() => downloadPdf("/pdf")}
              disabled={downloading}
              className="bg-red-700 hover:bg-red-800 h-11 font-bold uppercase tracking-wide text-xs"
              data-testid="view-download-pdf"
            >
              {downloading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Download className="w-4 h-4 mr-1" />}
              {t("Download PDF")}
            </Button>
          )}
          testId="view-safety-form-hero"
        />

        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr),18rem] gap-6">
          <div className="space-y-6">
            <KvBlock
              title={t("Employee")}
              testId="view-safety-form-employee"
              rows={[
                [t("Name"), doc.employee_name],
                [t("Employee ID"), doc.employee_id || "—"],
                [t("Position"), doc.position || "—"],
                [t("Project"), [doc.project_name, doc.project_number].filter(Boolean).join(" · ") || "—"],
              ]}
            />

            <KvBlock
              title={isTraining ? t("Training") : t("Issuance")}
              testId="view-safety-form-context"
              rows={isTraining ? [
                [t("Date"), formatDateLong(doc.training_date)],
                [t("Instructor"), doc.instructor_name],
                [t("Location"), doc.training_location || "—"],
              ] : [
                [t("Date Issued"), formatDateLong(doc.issued_date)],
                [t("Issued By"), doc.issued_by],
                [t("Location"), doc.location || "—"],
                [t("Condition"), <span key="condition"><b>{doc.condition}</b>{doc.condition?.toLowerCase() === "damaged" && doc.condition_note ? <span className="text-red-700"> — {doc.condition_note}</span> : null}</span>],
              ]}
            />

            <SectionCard title={isTraining ? t("Equipment Trained") : t("Equipment Issued")} testId="view-safety-form-items">
              <DataTable
                columns={isTraining ? trainingColumns : issuanceColumns}
                rows={tableRows}
                rowKey={(row) => `${row.idx}-${row.item}`}
                density="compact"
                tableMinWidth={isTraining ? "920px" : "960px"}
                empty={<EmptyState title={t("No items attached.")} message="" icon={FileText} data-testid="view-safety-form-items-empty" />}
                data-testid="view-safety-form-items-table"
              />

              {!isTraining ? (
                <div className="flex justify-end mt-4">
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-right" data-testid="view-safety-form-total">
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-red-900 font-bold">{t("Total Issued Value")}</div>
                    <div className="font-display text-2xl font-black text-slate-900">{fmtMoney(total)}</div>
                  </div>
                </div>
              ) : null}
            </SectionCard>

            {!isTraining && !doc.return ? (
              <SectionCard title={t("Next Step")} testId="view-safety-form-next-step">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-800 font-bold">{t("Equipment still out")}</div>
                    <p className="text-sm text-slate-600 mt-1">{t("When gear comes back, log the check-in here to close accountability, document condition, and calculate any chargeback immediately.")}</p>
                  </div>
                  <Link
                    to={`/safety/forms/equipment-issuance/${id}/return`}
                    className="inline-flex items-center justify-center gap-2 h-11 px-4 rounded-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide text-xs"
                    data-testid="view-checkin-btn"
                  >
                    <PackageCheck className="w-4 h-4" /> {t("Start Check-In / Return")}
                  </Link>
                </div>
              </SectionCard>
            ) : null}

            {!isTraining && doc.return ? (
              <SectionCard title={t("Check-In Receipt")} testId="view-safety-form-return">
                <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-700 font-bold inline-flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> {t("Returned")}
                    </div>
                    <p className="text-sm text-slate-600 mt-1">{formatDateLong(doc.return.check_in_date)} · {t("Received by")} {doc.return.received_by}</p>
                  </div>
                  <Button
                    onClick={() => downloadPdf("/return/pdf", "_return")}
                    disabled={downloading}
                    variant="outline"
                    className="h-10 border-emerald-600 text-emerald-700 hover:bg-emerald-50 font-bold uppercase tracking-wide text-xs"
                    data-testid="view-download-return-pdf"
                  >
                    {downloading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Download className="w-4 h-4 mr-1" />}
                    {t("Download Return PDF")}
                  </Button>
                </div>

                <DataTable
                  columns={returnColumns}
                  rows={returnRows}
                  rowKey={(row) => `${row.idx}-${row.itemLabel}`}
                  density="compact"
                  tableMinWidth="860px"
                  data-testid="view-safety-form-return-table"
                />

                <div className="flex justify-between items-end mt-4 flex-wrap gap-3">
                  {doc.return.return_notes ? (
                    <div className="text-xs text-slate-600 max-w-md">
                      <span className="font-mono text-[9px] uppercase tracking-[0.2em] font-bold text-slate-500">{t("Notes")}: </span>
                      {doc.return.return_notes}
                    </div>
                  ) : <span />}
                  <div className={`rounded-2xl border px-4 py-3 text-right ${(doc.return.chargeback?.total || 0) > 0 ? "bg-red-50 border-red-300" : "bg-emerald-50 border-emerald-300"}`} data-testid="view-safety-form-chargeback">
                    <div className={`font-mono text-[9px] uppercase tracking-[0.22em] font-bold ${(doc.return.chargeback?.total || 0) > 0 ? "text-red-900" : "text-emerald-900"}`}>{t("Total Chargeback")}</div>
                    <div className="font-display text-2xl font-black text-slate-900">{fmtMoney(doc.return.chargeback?.total || 0)}</div>
                    <div className="font-mono text-[9px] text-slate-600 mt-1">{t("Lost")} {fmtMoney(doc.return.chargeback?.lost || 0)} · {t("Damaged")} {fmtMoney(doc.return.chargeback?.damaged || 0)}</div>
                  </div>
                </div>
              </SectionCard>
            ) : null}

            {isTraining && (doc.topics || []).length > 0 ? (
              <SectionCard title={t("Topics Covered")} testId="view-safety-form-topics">
                <div className="flex flex-wrap gap-2">
                  {(doc.topics || []).map((k) => (
                    <span key={k} className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 font-mono text-[10px] uppercase tracking-wide font-bold">
                      {k.replace(/_/g, " ")}
                      {k === "other" && doc.topic_other ? ` — ${doc.topic_other}` : ""}
                    </span>
                  ))}
                </div>
              </SectionCard>
            ) : null}

            {!isTraining && (doc.photos || []).length > 0 ? (
              <SectionCard title={t("Photos")} testId="view-safety-form-photos">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
                  {(doc.photos || []).map((p, i) => (
                    <img key={i} src={resolvePhotoSrc(p)} alt="" loading="lazy" decoding="async" className="w-full h-36 object-cover rounded-xl border border-slate-200" />
                  ))}
                </div>
              </SectionCard>
            ) : null}

            <SectionCard title={t("Sign-Off")} testId="view-safety-form-signoff">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <SigBlock label={t("Employee Signature") + " · " + (doc.employee_name || "")} sig={doc.employee_signature} />
                <SigBlock
                  label={((isTraining ? t("Instructor Signature") : t("Supervisor Signature")) + " · " + (isTraining ? doc.instructor_name : doc.issued_by)) || ""}
                  sig={isTraining ? doc.instructor_signature : doc.supervisor_signature}
                />
              </div>
            </SectionCard>
          </div>

          <div className="space-y-6">
            <SectionCard title={t("Operational status")} testId="view-safety-form-status-panel">
              <div className="space-y-4 text-sm text-slate-700">
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-900 font-bold">{t("Record state")}</div>
                  <div className="mt-1 font-semibold text-slate-900">{t("Submitted and on file")}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">{t("What to do next")}</div>
                  <p className="mt-1 leading-6">{isTraining ? t("Use the PDF if the crew needs a field copy, and reopen training only when a new session is required.") : doc.return ? t("The return receipt closes the accountability loop. Download it for records or chargeback review.") : t("Start the check-in when gear returns so condition, chargeback, and final signatures are captured in the same flow.")}</p>
                </div>
                {!isTraining && !doc.return ? (
                  <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 flex gap-2" data-testid="view-safety-form-return-alert">
                    <AlertTriangle className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
                    <p className="text-sm text-amber-900">{t("This issuance is still open. Do not leave it unresolved once equipment is physically back in the yard or with supervision.")}</p>
                  </div>
                ) : null}
              </div>
            </SectionCard>

            <SectionCard title={t("Record metadata")} testId="view-safety-form-meta-panel">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between gap-3"><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t("Reference")}</span><span className="text-slate-900 font-medium text-right">{recordId}</span></div>
                <div className="flex justify-between gap-3"><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t("Generated")}</span><span className="text-slate-900 font-medium text-right">{doc.created_at ? formatPlatformTime(doc.created_at) : "—"}</span></div>
                <div className="flex justify-between gap-3"><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t("Confidentiality")}</span><span className="text-slate-900 font-medium text-right">{t("Confidential")}</span></div>
              </div>
            </SectionCard>
          </div>
        </div>
      </main>
    </div>
  );

  return wrapWithShell({
    isAdminRoute,
    pageTitle,
    recordLabel: pageTitle,
    subjectLabel: doc.employee_name || doc.id?.slice?.(0, 8)?.toUpperCase() || "Record",
    children: content,
  });
}