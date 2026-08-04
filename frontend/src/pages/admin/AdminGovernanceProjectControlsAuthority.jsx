import React, { useEffect, useMemo, useState } from "react";
import { ClipboardList, GitBranchPlus, Layers3, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/lib/i18n";
import { operatorStatusLabel, sanitizeOperatorCopy } from "@/lib/operatorLanguage";
import {
  fetchAdminProjectControlsOverview,
  fetchProjectControlsEventContracts,
  fetchProjectControlsReviewQueue,
  fetchEnterpriseWorkTypes,
  runAdminProjectControlsBackfill,
  saveEnterpriseWorkType,
} from "@/lib/projectControlsApi";

const TEXT_ES = {
  "Project Controls Standards": "Estándares de Controles del Proyecto",
  "Review company work types, unresolved links, and the data rules behind project controls.": "Revise los tipos de trabajo de la empresa, los vínculos sin resolver y las reglas de datos detrás de los controles del proyecto.",
  Refresh: "Actualizar",
  "Update existing records": "Actualizar registros existentes",
  "Add work type": "Agregar tipo de trabajo",
  "Company work types": "Tipos de trabajo de la empresa",
  "Items needing review": "Elementos que necesitan revisión",
  "Data rules": "Reglas de datos",
  Code: "Código",
  Name: "Nombre",
  Category: "Categoría",
  Status: "Estado",
  Reason: "Motivo",
  Source: "Origen",
  Save: "Guardar",
  Cancel: "Cancelar",
  Description: "Descripción",
  Keywords: "Palabras clave",
};

function localize(value, t, lang) {
  return lang === "es" ? (TEXT_ES[value] || t(value)) : t(value);
}

export default function AdminGovernanceProjectControlsAuthority() {
  const { t, lang } = useT();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [overview, setOverview] = useState(null);
  const [workTypes, setWorkTypes] = useState([]);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [eventContracts, setEventContracts] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", category: "", description: "", keywords: "" });

  const load = async () => {
    setLoading(true);
    try {
      const [overviewData, workTypeData, reviewData, eventData] = await Promise.all([
        fetchAdminProjectControlsOverview(),
        fetchEnterpriseWorkTypes(true),
        fetchProjectControlsReviewQueue(),
        fetchProjectControlsEventContracts(),
      ]);
      setOverview(overviewData || null);
      setWorkTypes(workTypeData?.items || []);
      setReviewQueue(reviewData?.items || []);
      setEventContracts(eventData?.items || []);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load project controls standards."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const cards = useMemo(() => {
    const summary = overview?.summary || {};
    return [
      { label: localize("Company work types", t, lang), value: summary.enterprise_work_types || 0, icon: Layers3 },
      { label: localize("Items needing review", t, lang), value: summary.review_queue_open || 0, icon: ClipboardList },
      { label: localize("Data rules", t, lang), value: eventContracts.length || 0, icon: GitBranchPlus },
    ];
  }, [eventContracts.length, lang, overview, t]);

  const onSave = async () => {
    setSaving(true);
    try {
      await saveEnterpriseWorkType({
        code: form.code,
        name: form.name,
        category: form.category,
        description: form.description,
        keywords: form.keywords.split(",").map((item) => item.trim()).filter(Boolean),
      });
      toast.success(t("Work type saved."));
      setDialogOpen(false);
      setForm({ code: "", name: "", category: "", description: "", keywords: "" });
      await load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not save the work type."));
    } finally {
      setSaving(false);
    }
  };

  const onBackfill = async () => {
    try {
      await runAdminProjectControlsBackfill();
      toast.success(t("Update existing records finished."));
      await load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not update existing records."));
    }
  };

  return (
    <LegacyAdminModernShell
      title={localize("Project Controls Standards", t, lang)}
      subtitle={localize("Review company work types, unresolved links, and the data rules behind project controls.", t, lang)}
    >
      <div className="space-y-6" data-testid="admin-project-controls-authority-page">
        <div className="flex flex-wrap gap-3" data-testid="admin-project-controls-action-row">
          <Button type="button" variant="outline" onClick={load} data-testid="admin-project-controls-refresh-button">
            <RefreshCw className="mr-2 h-4 w-4" /> {localize("Refresh", t, lang)}
          </Button>
          <Button type="button" variant="outline" onClick={onBackfill} data-testid="admin-project-controls-backfill-button">
            <GitBranchPlus className="mr-2 h-4 w-4" /> {localize("Update existing records", t, lang)}
          </Button>
          <Button type="button" onClick={() => setDialogOpen(true)} data-testid="admin-project-controls-add-work-type-button">
            <Layers3 className="mr-2 h-4 w-4" /> {localize("Add work type", t, lang)}
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3" data-testid="admin-project-controls-summary-grid">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <div key={card.label} className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid={`admin-project-controls-summary-${card.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{card.label}</div>
                    <div className="mt-2 text-3xl font-black text-slate-900">{card.value}</div>
                  </div>
                  <div className="rounded-full bg-red-50 p-3 text-red-700"><Icon className="h-5 w-5" /></div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-controls-work-types-section">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-slate-900">{localize("Company work types", t, lang)}</h2>
                <p className="mt-1 text-sm text-slate-600">{t("These stay admin-managed and are reused across projects.")}</p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700" data-testid="admin-project-controls-work-type-count">{workTypes.length}</span>
            </div>
            <div className="mt-4 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{localize("Code", t, lang)}</TableHead>
                    <TableHead>{localize("Name", t, lang)}</TableHead>
                    <TableHead>{localize("Category", t, lang)}</TableHead>
                    <TableHead>{localize("Status", t, lang)}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workTypes.map((row) => (
                    <TableRow key={row.work_type_id} data-testid={`admin-project-controls-work-type-row-${row.work_type_id}`}>
                      <TableCell className="font-semibold text-slate-900">{row.code}</TableCell>
                      <TableCell>
                        <div className="font-medium text-slate-900">{row.name}</div>
                        <div className="text-xs text-slate-500">{row.description || "—"}</div>
                      </TableCell>
                      <TableCell>{row.category || "—"}</TableCell>
                      <TableCell>
                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{operatorStatusLabel(row.status, t)}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!loading && workTypes.length === 0 ? (
                    <TableRow><TableCell colSpan={4} className="py-8 text-center text-sm text-slate-500">{t("No work types found.")}</TableCell></TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </div>
          </section>

          <div className="space-y-6">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-controls-review-section">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-xl font-black text-slate-900">{localize("Items needing review", t, lang)}</h2>
                <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900" data-testid="admin-project-controls-review-count">{reviewQueue.length}</span>
              </div>
              <div className="mt-4 space-y-3">
                {reviewQueue.slice(0, 8).map((row) => (
                  <div key={row.review_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-controls-review-item-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{sanitizeOperatorCopy(row.title, "Review item")}</div>
                      <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700">{operatorStatusLabel(row.status, t)}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{sanitizeOperatorCopy(row.reason, "Review the linked work-type item before moving forward.")}</p>
                    <div className="mt-2 text-xs text-slate-500">{localize("Source", t, lang)}: {row.source_collection || "—"}</div>
                  </div>
                ))}
                {!loading && reviewQueue.length === 0 ? <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">{t("No items need review right now.")}</div> : null}
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-project-controls-events-section">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-xl font-black text-slate-900">{localize("Data rules", t, lang)}</h2>
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-900">{eventContracts.length}</span>
              </div>
              <div className="mt-4 space-y-3">
                {eventContracts.map((row) => (
                  <div key={row.event_key} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`admin-project-controls-event-${row.event_key}`}>
                    <div className="font-semibold text-slate-900">{row.event_key}</div>
                    <div className="mt-1 text-sm text-slate-600">{row.operator_visible_consequence}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Authority")}: {row.authority_owner} · {t("Producer")}: {row.producer}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent data-testid="admin-project-controls-work-type-dialog">
          <DialogHeader>
            <DialogTitle>{localize("Add work type", t, lang)}</DialogTitle>
            <DialogDescription>{t("Create a reusable enterprise work type without touching any project-specific pay item.")}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <Input value={form.code} onChange={(event) => setForm((prev) => ({ ...prev, code: event.target.value }))} placeholder={localize("Code", t, lang)} data-testid="admin-project-controls-work-type-code-input" />
            <Input value={form.name} onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))} placeholder={localize("Name", t, lang)} data-testid="admin-project-controls-work-type-name-input" />
            <Input value={form.category} onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value }))} placeholder={localize("Category", t, lang)} data-testid="admin-project-controls-work-type-category-input" />
            <Textarea value={form.description} onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))} placeholder={localize("Description", t, lang)} data-testid="admin-project-controls-work-type-description-input" />
            <Input value={form.keywords} onChange={(event) => setForm((prev) => ({ ...prev, keywords: event.target.value }))} placeholder={`${localize("Keywords", t, lang)}: asphalt, paving, surface`} data-testid="admin-project-controls-work-type-keywords-input" />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setDialogOpen(false)} data-testid="admin-project-controls-work-type-cancel-button">{localize("Cancel", t, lang)}</Button>
            <Button type="button" onClick={onSave} disabled={saving} data-testid="admin-project-controls-work-type-save-button">{saving ? t("Saving…") : localize("Save", t, lang)}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </LegacyAdminModernShell>
  );
}
