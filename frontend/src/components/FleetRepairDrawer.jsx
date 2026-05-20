// FleetRepairDrawer.jsx — iter251 Phase 4 · Repair lifecycle drawers.
//
// Two modal surfaces used by FleetVisibility.jsx:
//   • <RepairDrawer> · Shop logs a repair (mechanic + notes + photos)
//   • <RtsDrawer>    · Dispatch confirms Return-to-Service (intentional)
//
// Both share visual language with the rest of the Fleet module · calm
// operational tone · large tap targets · mobile-first · bilingual.
// They do NOT introduce new design primitives.

import React, { useEffect, useRef, useState } from "react";
import {
  X, Wrench, ShieldCheck, AlertOctagon, MessageSquareQuote,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PhotoUpload } from "@/components/PhotoUpload";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";

function ModalShell({ titleIcon, title, kicker, accent, onClose, children, testId }) {
  const sheetRef = useRef(null);
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose?.(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      className="fixed inset-0 z-[80] flex items-end sm:items-center justify-center bg-slate-900/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      data-testid={testId}
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <div
        ref={sheetRef}
        className="bg-white w-full sm:max-w-lg sm:rounded-md rounded-t-md border-t-4 sm:border-2 max-h-[92vh] overflow-y-auto"
        style={{ borderColor: accent }}
      >
        <div className="sticky top-0 bg-white border-b-2 border-slate-200 px-4 py-3 flex items-center justify-between gap-3">
          <div className="min-w-0 flex items-center gap-2.5">
            <div
              className="inline-flex items-center justify-center w-9 h-9 rounded-md text-white shrink-0"
              style={{ backgroundColor: accent }}
            >
              {titleIcon}
            </div>
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-500">
                {kicker}
              </div>
              <div className="font-display text-base sm:text-lg font-bold text-slate-900 truncate">
                {title}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-900"
            data-testid={`${testId}-close`}
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="px-4 py-4">{children}</div>
      </div>
    </div>
  );
}

