import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { Printer, Loader2, Trash2, Mail, AlertOctagon, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RefKicker } from "@/components/RefKicker";
import BackLink from "@/components/BackLink";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { formatDateLong } from "@/lib/utils";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { PhotoLightbox } from "@/components/PhotoLightbox";
import { PhotoZipDownload } from "@/components/PhotoZipDownload";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { EmailReportDialog } from "@/components/EmailReportDialog";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import ShopSignoffCard from "@/components/ShopSignoffCard";
import { itemSeverity } from "@/lib/equipmentSeverity";
import { isAdmin } from "@/lib/adminAuth";
import { useT } from "@/lib/i18n";
import { formatEmployeeIdentity } from "@/lib/identity";
import { sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const KV = ({ label, value, full = false }) => (
  <div className={full ? "lg:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      {label}
    </div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
      {value || "—"}
    </div>
  </div>
);

const StatusPill = ({ status }) => {
  const { t } = useT();
  const map = {
    pass: { cls: "wp17-status-badge wp17-tone--emerald", label: t("PASS") },
    fail: { cls: "wp17-status-badge wp17-tone--red", label: t("FAIL") },
    na: { cls: "wp17-status-badge wp17-tone--slate", label: t("N/A") },
  };
  const v = map[status] || { cls: "wp17-status-badge wp17-tone--slate", label: "—" };
  return (
    <span className={`inline-flex items-center justify-center ${v.cls}`}>
      {v.label}
    </span>
  );
};

export default function ViewEquipmentInspection({ context = "admin" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { t } = useT();
  const isAdminRoute = pathname.startsWith("/admin/");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emailOpen, setEmailOpen] = useState(false);

  const isShopContext = context === "shop";
  // Portal-aware back href: shop context always sends to /shop; otherwise
  // strip the trailing /<id> from the current pathname so /pm/equipment/<id>
  // bounces to /pm/equipment and /admin/equipment/<id> bounces to /admin/equipment.
  const backHref = isShopContext
    ? "/shop"
    : (pathname.replace(/\/[^/]+$/, "") || "/admin/equipment");
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/equipment-inspections/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error(t("Inspection not found"));
        navigate(backHref);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [backHref, id, navigate, t]);  

  useEffect(() => {
    if (!loading && data) maybeAutoPrint();
  }, [loading, data]);

  const onDelete = async () => {
    if (!window.confirm(t("Permanently delete this equipment inspection?"))) return;
    try {
      await api.delete(`/equipment-inspections/${id}`);
      toast.success(t("Deleted"));
      navigate(backHref);
    } catch {
      toast.error(t("Could not delete"));
    }
  };

  // Update a single signoff entry in local state so the UI reflects the
  // new state without a full reload.
  const updateSignoff = (section, item, signoffEntry) => {
    setData((prev) => {
      if (!prev) return prev;
      const key = `${section}|${item}`;
      const current = (prev.shop_signoffs || []).filter((s) => s.key !== key);
      const next = signoffEntry ? [...current, signoffEntry] : current;
      return { ...prev, shop_signoffs: next };
    });
  };

  if (loading) {
    const loadingContent = (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 animate-spin text-red-700" />
      </div>
    );
    return isAdminRoute ? (
      <AdminRouteShell
        pageTitle="Equipment Inspection"
        subtitle="Admin review for pre-op findings, sign-offs, and unit readiness."
        portalRole="Admin · Equipment Inspections"
        crumbs={[{ label: "Field Operations" }, { label: "Equipment Pre-Op" }]}
        testId="admin-view-equipment-inspection-shell"
      >
        {loadingContent}
      </AdminRouteShell>
    ) : loadingContent;
  }
  if (!data) return null;

  const fail = (data.fail_count || 0) > 0;
  const signoffsByKey = Object.fromEntries(
    (data.shop_signoffs || []).map((s) => [s.key, s])
  );

  const content = (
    <div className="min-h-screen bg-slate-50 print:bg-white pb-32 print:pb-0">
      <PrintWatermark />
      <div className="caution-stripe print:hidden" />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 print:py-0 space-y-5">
        <div className="print:hidden flex flex-wrap items-center justify-between gap-3">
          <BackLink
            to={backHref}
            label={isShopContext ? t("Shop Operations") : t("Equipment Pre-Op")}
            variant="body"
            testId="back-link"
          />
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => setEmailOpen(true)} variant="outline" size="sm" data-testid="email-btn">
              <Mail className="w-4 h-4 mr-1" /> {t("Email")}
            </Button>
            <Button onClick={() => printReport()} size="sm" data-testid="print-btn">
              <Printer className="w-4 h-4 mr-1" /> {t("Print")}
            </Button>
            {isAdmin() && (
              <Button onClick={onDelete} variant="outline" size="sm" data-testid="delete-btn">
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        <Card className="print-section">
          <CardContent className="p-5 sm:p-7">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <span className="font-mono text-xs uppercase tracking-[0.22em] text-red-700">{t("Equipment Pre-Op Inspection")}</span>
              {/* iter336 · review-side reference continuity */}
              <RefKicker
                recordId={data.inspection_number || data.id}
                testId="view-equip-inspection-ref"
                className="mt-1"
              />
              <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
                {data.equipment_type} · {data.equipment_unit}
              </h1>
              <div className="text-sm text-slate-600 mt-2 flex items-center gap-2 flex-wrap">
                {data.doc_id && (
                  <span
                    className="wp17-status-badge wp17-tone--red"
                    data-testid="record-doc-id-badge"
                  >
                    <span className="text-[9px] uppercase tracking-[0.22em]">Doc ID</span>
                    {data.doc_id}
                  </span>
                )}
                <span>{formatDateLong(data.inspection_date)} · {data.inspection_time} · {data.location}</span>
              </div>
              {data.submit_language === "es" && (
                <div className="mt-2">
                  <SubmitLangBadge lang={data.submit_language} />
                </div>
              )}
            </div>
            {fail && (
              <div className="wp17-status-badge wp17-tone--red !px-4 !py-2 flex items-center gap-2">
                <AlertOctagon className="w-5 h-5 text-red-700" />
                <span className="font-display font-black text-red-700 text-sm uppercase tracking-wide">
                  Fail — Out of Service
                </span>
              </div>
            )}
          </div>
          </CardContent>
        </Card>

        <Card className="print-section">
          <CardHeader className="pb-4"><CardTitle>Project & Operator</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <KV label="Project" value={sanitizeOperatorReference(data.project_name, "Operations support work")} />
            <KV label="Project #" value={sanitizeOperatorProjectNumber(data.project_number, "Operations support")} />
            <KV label="Location" value={sanitizeOperatorReference(data.location, "—")} full />
            <KV label="Operator" value={sanitizeOperatorReference(formatEmployeeIdentity(data) || data.operator_name, "Operator record")} />
            <KV label="Date / Time" value={`${data.inspection_date} ${data.inspection_time}`} />
          </CardContent>
        </Card>

        <Card className="print-section">
          <CardHeader className="pb-4"><CardTitle>Equipment</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
            <KV label="Type" value={data.equipment_type} />
            <KV label="Unit" value={data.equipment_unit} />
            <KV label="Make" value={data.equipment_make} />
            <KV label="Model" value={data.equipment_model} />
            <KV label="Serial #" value={data.equipment_serial} />
            <KV label="Hour Meter / Odometer" value={data.hour_meter || data.odometer} />
          </CardContent>
        </Card>

        {/* Tally */}
        <Card className="print-section">
          <CardHeader className="pb-4"><CardTitle>{t("Inspection Summary")}</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap items-center gap-4">
            <div className="text-center">
              <div className="font-display text-3xl font-black text-emerald-700" data-testid="view-pass-count">{data.pass_count || 0}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">{t("Pass")}</div>
            </div>
            <div className="text-center">
              <div className="font-display text-3xl font-black text-red-700" data-testid="view-fail-count">{data.fail_count || 0}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">{t("Fail")}</div>
            </div>
            <div className="text-center">
              <div className="font-display text-3xl font-black text-slate-600" data-testid="view-na-count">{data.na_count || 0}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">{t("N/A")}</div>
            </div>
            <div className="ml-auto">
              <div className={`wp17-status-badge ${fail ? "wp17-tone--red" : "wp17-tone--emerald"} !px-4 !py-2`}>
                {fail ? "Out of Service" : "Cleared to Operate"}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Checklist sections */}
        {Object.entries(data.checklist || {}).map(([sectionTitle, items]) => (
          <Card key={sectionTitle} className="print-section">
            <CardHeader className="pb-4"><CardTitle>{sectionTitle}</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {Object.entries(items).map(([item, res]) => {
                const isFail = res?.status === "fail";
                const sev = isFail ? itemSeverity(item) : null;
                const key = `${sectionTitle}|${item}`;
                const existing = signoffsByKey[key] || null;
                return (
                  <div key={item} className={`py-1.5 border-b border-slate-100 last:border-0 ${
                    isFail
                      ? sev === "oos"
                        ? "border-l-4 border-l-red-700 pl-3"
                        : "border-l-4 border-l-amber-500 pl-3"
                      : ""
                  }`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 text-sm text-slate-800">
                        {item}
                        {isFail && (
                          <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-black tracking-[0.1em] align-middle"
                            style={sev === "oos" ? { background: "#b91c1c", color: "white" } : { background: "#f59e0b", color: "white" }}>
                            {sev === "oos" ? <><AlertOctagon className="w-2.5 h-2.5" /> {t("OOS")}</> : <><AlertTriangle className="w-2.5 h-2.5" /> {t("ATTN")}</>}
                          </span>
                        )}
                        {res?.note && (
                          <div className="text-xs text-slate-500 italic mt-0.5">{res.note}</div>
                        )}
                        {res?.photo && (
                          <PhotoLightbox
                            src={res.photo}
                            alt={`Failure evidence — ${item}`}
                            filename={`MASCI_EquipFail_${(data.id || id || "").slice(0, 8)}_${item.replace(/[^A-Za-z0-9]+/g, "_").slice(0, 30)}.jpg`}
                            className="mt-2 inline-block"
                            testId={`equip-failphoto-${item}`}
                          >
                            <img
                              src={res.photo}
                              alt="Failure evidence"
                              className="w-32 h-24 object-cover rounded border-2 border-red-300"
                            />
                          </PhotoLightbox>
                        )}
                      </div>
                      <StatusPill status={res?.status} />
                    </div>
                    {isFail && (
                      <ShopSignoffCard
                        inspectionId={data.id || id}
                        section={sectionTitle}
                        item={item}
                        severity={sev}
                        existing={existing}
                        onChange={(entry) => updateSignoff(sectionTitle, item, entry)}
                      />
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        ))}

        {(data.deficiency_notes || data.corrective_actions) && (
          <Card className="print-section">
            <CardHeader className="pb-4"><CardTitle>Notes & Corrective Actions</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
              <KV label="Deficiencies" value={data.deficiency_notes} />
              <KV label="Corrective Actions" value={data.corrective_actions} />
            </CardContent>
          </Card>
        )}

        {data.photos && data.photos.length > 0 && (
          <Card className="print-section">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between gap-3">
                <CardTitle>Photos ({data.photos.length})</CardTitle>
              <PhotoZipDownload
                photos={data.photos}
                prefix={`MASCI_Equipment_${(data.id || id || "").slice(0, 8)}_photos`}
                testId="equipment-photos-zip"
              />
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
              {data.photos.map((p, i) => (
                <PhotoLightbox
                  key={i}
                  src={resolvePhotoSrc(p)}
                  alt={`Equipment Photo ${i + 1}`}
                  filename={`MASCI_Equipment_${(data.id || id || "").slice(0, 8)}_photo${i + 1}.jpg`}
                  className="block w-full"
                  testId={`equip-photo-${i}`}
                >
                  <img src={resolvePhotoSrc(p)} alt={`Photo ${i + 1}`} loading="lazy" decoding="async" className="w-full aspect-[4/3] object-cover rounded border border-slate-200" />
                </PhotoLightbox>
              ))}
            </CardContent>
          </Card>
        )}

        {data.operator_signature && (
          <Card className="print-section">
            <CardHeader className="pb-4"><CardTitle>Sign-Off</CardTitle></CardHeader>
            <CardContent>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-2">Operator: {sanitizeOperatorReference(formatEmployeeIdentity(data) || data.operator_name, "Operator record")}</div>
              <img src={resolvePhotoSrc(data.operator_signature)} alt="Operator signature" className="max-h-32 border-b-2 border-slate-300" />
            </CardContent>
          </Card>
        )}
      </main>

      <EmailReportDialog
        open={emailOpen}
        onOpenChange={setEmailOpen}
        kind="equipment-inspection"
        recordId={id}
        record={data}
      />
    </div>
  );

  return isAdminRoute ? (
    <AdminRouteShell
      pageTitle="Equipment Inspection"
      subtitle="Admin review for pre-op findings, sign-offs, and unit readiness."
      portalRole="Admin · Equipment Inspections"
      crumbs={[
        { label: "Field Operations" },
        { label: "Equipment Pre-Op" },
        { label: data.equipment_unit || data.id?.slice(0, 8)?.toUpperCase() || "Inspection" },
      ]}
      contentClassName="px-0 py-0"
      testId="admin-view-equipment-inspection-shell"
    >
      {content}
    </AdminRouteShell>
  ) : content;
}
