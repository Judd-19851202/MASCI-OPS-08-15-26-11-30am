import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, FolderTree, Link2, RefreshCw, Search, UserRoundCog } from "lucide-react";
import { toast } from "sonner";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";
import {
  createGovernanceHierarchyNode,
  fetchGovernanceHierarchyAssignments,
  fetchGovernanceHierarchyNodeDetail,
  fetchGovernanceHierarchyNodes,
  fetchGovernanceHierarchyOverview,
  fetchGovernanceHierarchyReviewQueue,
  fetchGovernanceHierarchyScope,
  runGovernanceHierarchyBackfill,
  setGovernanceHierarchyNodeState,
  updateGovernanceHierarchyNode,
} from "@/lib/enterpriseGovernanceApi";

const TEXT_ES = {
  "Organization Structure": "Estructura organizativa",
  "Manage the current operating structure without replacing existing project, people, equipment, or field records.": "Administre la estructura operativa actual sin reemplazar registros existentes de proyectos, personas, equipos o campo.",
  Refresh: "Actualizar",
  "Re-scan current records": "Volver a revisar registros actuales",
  "Add organization item": "Agregar elemento organizativo",
  Search: "Buscar",
  "name, code, or path": "nombre, código o ruta",
  "All structure types": "Todos los tipos",
  Company: "Compañía",
  Division: "División",
  Department: "Departamento",
  Region: "Región",
  Facility: "Instalación",
  Project: "Proyecto",
  Contract: "Contrato",
  Phase: "Fase",
  "Work Package": "Paquete de trabajo",
  "Cost Code": "Código de costo",
  Activity: "Actividad",
  Plant: "Planta",
  Yard: "Patio",
  Shop: "Taller",
  "Current structure": "Estructura actual",
  "Review queue": "Cola de revisión",
  Assignments: "Asignaciones",
  "Scope preview": "Vista previa de alcance",
  Name: "Nombre",
  Type: "Tipo",
  Path: "Ruta",
  Status: "Estado",
  Bindings: "Vinculaciones",
  Active: "Activo",
  Archived: "Archivado",
  Inactive: "Inactivo",
  "No structure items match these filters.": "Ningún elemento coincide con estos filtros.",
  Details: "Detalles",
  Children: "Elementos hijos",
  "Source bindings": "Vinculaciones de origen",
  "Resource assignments": "Asignaciones de recursos",
  "No item selected yet.": "Todavía no se seleccionó ningún elemento.",
  "Choose an organization item to review its place, linked records, and downstream readiness.": "Elija un elemento organizativo para revisar su ubicación, registros vinculados y preparación posterior.",
  Edit: "Editar",
  Activate: "Activar",
  Deactivate: "Desactivar",
  Archive: "Archivar",
  "Create organization item": "Crear elemento organizativo",
  "Update organization item": "Actualizar elemento organizativo",
  Save: "Guardar",
  Cancel: "Cancelar",
  Description: "Descripción",
  Code: "Código",
  Parent: "Padre",
  "Display order": "Orden visible",
  "External reference": "Referencia externa",
  "Created the organization item.": "Se creó el elemento organizativo.",
  "Updated the organization item.": "Se actualizó el elemento organizativo.",
  "Backfill finished.": "La vinculación inicial terminó.",
  "Could not load organization structure.": "No se pudo cargar la estructura organizativa.",
  "Could not save the organization item.": "No se pudo guardar el elemento organizativo.",
  "Could not refresh the structure.": "No se pudo actualizar la estructura.",
  "Could not update item status.": "No se pudo actualizar el estado del elemento.",
  Email: "Correo",
  "all current identities": "todas las identidades actuales",
  "Matched identities": "Identidades coincidentes",
  Reason: "Motivo",
};

const TYPE_OPTIONS = [
  ["company", "Company"],
  ["division", "Division"],
  ["department", "Department"],
  ["region", "Region"],
  ["facility", "Facility"],
  ["project", "Project"],
  ["contract", "Contract"],
  ["phase", "Phase"],
  ["work_package", "Work Package"],
  ["cost_code", "Cost Code"],
  ["schedule_activity", "Activity"],
];

const FACILITY_OPTIONS = [["plant", "Plant"], ["yard", "Yard"], ["shop", "Shop"]];

function tone(active, archived) {
  if (archived) return "border-rose-200 bg-rose-50 text-rose-700";
  if (active) return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-amber-200 bg-amber-50 text-amber-700";
}

