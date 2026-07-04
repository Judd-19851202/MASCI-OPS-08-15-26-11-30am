import React, { useState } from "react";
import { CheckCircle2, AlertOctagon, AlertTriangle, Loader2, Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import EmployeeRosterField from "@/components/EmployeeRosterField";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useT, getLang } from "@/lib/i18n";
import { translateUserInput } from "@/lib/translateOnSubmit";
import { isShop } from "@/lib/shopAuth";
import { isAdmin } from "@/lib/adminAuth";

/**
 * One sign-off card per FAIL line on a Pre-Op inspection. Shop / admin only.
 * - If no signoff yet: shows form (signed_by, action_taken, notes, button)
 * - If signed off:    shows the stamp + a Reopen button
 *
 * Backed by:
 *   POST   /api/admin/equipment-inspections/{id}/signoff
 *   DELETE /api/admin/equipment-inspections/{id}/signoff?section=&item=
 */
const ACTION_KEYS = ["Repaired", "Tagged out of service", "Parts ordered", "No action needed"];

export default function ShopSignoffCard({
  inspectionId,
  section,
  item,
  severity, // "oos" | "attn"
  existing, // signoff doc or null
  onChange,
}) {
  const { t } = useT();
  const canSignOff = isShop() || isAdmin();
  const [signedBy, setSignedBy] = useState("");
  const [signedByEmployeeId, setSignedByEmployeeId] = useState(""); // iter364 · canonical roster id
  const [action, setAction] = useState(ACTION_KEYS[0]);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);

  if (!canSignOff) return null;

  const sevPill =
    severity === "oos" ? (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-black tracking-[0.1em] bg-red-700 text-white">
        <AlertOctagon className="w-3 h-3" /> {t("OUT OF SERVICE")}
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-black tracking-[0.1em] bg-amber-500 text-white">
        <AlertTriangle className="w-3 h-3" /> {t("NEEDS ATTENTION")}
      </span>
    );

  const sign = async () => {
    if (!signedBy.trim()) {
      toast.error(t("Enter your name to sign off."));
      return;
    }
    setBusy(true);
    try {
      let payload = {
        section,
        item,
        signed_by: signedBy.trim(),
        signed_by_employee_id: signedByEmployeeId || "",
        action_taken: action,
        notes: notes.trim(),
      };
      // ES → EN: translate freeform "notes" before persisting.
      // signed_by is a proper noun and action_taken is a fixed enum, so
      // they're left as-is.
      payload = await translateUserInput(payload, getLang());
      const r = await api.post(`/admin/equipment-inspections/${inspectionId}/signoff`, payload);
      toast.success(t("Signed off."));
      onChange && onChange(r.data?.signoff || null);
    } catch {
      toast.error(t("Could not save sign-off."));
    } finally {
      setBusy(false);
    }
  };

  const reopen = async () => {
    if (!window.confirm(t("Reopen this item? The shop sign-off stamp will be removed."))) return;
    setBusy(true);
    try {
      await api.delete(
        `/admin/equipment-inspections/${inspectionId}/signoff?section=${encodeURIComponent(section)}&item=${encodeURIComponent(item)}`
      );
      toast.success(t("Reopened."));
      onChange && onChange(null);
    } catch {
      toast.error(t("Could not reopen."));
    } finally {
      setBusy(false);
    }
  };

  if (existing) {
    return (
      <div
        className="mt-3 border-2 border-emerald-500 bg-emerald-50 rounded-md p-3 print:border print:border-slate-300 print:bg-white"
        data-testid={`signoff-stamp-${section}-${item}`}
      >
        <div className="flex items-start gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">
            <div className="font-display font-black text-emerald-800 uppercase tracking-wide text-xs">
              {t("Shop signed off")} · {existing.action_taken || "—"}
            </div>
            <div className="text-emerald-900 mt-0.5">
              {t("By")}: <span className="font-bold">{existing.signed_by}</span>
              {" · "}
              <span className="font-mono text-xs">
                {existing.signed_at ? new Date(existing.signed_at).toLocaleString() : "—"}
              </span>
            </div>
            {existing.notes && (
              <div className="text-emerald-900 italic mt-1">&quot;{existing.notes}&quot;</div>
            )}
          </div>
          <Button
            type="button"
            onClick={reopen}
            disabled={busy}
            variant="outline"
            size="sm"
            className="border-emerald-700 text-emerald-700 hover:bg-emerald-100 print:hidden h-8 px-2"
            data-testid={`signoff-reopen-${section}-${item}`}
          >
            {busy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Undo2 className="w-3 h-3 mr-1" />}
            {t("Reopen")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="mt-3 border-2 border-amber-300 bg-amber-50 rounded-md p-3 print:hidden"
      data-testid={`signoff-form-${section}-${item}`}
    >
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-800 font-black">
          {t("Shop Sign-Off")}
        </span>
        {sevPill}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        {/* iter364 · Shop sign-off identity captured atomically (name +
            canonical employee_id) via the same roster-first selector
            used on Incidents / PPE / Training / Pre-Op / QA-QC / CAPA. */}
        <EmployeeRosterField
          label=""
          value={{ id: signedByEmployeeId, name: signedBy, linked: !!signedByEmployeeId }}
          onChange={({ id, name, linked }) => {
            setSignedBy(name);
            setSignedByEmployeeId(linked ? id : "");
          }}
          placeholder={t("Your name (mechanic / shop)")}
          testId={`signoff-by-${section}-${item}-roster`}
        />
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="h-9 text-sm rounded-md border border-amber-300 px-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
          data-testid={`signoff-action-${section}-${item}`}
        >
          {ACTION_KEYS.map((k) => (
            <option key={k} value={k}>{t(k)}</option>
          ))}
        </select>
      </div>
      <Textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder={t("Optional notes (parts replaced, follow-up needed, etc.)")}
        rows={2}
        className="mt-2 text-sm border-amber-300 focus-visible:ring-amber-500"
        data-testid={`signoff-notes-${section}-${item}`}
      />
      <div className="mt-2 flex justify-end">
        <Button
          type="button"
          onClick={sign}
          disabled={busy}
          className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide text-xs h-9 px-4"
          data-testid={`signoff-submit-${section}-${item}`}
        >
          {busy ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <CheckCircle2 className="w-4 h-4 mr-1" />}
          {t("Sign Off")}
        </Button>
      </div>
    </div>
  );
}