function DefectContextStrip({ defect, t }) {
  if (!defect) return null;
  const unit = defect.truck_unit_number || defect.trailer_unit_number || "—";
  const sevIsOos = defect.severity === "oos";
  return (
    <div className="bg-slate-50 border-2 border-slate-200 rounded-md px-3 py-2.5 mb-4">
      <div className="flex items-center gap-2 mb-1">
        <span
          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider text-white ${sevIsOos ? "bg-red-700" : "bg-amber-600"}`}
        >
          {sevIsOos ? <AlertOctagon className="w-3 h-3" /> : <Wrench className="w-3 h-3" />}
          {sevIsOos ? t("Out of Service") : t("Monitor")}
        </span>
        <span className="font-mono text-[11px] uppercase tracking-wider text-slate-700 font-bold">
          {unit}
        </span>
      </div>
      <div className="text-sm font-semibold text-slate-900 leading-snug">
        {defect.checklist_item}
      </div>
      {defect.driver_note && (
        <div className="mt-1.5 flex items-start gap-1.5 text-[13px] text-slate-700 italic bg-amber-50/60 border-l-2 border-amber-400 pl-2 py-1 rounded-sm">
          <MessageSquareQuote className="w-3.5 h-3.5 shrink-0 text-amber-700 mt-0.5" />
          <span>"{defect.driver_note}"</span>
        </div>
      )}
      {Array.isArray(defect.photos) && defect.photos.length > 0 && (
        <div className="mt-2 grid grid-cols-3 gap-1.5">
          {defect.photos.slice(0, 6).map((src, i) => (
            <img
              key={i}
              src={src}
              alt=""
              className="w-full h-16 object-cover rounded border border-slate-200"
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function RepairDrawer({ open, defect, accent, onClose, onSubmit }) {
  const { t } = useT();
  const [mechanic, setMechanic] = useState("");
  const [notes, setNotes] = useState("");
  const [photos, setPhotos] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (open) { setMechanic(""); setNotes(""); setPhotos([]); setErr(""); }
  }, [open, defect?.defect_id]);

  if (!open || !defect) return null;

  const canSubmit = mechanic.trim().length >= 2 && notes.trim().length >= 5 && !submitting;

  const submit = async () => {
    setErr("");
    setSubmitting(true);
    try {
      await onSubmit({
        actor_name: mechanic.trim(),
        notes: notes.trim(),
        photos,
      });
    } catch (e) {
      setErr(e?.message || String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalShell
      titleIcon={<Wrench className="w-4 h-4" />}
      title={t("Log Repair")}
      kicker={t("Shop · Repair Lifecycle")}
      accent={accent}
      onClose={onClose}
      testId="fleet-repair-drawer"
    >
      <DefectContextStrip defect={defect} t={t} />

      {/* Phase 5 · contextual coaching from /api/guidance/tips */}
      <HelpTipBlock formKey="fleet.repair" className="mb-4" />

      <div className="space-y-3">
        <div>
          <label className="block text-[11px] font-mono uppercase tracking-wider font-bold text-slate-700 mb-1">
            {t("Mechanic / Repair owner")}
          </label>
          <input
            type="text"
            value={mechanic}
            onChange={(e) => setMechanic(e.target.value)}
            placeholder={t("Name of the person performing the repair")}
            className="w-full h-11 px-3 border-2 border-slate-300 rounded-md text-sm focus:border-slate-900 focus:outline-none"
            data-testid="fleet-repair-mechanic-input"
          />
        </div>

        <div>
          <label className="block text-[11px] font-mono uppercase tracking-wider font-bold text-slate-700 mb-1">
            {t("Repair notes")}
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder={t("What was inspected and what was done (parts, adjustments, retorques, etc.)")}
            className="w-full px-3 py-2 border-2 border-slate-300 rounded-md text-sm focus:border-slate-900 focus:outline-none resize-y"
            data-testid="fleet-repair-notes-input"
          />
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mt-0.5">
            {notes.trim().length < 5
              ? t("≥ 5 characters")
              : `${notes.trim().length} ${t("characters")}`}
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-mono uppercase tracking-wider font-bold text-slate-700 mb-1">
            {t("Repair photos (optional)")}
          </label>
          <PhotoUpload
            photos={photos}
            onChange={setPhotos}
            testIdBase="fleet-repair-photo"
          />
        </div>

        {err && (
          <div
            className="bg-red-50 border-2 border-red-300 text-red-900 rounded-md px-3 py-2 text-sm"
            data-testid="fleet-repair-error"
          >
            {err}
          </div>
        )}

        <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-end gap-2 pt-1">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-11 text-sm"
            data-testid="fleet-repair-cancel"
          >
            {t("Cancel")}
          </Button>
          <Button
            onClick={submit}
            disabled={!canSubmit}
            className="h-11 text-sm"
            style={{ backgroundColor: accent, color: "white" }}
            data-testid="fleet-repair-submit"
          >
            <Wrench className="w-4 h-4 mr-1.5" />
            {submitting ? t("Saving…") : t("Mark Repaired")}
          </Button>
        </div>

        <div className="text-[11px] text-slate-500 leading-snug pt-1">
          {t("Logging the repair flags the defect as awaiting Dispatch Return-to-Service. The unit will not roll until Dispatch confirms.")}
        </div>
      </div>
    </ModalShell>
  );
}

export function RtsDrawer({ open, defect, accent, onClose, onSubmit }) {
  const { t } = useT();
  const [dispatcher, setDispatcher] = useState("");
  const [note, setNote] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (open) { setDispatcher(""); setNote(""); setConfirm(false); setErr(""); }
  }, [open, defect?.defect_id]);

  if (!open || !defect) return null;

  const canSubmit = dispatcher.trim().length >= 2 && confirm && !submitting;

  const submit = async () => {
    setErr("");
    setSubmitting(true);
    try {
      await onSubmit({
        actor_name: dispatcher.trim(),
        notes: note.trim(),
        photos: [],
      });
    } catch (e) {
      setErr(e?.message || String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalShell
      titleIcon={<ShieldCheck className="w-4 h-4" />}
      title={t("Confirm Return to Service")}
      kicker={t("Dispatch · Return-to-Service")}
      accent={accent}
      onClose={onClose}
      testId="fleet-rts-drawer"
    >
      <DefectContextStrip defect={defect} t={t} />

      {/* Phase 5 · contextual coaching from /api/guidance/tips */}
      <HelpTipBlock formKey="fleet.rts" className="mb-4" />

      {defect.repair_notes && (
        <div className="bg-emerald-50 border-2 border-emerald-200 rounded-md px-3 py-2 mb-3">
          <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-emerald-900 mb-0.5">
            {t("Shop repair note")}
          </div>
          <div className="text-sm text-emerald-900 leading-snug">
            {defect.repair_notes}
          </div>
          {defect.repaired_by_name && (
            <div className="text-[11px] text-emerald-800 mt-1 font-mono">
              {t("by")} {defect.repaired_by_name}
              {defect.repaired_at && ` · ${new Date(defect.repaired_at).toLocaleString()}`}
            </div>
          )}
          {Array.isArray(defect.repair_photos) && defect.repair_photos.length > 0 && (
            <div className="mt-2 grid grid-cols-3 gap-1.5">
              {defect.repair_photos.slice(0, 6).map((src, i) => (
                <img
                  key={i}
                  src={src}
                  alt=""
                  className="w-full h-16 object-cover rounded border border-emerald-300"
                />
              ))}
            </div>
          )}
        </div>
      )}

      <div className="space-y-3">
        <div>
          <label className="block text-[11px] font-mono uppercase tracking-wider font-bold text-slate-700 mb-1">
            {t("Dispatcher confirming")}
          </label>
          <input
            type="text"
            value={dispatcher}
            onChange={(e) => setDispatcher(e.target.value)}
            placeholder={t("Your name")}
            className="w-full h-11 px-3 border-2 border-slate-300 rounded-md text-sm focus:border-slate-900 focus:outline-none"
            data-testid="fleet-rts-dispatcher-input"
          />
        </div>

        <div>
          <label className="block text-[11px] font-mono uppercase tracking-wider font-bold text-slate-700 mb-1">
            {t("Dispatch note (optional)")}
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            placeholder={t("Anything Dispatch should record alongside the return-to-service")}
            className="w-full px-3 py-2 border-2 border-slate-300 rounded-md text-sm focus:border-slate-900 focus:outline-none resize-y"
            data-testid="fleet-rts-note-input"
          />
        </div>

        <label
          className="flex items-start gap-2.5 cursor-pointer bg-amber-50 border-2 border-amber-300 rounded-md px-3 py-2.5"
          data-testid="fleet-rts-confirm-label"
        >
          <input
            type="checkbox"
            checked={confirm}
            onChange={(e) => setConfirm(e.target.checked)}
            className="mt-0.5 w-5 h-5 accent-emerald-700"
            data-testid="fleet-rts-confirm-checkbox"
          />
          <span className="text-sm text-amber-900 leading-snug">
            {t("I have reviewed the Shop repair record and confirm this unit is safe to return to service.")}
          </span>
        </label>

        {err && (
          <div
            className="bg-red-50 border-2 border-red-300 text-red-900 rounded-md px-3 py-2 text-sm"
            data-testid="fleet-rts-error"
          >
            {err}
          </div>
        )}

        <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-end gap-2 pt-1">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-11 text-sm"
            data-testid="fleet-rts-cancel"
          >
            {t("Cancel")}
          </Button>
          <Button
            onClick={submit}
            disabled={!canSubmit}
            className="h-11 text-sm"
            style={{ backgroundColor: accent, color: "white" }}
            data-testid="fleet-rts-submit"
          >
            <ShieldCheck className="w-4 h-4 mr-1.5" />
            {submitting ? t("Saving…") : t("Return to Service")}
          </Button>
        </div>
      </div>
    </ModalShell>
  );
}