function humanType(value) {
  return TYPE_OPTIONS.find(([key]) => key === value)?.[1] || value;
}

function localize(value, t, lang) {
  if (typeof value !== "string") return value;
  const translated = t(value);
  if (lang !== "es" || translated !== value) return translated;
  return TEXT_ES[value] || value;
}

function SummaryCard({ icon: Icon, label, value, detail, testId }) {
  return (
    <div className="rounded-[1.5rem] border border-[color:var(--border-hairline)] bg-white/95 p-5 shadow-[0_16px_36px_rgba(15,23,42,0.08)]" data-testid={testId}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</div>
          <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
        </div>
        <div className="rounded-full bg-slate-100 p-3 text-slate-700"><Icon className="h-5 w-5" /></div>
      </div>
      <div className="mt-3 text-sm text-slate-600">{detail}</div>
    </div>
  );
}

function NodeDialog({ open, onOpenChange, onSubmit, form, setForm, parentOptions, t, isEditing }) {
  const lt = (value) => t(value);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="hierarchy-item-dialog">
        <DialogHeader>
          <DialogTitle>{lt(isEditing ? "Update organization item" : "Create organization item")}</DialogTitle>
          <DialogDescription>{lt("Manage the current operating structure without replacing existing project, people, equipment, or field records.")}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            {lt("Type")}
            <Select value={form.type} onValueChange={(value) => setForm((prev) => ({ ...prev, type: value, subtype: value === "facility" ? prev.subtype || "yard" : "" }))}>
              <SelectTrigger data-testid="hierarchy-form-type-select"><SelectValue placeholder={lt("All structure types")} /></SelectTrigger>
              <SelectContent>{TYPE_OPTIONS.map(([value, label]) => <SelectItem key={value} value={value}>{lt(label)}</SelectItem>)}</SelectContent>
            </Select>
          </label>
          {form.type === "facility" ? (
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              {lt("Facility")}
              <Select value={form.subtype} onValueChange={(value) => setForm((prev) => ({ ...prev, subtype: value }))}>
                <SelectTrigger data-testid="hierarchy-form-subtype-select"><SelectValue /></SelectTrigger>
                <SelectContent>{FACILITY_OPTIONS.map(([value, label]) => <SelectItem key={value} value={value}>{lt(label)}</SelectItem>)}</SelectContent>
              </Select>
            </label>
          ) : <div />}
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            {lt("Code")}
            <Input data-testid="hierarchy-form-code-input" value={form.code} onChange={(e) => setForm((prev) => ({ ...prev, code: e.target.value }))} disabled={isEditing} />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            {lt("Name")}
            <Input data-testid="hierarchy-form-name-input" value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700 md:col-span-2">
            {lt("Parent")}
            <Select value={form.parent_id || "__none__"} onValueChange={(value) => setForm((prev) => ({ ...prev, parent_id: value === "__none__" ? "" : value }))}>
              <SelectTrigger data-testid="hierarchy-form-parent-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">—</SelectItem>
                {parentOptions.map((option) => <SelectItem key={option.id} value={option.id}>{`${option.name} · ${humanType(option.type)}`}</SelectItem>)}
              </SelectContent>
            </Select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700 md:col-span-2">
            {lt("Description")}
            <Textarea data-testid="hierarchy-form-description-input" value={form.description} onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))} />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            {lt("Display order")}
            <Input data-testid="hierarchy-form-display-order-input" type="number" value={form.display_order} onChange={(e) => setForm((prev) => ({ ...prev, display_order: e.target.value }))} />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            {lt("External reference")}
            <Input data-testid="hierarchy-form-external-reference-input" value={form.external_source_identifier} onChange={(e) => setForm((prev) => ({ ...prev, external_source_identifier: e.target.value }))} />
          </label>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="hierarchy-form-cancel-button">{lt("Cancel")}</Button>
          <Button onClick={onSubmit} data-testid="hierarchy-form-submit-button">{lt("Save")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function AdminGovernanceHierarchyFoundation() {
  const { t, lang } = useT();
  const lt = useCallback((value) => localize(value, t, lang), [lang, t]);
  const [overview, setOverview] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [detail, setDetail] = useState(null);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [scope, setScope] = useState([]);
  const [search, setSearch] = useState("");
  const [scopeEmail, setScopeEmail] = useState("");
  const [typeFilter, setTypeFilter] = useState("__all__");
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ type: "division", subtype: "", code: "", name: "", parent_id: "", description: "", display_order: 0, external_source_identifier: "" });

  const loadAll = useCallback(async (keepSelected = true) => {
    setLoading(true);
    try {
      const [overviewData, nodeData, reviewData, assignmentData, scopeData] = await Promise.all([
        fetchGovernanceHierarchyOverview(),
        fetchGovernanceHierarchyNodes({ search, node_type: typeFilter === "__all__" ? "" : typeFilter }),
        fetchGovernanceHierarchyReviewQueue(),
        fetchGovernanceHierarchyAssignments(),
        fetchGovernanceHierarchyScope(scopeEmail ? { email: scopeEmail } : {}),
      ]);
      setOverview(overviewData);
      setNodes(nodeData.items || []);
      setReviewQueue(reviewData.items || []);
      setAssignments(assignmentData.items || []);
      setScope(scopeData.items || []);
      const targetId = keepSelected ? (selectedId || nodeData.items?.[0]?.id || "") : (nodeData.items?.[0]?.id || "");
      setSelectedId(targetId);
      if (targetId) {
        setDetail(await fetchGovernanceHierarchyNodeDetail(targetId));
      } else {
        setDetail(null);
      }
    } catch (error) {
      toast.error(operationalError(error, lt("Could not load organization structure.")));
    } finally {
      setLoading(false);
    }
  }, [lt, scopeEmail, search, selectedId, typeFilter]);

  useEffect(() => { loadAll(false); }, [loadAll]);

  const parentOptions = useMemo(() => nodes.filter((row) => row.id !== selectedId && !row.archive_status), [nodes, selectedId]);
  const selectedNode = detail?.node || null;

  const openCreate = () => {
    setEditing(false);
    setForm({ type: "division", subtype: "", code: "", name: "", parent_id: overview?.current_masci_hierarchy?.company?.id || "", description: "", display_order: 0, external_source_identifier: "" });
    setDialogOpen(true);
  };

  const openEdit = () => {
    if (!selectedNode) return;
    setEditing(true);
    setForm({
      type: selectedNode.type,
      subtype: selectedNode.subtype || "",
      code: selectedNode.code || "",
      name: selectedNode.name || "",
      parent_id: selectedNode.parent_id || "",
      description: selectedNode.description || "",
      display_order: selectedNode.display_order || 0,
      external_source_identifier: selectedNode.external_source_identifier || "",
    });
    setDialogOpen(true);
  };

  const saveItem = async () => {
    try {
      if (editing && selectedNode) {
        await updateGovernanceHierarchyNode(selectedNode.id, form);
        toast.success(lt("Updated the organization item."));
      } else {
        await createGovernanceHierarchyNode(form);
        toast.success(lt("Created the organization item."));
      }
      setDialogOpen(false);
      await loadAll(false);
    } catch (error) {
      toast.error(operationalError(error, lt("Could not save the organization item.")));
    }
  };

  const runBackfill = async () => {
    try {
      await runGovernanceHierarchyBackfill();
      toast.success(lt("Backfill finished."));
      await loadAll(false);
    } catch (error) {
      toast.error(operationalError(error, lt("Could not refresh the structure.")));
    }
  };

  const changeState = async (action) => {
    if (!selectedNode) return;
    try {
      await setGovernanceHierarchyNodeState(selectedNode.id, action, { reason: `${action} from organization structure workspace` });
      await loadAll(true);
    } catch (error) {
      toast.error(operationalError(error, lt("Could not update item status.")));
    }
  };

  return (
    <LegacyAdminModernShell
      title="Organization Structure"
      subtitle="Manage the current operating structure without replacing existing project, people, equipment, or field records."
      breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Organization" }]}
      testidPrefix="admin-governance-hierarchy"
      primaryActions={
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => loadAll(true)} data-testid="hierarchy-refresh-button"><RefreshCw className="mr-2 h-4 w-4" />{lt("Refresh")}</Button>
          <Button variant="outline" onClick={runBackfill} data-testid="hierarchy-backfill-button">{lt("Re-scan current records")}</Button>
          <Button onClick={openCreate} data-testid="hierarchy-add-button">{lt("Add organization item")}</Button>
        </div>
      }
    >
      <div className="space-y-6" data-testid="hierarchy-foundation-page">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <SummaryCard icon={Building2} label={lt("Current structure")} value={overview?.summary?.total_nodes ?? "—"} detail={`${overview?.summary?.active_nodes ?? 0} active · ${overview?.summary?.archived_nodes ?? 0} archived`} testId="hierarchy-summary-structure" />
          <SummaryCard icon={Link2} label={lt("Bindings")} value={overview?.summary?.bindings_total ?? 0} detail={`${overview?.summary?.projects_bound ?? 0} project links`} testId="hierarchy-summary-bindings" />
          <SummaryCard icon={FolderTree} label={lt("Review queue")} value={overview?.summary?.review_queue_total ?? 0} detail={`${reviewQueue.length} items ready for review`} testId="hierarchy-summary-review" />
          <SummaryCard icon={UserRoundCog} label={lt("Assignments")} value={overview?.summary?.resource_assignments_total ?? 0} detail={`${scope.length} ${lt("Matched identities").toLowerCase()}`} testId="hierarchy-summary-assignments" />
        </div>

        <div className="grid gap-4 rounded-[1.5rem] border border-[color:var(--border-hairline)] bg-white/95 p-5 lg:grid-cols-[1.4fr_0.9fr]" data-testid="hierarchy-main-panel">
          <div className="space-y-4 min-w-0">
            <div className="grid gap-3 md:grid-cols-[1fr_220px]">
              <label className="grid gap-2 text-sm font-medium text-slate-700">
                {lt("Search")}
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} placeholder={lt("name, code, or path")} data-testid="hierarchy-search-input" />
                </div>
              </label>
              <label className="grid gap-2 text-sm font-medium text-slate-700">
                {lt("Type")}
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger data-testid="hierarchy-type-filter"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">{lt("All structure types")}</SelectItem>
                    {TYPE_OPTIONS.map(([value, label]) => <SelectItem key={value} value={value}>{lt(label)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </label>
            </div>

            <Table data-testid="hierarchy-nodes-table">
              <TableHeader>
                <TableRow>
                  <TableHead>{lt("Name")}</TableHead>
                  <TableHead>{lt("Type")}</TableHead>
                  <TableHead>{lt("Path")}</TableHead>
                  <TableHead>{lt("Status")}</TableHead>
                  <TableHead>{lt("Bindings")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {nodes.map((row) => (
                  <TableRow key={row.id} data-state={selectedId === row.id ? "selected" : "default"} onClick={async () => { setSelectedId(row.id); setDetail(await fetchGovernanceHierarchyNodeDetail(row.id)); }} className="cursor-pointer" data-testid={`hierarchy-node-row-${row.id.replace(/[^a-z0-9-]/gi, '-')}`}>
                    <TableCell>
                      <div className="font-semibold text-slate-900">{row.name}</div>
                      <div className="text-xs text-slate-500">{row.code}</div>
                    </TableCell>
                    <TableCell>{lt(humanType(row.type))}{row.subtype ? ` · ${lt(row.subtype.charAt(0).toUpperCase() + row.subtype.slice(1))}` : ""}</TableCell>
                    <TableCell className="max-w-[300px] truncate">{row.ancestry_path}</TableCell>
                    <TableCell><span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${tone(row.active_status, row.archive_status)}`}>{row.archive_status ? lt("Archived") : row.active_status ? lt("Active") : lt("Inactive")}</span></TableCell>
                    <TableCell>{Object.values(row.binding_counts || {}).reduce((sum, value) => sum + Number(value || 0), 0)}</TableCell>
                  </TableRow>
                ))}
                {!loading && nodes.length === 0 ? <TableRow><TableCell colSpan={5} className="text-center text-slate-500" data-testid="hierarchy-empty-state">{lt("No structure items match these filters.")}</TableCell></TableRow> : null}
              </TableBody>
            </Table>
          </div>

          <div className="space-y-4 min-w-0">
            <div className="rounded-[1.25rem] border border-[color:var(--border-hairline)] bg-slate-50/90 p-4" data-testid="hierarchy-detail-panel">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{lt("Details")}</div>
                  <div className="mt-1 text-xl font-black text-slate-900">{selectedNode?.name || lt("No item selected yet.")}</div>
                  <div className="text-sm text-slate-600">{selectedNode ? `${selectedNode.code} · ${lt(humanType(selectedNode.type))}` : lt("Choose an organization item to review its place, linked records, and downstream readiness.")}</div>
                </div>
                {selectedNode ? <div className="flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" onClick={openEdit} data-testid="hierarchy-edit-button">{lt("Edit")}</Button>
                  <Button variant="outline" size="sm" onClick={() => changeState(selectedNode.active_status ? "deactivate" : "activate")} data-testid="hierarchy-toggle-status-button">{selectedNode.active_status ? lt("Deactivate") : lt("Activate")}</Button>
                  <Button variant="outline" size="sm" onClick={() => changeState("archive")} data-testid="hierarchy-archive-button">{lt("Archive")}</Button>
                </div> : null}
              </div>
              {selectedNode ? <div className="mt-4 grid gap-3 text-sm text-slate-700 md:grid-cols-2">
                <div data-testid="hierarchy-detail-path"><span className="font-semibold">{lt("Path")}: </span>{selectedNode.ancestry_path}</div>
                <div data-testid="hierarchy-detail-parent"><span className="font-semibold">{lt("Parent")}: </span>{detail?.ancestry?.slice(-1)?.[0]?.name || "—"}</div>
                <div data-testid="hierarchy-detail-children"><span className="font-semibold">{lt("Children")}: </span>{detail?.children?.length || 0}</div>
                <div data-testid="hierarchy-detail-bindings"><span className="font-semibold">{lt("Bindings")}: </span>{detail?.bindings?.length || 0}</div>
              </div> : null}
            </div>

            <div className="grid gap-4 lg:grid-cols-1 xl:grid-cols-1">
              <div className="rounded-[1.25rem] border border-[color:var(--border-hairline)] bg-white p-4" data-testid="hierarchy-review-queue-panel">
                <div className="text-sm font-semibold text-slate-900">{lt("Review queue")}</div>
                <div className="mt-3 space-y-3">
                  {reviewQueue.slice(0, 4).map((item) => <div key={item.review_id} className="rounded-2xl border border-amber-200 bg-amber-50 p-3" data-testid={`hierarchy-review-item-${item.review_id.replace(/[^a-z0-9-]/gi, '-')}`}><div className="font-semibold text-amber-900">{item.source_label}</div><div className="text-xs text-amber-700">{item.reason}</div></div>)}
                  {reviewQueue.length === 0 ? <div className="text-sm text-slate-500">No unresolved hierarchy mappings.</div> : null}
                </div>
              </div>

              <div className="rounded-[1.25rem] border border-[color:var(--border-hairline)] bg-white p-4" data-testid="hierarchy-assignment-panel">
                <div className="text-sm font-semibold text-slate-900">{lt("Assignments")}</div>
                <div className="mt-3 space-y-2 text-sm text-slate-700">
                  {assignments.slice(0, 5).map((item) => <div key={item.assignment_id} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2" data-testid={`hierarchy-assignment-${item.assignment_id.replace(/[^a-z0-9-]/gi, '-')}`}><span>{item.metadata?.email || item.resource_id}</span><span className="text-xs text-slate-500">{item.project_scope || item.facility_scope || item.assigned_node_id}</span></div>)}
                </div>
              </div>

              <div className="rounded-[1.25rem] border border-[color:var(--border-hairline)] bg-white p-4" data-testid="hierarchy-scope-panel">
                <div className="flex flex-wrap items-end gap-3">
                  <label className="grid flex-1 gap-2 text-sm font-medium text-slate-700">
                    {lt("Email")}
                    <Input value={scopeEmail} onChange={(e) => setScopeEmail(e.target.value)} placeholder={lt("all current identities")} data-testid="hierarchy-scope-email-input" />
                  </label>
                  <Button variant="outline" onClick={() => loadAll(true)} data-testid="hierarchy-scope-refresh-button">{lt("Scope preview")}</Button>
                </div>
                <div className="mt-3 space-y-2">
                  {scope.slice(0, 4).map((item, index) => <div key={`${item.identity?.email || 'scope'}-${index}`} className="rounded-xl bg-slate-50 px-3 py-2" data-testid={`hierarchy-scope-item-${index}`}><div className="font-semibold text-slate-900">{item.identity?.display_name || item.identity?.email}</div><div className="text-xs text-slate-600">{(item.scope_preview?.project_scope || []).slice(0, 4).join(" · ") || "Company-wide preview"}</div></div>)}
                  {scope.length === 0 ? <div className="text-sm text-slate-500">No scope preview records matched.</div> : null}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <NodeDialog open={dialogOpen} onOpenChange={setDialogOpen} onSubmit={saveItem} form={form} setForm={setForm} parentOptions={parentOptions} t={lt} isEditing={editing} />
    </LegacyAdminModernShell>
  );
}