import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Archive, ClipboardList, RefreshCw, Save, UsersRound } from "lucide-react";
import { toast } from "sonner";
import PmShell from "@/components/PmShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useT } from "@/lib/i18n";
import { operatorConfidenceLabel, operatorStatusLabel } from "@/lib/operatorLanguage";
import {
  archivePmProject,
  confirmPmCrew,
  fetchPmCrewIntelligence,
  fetchPmProjectControlsOverview,
  fetchPmProjectLifecycle,
  fetchPmProjectLookahead,
  fetchPmProjectMappings,
  fetchPmProjectPayItems,
  fetchPmProjectWorkLedger,
  fetchPmWorkTypes,
  restorePmProject,
  savePmProjectLifecycle,
  savePmProjectLookahead,
  savePmProjectMapping,
  savePmProjectPayItem,
  setPmCrewSuggestionState,
} from "@/lib/projectControlsApi";

function initialPayItemForm() {
  return {
    customer_pay_item_number: "",
    description: "",
    unit: "EA",
    contract_quantity: "",
    contract_unit_price: "",
    status: "active",
  };
}

export default function PmProjectControlsAuthority() {
  const { t } = useT();
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState(null);
  const [payItems, setPayItems] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [workTypes, setWorkTypes] = useState([]);
  const [lookahead, setLookahead] = useState(null);
  const [lifecycle, setLifecycle] = useState(null);
  const [crewIntel, setCrewIntel] = useState({ confirmed_crews: [], suggestions: [] });
  const [ledgerRows, setLedgerRows] = useState([]);
  const [payItemForm, setPayItemForm] = useState(initialPayItemForm());
  const [mappingForm, setMappingForm] = useState({ pay_item_id: "", primary_work_type_id: "", explanation: "" });

  useEffect(() => {
    const next = params.get("project_number") || "";
    setProjectNumber(next);
  }, [params]);

  const load = async (pn = projectNumber) => {
    if (!pn) return;
    setLoading(true);
    try {
      const [overviewData, payItemData, mappingData, workTypeData, lookaheadData, lifecycleData, crewData, ledgerData] = await Promise.all([
        fetchPmProjectControlsOverview(pn),
        fetchPmProjectPayItems(pn),
        fetchPmProjectMappings(pn),
        fetchPmWorkTypes(),
        fetchPmProjectLookahead(pn),
        fetchPmProjectLifecycle(pn),
        fetchPmCrewIntelligence(pn),
        fetchPmProjectWorkLedger(pn, 25),
      ]);
      setOverview(overviewData || null);
      setPayItems(payItemData?.items || []);
      setMappings(mappingData?.items || []);
      setWorkTypes(workTypeData?.items || []);
      setLookahead(lookaheadData || null);
      setLifecycle(lifecycleData || null);
      setCrewIntel(crewData || { confirmed_crews: [], suggestions: [] });
      setLedgerRows(ledgerData?.items || []);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load project controls."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectNumber) load(projectNumber);
  }, [projectNumber]);

  const counts = useMemo(() => overview?.counts || {}, [overview]);

  const setProject = (pn) => {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (pn) next.set("project_number", pn);
      else next.delete("project_number");
      return next;
    });
  };

  const onSavePayItem = async () => {
    if (!projectNumber) return;
    try {
      await savePmProjectPayItem(projectNumber, {
        ...payItemForm,
        contract_quantity: Number(payItemForm.contract_quantity || 0),
        contract_unit_price: Number(payItemForm.contract_unit_price || 0),
      });
      toast.success(t("Project pay item saved."));
      setPayItemForm(initialPayItemForm());
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not save the project pay item."));
    }
  };

  const onSaveMapping = async () => {
    if (!projectNumber || !mappingForm.pay_item_id) return;
    try {
      await savePmProjectMapping(projectNumber, { ...mappingForm, status: "approved" });
      toast.success(t("Work type link saved."));
      setMappingForm({ pay_item_id: "", primary_work_type_id: "", explanation: "" });
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not save the mapping."));
    }
  };

  const onSaveLookahead = async () => {
    if (!projectNumber || !lookahead) return;
    try {
      await savePmProjectLookahead(projectNumber, lookahead);
      toast.success(t("Two-week lookahead saved."));
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not save the lookahead."));
    }
  };

  const onLifecycle = async (nextState) => {
    if (!projectNumber) return;
    try {
      await savePmProjectLifecycle(projectNumber, { next_state: nextState, reason: `PM set lifecycle to ${nextState}` });
      toast.success(t("Lifecycle updated."));
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not update the lifecycle."));
    }
  };

  const onArchiveToggle = async () => {
    if (!projectNumber || !lifecycle) return;
    try {
      if (lifecycle.archive_status) await restorePmProject(projectNumber, "PM restored archived project for governed access.");
      else await archivePmProject(projectNumber, "PM archived project while preserving all historical records.");
      toast.success(lifecycle.archive_status ? t("Project restored.") : t("Project archived without deleting history."));
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not change archive state."));
    }
  };

  const onCrewAction = async (suggestion, action) => {
    try {
      if (action === "accept") {
        await confirmPmCrew(projectNumber, {
          suggestion_id: suggestion.suggestion_id,
          crew_name: `${suggestion.leader || suggestion.members?.[0] || "Crew"} Crew`,
        });
      } else {
        await setPmCrewSuggestionState(projectNumber, suggestion.suggestion_id, action, `${action}ed from PM project controls authority.`);
      }
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not update the crew suggestion."));
    }
  };

  return (
    <PmShell
      title="Project Controls"
      section="jobs"
      subtitle="Set pay items, work type links, lookahead notes, job status, and crew decisions for this job."
    >
      <div className="space-y-6" data-testid="pm-project-controls-authority-page">
        <div className="rounded-[1.75rem] border border-white/30 bg-white/80 p-5 shadow-sm backdrop-blur" data-testid="pm-project-controls-header-card">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{t("Assigned project scope")}</div>
              <h1 className="mt-2 text-3xl font-black text-slate-900">{t("Project Controls")}</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{t("Pay items stay job-specific, company work types stay admin-managed, and approved links connect the two without changing Daily Reports.")}</p>
            </div>
            <div className="flex gap-3">
              <Button type="button" variant="outline" onClick={() => load(projectNumber)} data-testid="pm-project-controls-refresh-button">
                <RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}
              </Button>
            </div>
          </div>
          <div className="mt-4 max-w-sm" data-testid="pm-project-controls-project-picker-shell">
            <PmProjectSelector projectNumber={projectNumber} onChange={setProject} />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4" data-testid="pm-project-controls-summary-grid">
          {[
            ["pay-items", counts.pay_items || 0, ClipboardList, t("Pay items")],
            ["approved-mappings", counts.approved_mappings || 0, Save, t("Approved links")],
            ["crew-suggestions", counts.crew_suggestions || 0, UsersRound, t("Crew suggestions")],
            ["work-ledger", counts.work_ledger_rows || 0, Archive, t("Work blocks")],
          ].map(([key, value, Icon, label]) => (
            <div key={key} className="rounded-[1.5rem] border border-white/30 bg-white/85 p-4 shadow-sm" data-testid={`pm-project-controls-summary-${key}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</div>
                  <div className="mt-2 text-3xl font-black text-slate-900">{value}</div>
                </div>
                <div className="rounded-full bg-cyan-50 p-3 text-cyan-700"><Icon className="h-5 w-5" /></div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-controls-pay-items-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Project pay items")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("These remain the customer / contract approved record for this project only.")}</p>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700" data-testid="pm-project-controls-pay-item-count">{payItems.length}</span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <Input value={payItemForm.customer_pay_item_number} onChange={(event) => setPayItemForm((prev) => ({ ...prev, customer_pay_item_number: event.target.value }))} placeholder={t("Pay item number")} data-testid="pm-project-controls-pay-item-number-input" />
                <Input value={payItemForm.unit} onChange={(event) => setPayItemForm((prev) => ({ ...prev, unit: event.target.value }))} placeholder={t("Unit")} data-testid="pm-project-controls-pay-item-unit-input" />
                <Input value={payItemForm.description} onChange={(event) => setPayItemForm((prev) => ({ ...prev, description: event.target.value }))} placeholder={t("Description")} data-testid="pm-project-controls-pay-item-description-input" />
                <div className="grid grid-cols-2 gap-3">
                  <Input value={payItemForm.contract_quantity} onChange={(event) => setPayItemForm((prev) => ({ ...prev, contract_quantity: event.target.value }))} placeholder={t("Contract qty")} data-testid="pm-project-controls-pay-item-quantity-input" />
                  <Input value={payItemForm.contract_unit_price} onChange={(event) => setPayItemForm((prev) => ({ ...prev, contract_unit_price: event.target.value }))} placeholder={t("Unit price")} data-testid="pm-project-controls-pay-item-price-input" />
                </div>
              </div>
              <div className="mt-4 flex justify-end">
                <Button type="button" onClick={onSavePayItem} disabled={!projectNumber} data-testid="pm-project-controls-pay-item-save-button">{t("Save pay item")}</Button>
              </div>
              <div className="mt-4 space-y-3">
                {payItems.map((row) => (
                  <div key={row.pay_item_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-controls-pay-item-row-${row.pay_item_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-900">{row.customer_pay_item_number} · {row.description}</div>
                        <div className="mt-1 text-xs text-slate-500">{t("Unit")}: {row.unit || "—"} · {t("Contract value")}: ${(Number(row.contract_value || 0)).toFixed(2)}</div>
                      </div>
                      <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700">{row.status}</span>
                    </div>
                  </div>
                ))}
                {!loading && payItems.length === 0 ? <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">{t("No project pay items entered yet.")}</div> : null}
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-controls-mappings-section">
              <h2 className="text-xl font-black text-slate-900">{t("Approved work type links")}</h2>
              <p className="mt-1 text-sm text-slate-600">{t("Link each pay item to the right company work type. Nothing is approved automatically.")}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" value={mappingForm.pay_item_id} onChange={(event) => setMappingForm((prev) => ({ ...prev, pay_item_id: event.target.value }))} data-testid="pm-project-controls-mapping-pay-item-select">
                  <option value="">{t("Choose pay item")}</option>
                  {payItems.map((row) => <option key={row.pay_item_id} value={row.pay_item_id}>{row.customer_pay_item_number} · {row.description}</option>)}
                </select>
                <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900" value={mappingForm.primary_work_type_id} onChange={(event) => setMappingForm((prev) => ({ ...prev, primary_work_type_id: event.target.value }))} data-testid="pm-project-controls-mapping-work-type-select">
                  <option value="">{t("Choose work type")}</option>
                  {workTypes.map((row) => <option key={row.work_type_id} value={row.work_type_id}>{row.code} · {row.name}</option>)}
                </select>
              </div>
              <Textarea className="mt-3" value={mappingForm.explanation} onChange={(event) => setMappingForm((prev) => ({ ...prev, explanation: event.target.value }))} placeholder={t("Why this mapping is correct for this project.")} data-testid="pm-project-controls-mapping-explanation-input" />
              <div className="mt-4 flex justify-end">
                <Button type="button" onClick={onSaveMapping} disabled={!mappingForm.pay_item_id || !mappingForm.primary_work_type_id} data-testid="pm-project-controls-mapping-save-button">{t("Save link")}</Button>
              </div>
              <div className="mt-4 space-y-3">
                {mappings.map((row) => (
                  <div key={row.mapping_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-controls-mapping-row-${row.mapping_id}`}>
                    <div className="font-semibold text-slate-900">{row.customer_pay_item_number || row.pay_item_id}</div>
                    <div className="mt-1 text-sm text-slate-600">{t("Primary work type")}: {workTypes.find((item) => item.work_type_id === row.primary_work_type_id)?.name || row.primary_work_type_id || t("Pending review")}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Status")}: {operatorStatusLabel(row.status, t)} · {t("Source")}: {row.source}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="space-y-6">
            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-controls-lookahead-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Two-week lookahead")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Field progress can inform this view, but the PM-published plan remains the schedule source.")}</p>
                </div>
                <Button type="button" onClick={onSaveLookahead} disabled={!lookahead} data-testid="pm-project-controls-lookahead-save-button">{t("Save")}</Button>
              </div>
              <Textarea className="mt-4" value={lookahead?.comparison_note || ""} onChange={(event) => setLookahead((prev) => ({ ...(prev || {}), comparison_note: event.target.value }))} placeholder={t("Planned vs actual note")} data-testid="pm-project-controls-lookahead-note-input" />
              <div className="mt-4 space-y-3">
                {(lookahead?.tasks || []).slice(0, 6).map((task, index) => (
                  <div key={`${task.code || task.schedule_activity_id}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-controls-lookahead-task-${index}`}>
                    <div className="font-semibold text-slate-900">{task.code || task.schedule_activity_id || t("Task")}</div>
                    <div className="mt-1 text-sm text-slate-600">{task.title || t("Planned work")}</div>
                    <div className="mt-2 text-xs text-slate-500">{task.planned_start || "—"} → {task.planned_finish || "—"} · {task.responsible_party || t("PM / Field")}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-controls-lifecycle-section">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-slate-900">{t("Job status & archive")}</h2>
                  <p className="mt-1 text-sm text-slate-600">{t("Archiving keeps history. Every record stays searchable under the same permissions.")}</p>
                </div>
                <Button type="button" variant="outline" onClick={onArchiveToggle} disabled={!lifecycle} data-testid="pm-project-controls-archive-toggle-button">{lifecycle?.archive_status ? t("Restore job") : t("Archive job")}</Button>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {(lifecycle?.allowed_states || []).map((state) => (
                  <Button key={state} type="button" variant={lifecycle?.current_state === state ? "default" : "outline"} size="sm" onClick={() => onLifecycle(state)} data-testid={`pm-project-controls-lifecycle-state-${state.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}>
                    {operatorStatusLabel(state, t)}
                  </Button>
                ))}
              </div>
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700" data-testid="pm-project-controls-lifecycle-summary">
                {t("Current state")}: <strong>{operatorStatusLabel(lifecycle?.current_state, t)}</strong> · {t("Archive")}: <strong>{lifecycle?.archive_status ? t("Archived") : t("Active")}</strong>
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-controls-crew-section">
              <h2 className="text-xl font-black text-slate-900">{t("Crew suggestions")}</h2>
              <p className="mt-1 text-sm text-slate-600">{t("Crew patterns stay suggestions until a person confirms them.")}</p>
              <div className="mt-4 space-y-3">
                {(crewIntel?.suggestions || []).slice(0, 5).map((row) => (
                  <div key={row.suggestion_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-controls-crew-suggestion-${row.suggestion_id}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-900">{row.leader || t("Crew leader suggestion")}</div>
                        <div className="mt-1 text-sm text-slate-600">{(row.members || []).join(", ")}</div>
                        <div className="mt-2 text-xs text-slate-500">{t("Observed")}: {row.observation_count} · {t("Confidence")}: {operatorConfidenceLabel(row.confidence, t)}</div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Button type="button" size="sm" onClick={() => onCrewAction(row, "accept")} data-testid={`pm-project-controls-crew-accept-${row.suggestion_id}`}>{t("Confirm")}</Button>
                        <Button type="button" size="sm" variant="outline" onClick={() => onCrewAction(row, "defer")} data-testid={`pm-project-controls-crew-defer-${row.suggestion_id}`}>{t("Defer")}</Button>
                        <Button type="button" size="sm" variant="ghost" onClick={() => onCrewAction(row, "reject")} data-testid={`pm-project-controls-crew-reject-${row.suggestion_id}`}>{t("Reject")}</Button>
                      </div>
                    </div>
                  </div>
                ))}
                {(crewIntel?.confirmed_crews || []).slice(0, 5).map((row) => (
                  <div key={row.crew_id} className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4" data-testid={`pm-project-controls-confirmed-crew-${row.crew_id}`}>
                    <div className="font-semibold text-emerald-900">{row.crew_name}</div>
                    <div className="mt-1 text-sm text-emerald-800">{(row.members || []).join(", ")}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-controls-ledger-section">
              <h2 className="text-xl font-black text-slate-900">{t("Recent work blocks")}</h2>
              <p className="mt-1 text-sm text-slate-600">{t("This ledger stays additive: Daily Reports remain the source for field actuals.")}</p>
              <div className="mt-4 space-y-3">
                {ledgerRows.slice(0, 6).map((row) => (
                  <div key={row.ledger_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-controls-ledger-row-${row.ledger_id}`}>
                    <div className="font-semibold text-slate-900">{row.title || t("Work block")}</div>
                    <div className="mt-1 text-sm text-slate-600">{row.report_date || "—"} · {row.customer_pay_item_number || row.cost_code || t("No linked cost code yet")}</div>
                    <div className="mt-2 text-xs text-slate-500">{t("Resources")}: {row.resource_counts?.labor || 0} {t("labor")}, {row.resource_counts?.equipment || 0} {t("equipment")}, {row.resource_counts?.materials || 0} {t("materials")}</div>
                  </div>
                ))}
                {!loading && ledgerRows.length === 0 ? <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">{t("No work blocks yet. Daily Reports will add them automatically when field work is entered.")}</div> : null}
              </div>
            </section>
          </div>
        </div>
      </div>
    </PmShell>
  );
}
