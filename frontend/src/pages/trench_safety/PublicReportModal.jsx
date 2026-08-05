// Public Field Reporting modal — Damage / Unsafe Condition / Missing Pins /
// Missing Labels. Wired to the existing public damage-report endpoint
// (now extended with a `kind` field, server-side validated).
//
// Per GAP-4: reports create records for Safety review; do NOT modify the
// asset; do NOT change status automatically; ARE auditable.
import React, { useState } from "react";
import { X, Send, CheckCircle2, Loader2, AlertTriangle } from "lucide-react";
import axios from "axios";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { useT } from "@/lib/i18n";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { buildSubmissionConfirmation } from "@/lib/submissionConfirmation";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const KINDS = [
  { value: "Damage",            label: "Damage" },
  { value: "Unsafe Condition",  label: "Unsafe Condition" },
  { value: "Missing Pins",      label: "Missing Pins" },
  { value: "Missing Labels",    label: "Missing Labels" },
];

export default function PublicReportModal({
  open,
  onClose,
  defaultAssetId = "",
  lockAssetId = false,
}) {
  // Remount the form when the modal opens so the inputs are fresh,
  // without violating react-hooks/set-state-in-effect.
  return open ? (
    <PublicReportModalInner
      key={`rpt-${defaultAssetId}`}
      onClose={onClose}
      defaultAssetId={defaultAssetId}
      lockAssetId={lockAssetId}
    />
  ) : null;
}

function PublicReportModalInner({ onClose, defaultAssetId, lockAssetId }) {
  const { t } = useT();
  const [kind, setKind] = useState(KINDS[0].value);
  const [assetId, setAssetId] = useState(defaultAssetId);
  const [description, setDescription] = useState("");
  const [name, setName] = useState("");
  const [contact, setContact] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await axios.post(`${API}/trench-safety/public/damage-report`, {
        asset_id: assetId.trim().toUpperCase(),
        kind,
        description: description.trim(),
        reported_by_name: name.trim() || null,
        contact: contact.trim() || null,
      });
      if (r.data?.ok) {
        setDone(r.data);
      } else {
        setErr(t("Could not submit. Try again."));
      }
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || t("Could not submit. Try again."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-3"
      data-testid="public-report-modal"
      onClick={onClose}
    >
      <div
        className="wp17-public-card max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div className="inline-flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-700" />
            <h2 className="font-display text-lg font-black text-slate-900">
              {t("Report a Problem")}
            </h2>
          </div>
          <button
            onClick={onClose}
            data-testid="public-report-close"
            aria-label={t("Close")}
            className="text-slate-500 hover:text-slate-900"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {done ? (
          <div className="p-5" data-testid="public-report-success">
            <SubmissionConfirmation
              embedded
              confirmation={buildSubmissionConfirmation({
                workflowKey: "trench-report",
                documentNumber: done.doc_id || "",
                submittedAt: done.received_at || new Date().toISOString(),
                submittedBy: name.trim() || "Anonymous",
                contextItems: [{ label: "Asset", value: assetId.trim().toUpperCase() }],
                followUpRequired: "No further action is required from you at this time.",
                expectedProcessingStatus: "Filed and open for Shop and Safety review",
                note: "The asset stays unchanged until Shop reviews this report.",
                startAnother: {
                  label: "Start Another",
                  onClick: () => {
                    setDone(false);
                    setDescription("");
                    setName("");
                    setContact("");
                    setErr("");
                  },
                },
                returnToPortal: { label: "Return to Portal", onClick: onClose },
              })}
            />
          </div>
        ) : (
          <form onSubmit={submit} className="p-5 space-y-4">
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{t("What's wrong?")}</label>
              <div className="mt-1 grid grid-cols-2 gap-2">
                {KINDS.map((k) => (
                  <button
                    key={k.value}
                    type="button"
                    onClick={() => setKind(k.value)}
                    data-testid={`public-report-kind-${k.value.toLowerCase().replace(/\s+/g, "-")}`}
                    className={
                      "text-left px-3 py-2 rounded border-2 text-sm font-bold " +
                      (kind === k.value
                        ? "border-amber-500 bg-amber-50 text-amber-900"
                        : "border-slate-200 bg-white text-slate-700 hover:border-amber-300")
                    }
                  >
                    {t(k.label)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="rpt-asset-id" className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
                {t("Asset ID")}
              </label>
              <Input
                id="rpt-asset-id"
                required
                value={assetId}
                onChange={(e) => setAssetId(e.target.value)}
                placeholder="TB-07"
                disabled={lockAssetId}
                className="h-10 mt-1 border-2 font-mono uppercase"
                data-testid="public-report-asset-id"
              />
            </div>

            <div>
              <label htmlFor="rpt-desc" className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
                {t("What did you see? (5+ characters)")}
              </label>
              <Textarea
                id="rpt-desc"
                required
                minLength={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t("e.g. crack near top rail on the east side; missing R-pin on spreader…")}
                rows={3}
                className="mt-1 border-2"
                data-testid="public-report-desc"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div>
                <label htmlFor="rpt-name" className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
                  {t("Your name (optional)")}
                </label>
                <Input id="rpt-name" value={name} onChange={(e) => setName(e.target.value)} className="h-10 mt-1 border-2" data-testid="public-report-name" />
              </div>
              <div>
                <label htmlFor="rpt-contact" className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
                  {t("Contact (optional)")}
                </label>
                <Input id="rpt-contact" value={contact} onChange={(e) => setContact(e.target.value)} placeholder={t("phone or email")} className="h-10 mt-1 border-2" data-testid="public-report-contact" />
              </div>
            </div>

            {err && (
              <div className="text-sm text-red-800 bg-red-50 border border-red-200 rounded p-2" data-testid="public-report-error">
                {err}
              </div>
            )}

            <div className="text-xs text-slate-500 leading-relaxed">
              {t("Your report goes to MASCI Safety for review. Submitting does not change the asset's status — Shop and Safety decide next steps.")}
            </div>

            <Button
              type="submit"
              disabled={busy || description.trim().length < 5 || !assetId.trim()}
              data-testid="public-report-submit"
              className="w-full h-12 bg-cyan-700 hover:bg-cyan-800 disabled:bg-slate-300 text-white font-bold uppercase tracking-[0.12em] text-sm inline-flex items-center justify-center gap-2"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {t("Submit Report")}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
