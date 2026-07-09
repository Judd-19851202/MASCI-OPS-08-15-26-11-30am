/**
 * AssignmentDrawer.jsx · iter394 · DLS Operational Flow Board.
 *
 * Right-side slide-over for a single dispatch_assignment. Surfaces:
 *   1. Full state_history timeline (read-only, latest → oldest).
 *   2. Issue a driver magic-link (creates `/d/{token}` URL · copy + open).
 *   3. Cancel the assignment (with reason).
 *   4. Reassign driver / truck.
 *   5. Revoke an active driver session (if any).
 *
 * Restraint: this component has NO state-machine logic of its own —
 * every action is a thin call to an existing iter392/iter393 endpoint
 * and the lifecycle engine remains the single source of truth.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  X, Link2, Copy, Ban, Replace, ShieldOff, Clock, CheckCircle2, AlertTriangle, Pencil, Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import AttachmentStrip from "@/components/dispatch/AttachmentStrip";
import OperationalMomentsRail from "@/components/dispatch/OperationalMomentsRail";
import DispatchDecisionChip from "@/components/dispatch/DispatchDecisionChip";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders(tenantOverride) {
  const headers = { "Content-Type": "application/json" };
  const admin = getAdminToken();
  const disp = getDispatchToken();
  if (admin) headers["X-Admin-Token"] = admin;
  if (disp) headers["X-Dispatch-Token"] = disp;
  if (tenantOverride) headers["X-Tenant-Id"] = tenantOverride;
  return headers;
}

function fmtDt(iso) {
  if (!iso) return "—";
  try {
    return formatPlatformTime(iso);
  } catch {
    return iso;
  }
}

function HistoryEntry({ entry, idx, isLatest }) {
  const standard = entry.standard !== false;
  const tag = entry.warning_tag;
  return (
    <li
      data-testid={`history-entry-${idx}`}
      className={`relative pl-6 pr-2 py-2 border-l-2 ${
        isLatest ? "border-orange-500" : "border-slate-200"
      }`}
    >
      <span
        className={`absolute left-[-7px] top-3 inline-block w-3 h-3 rounded-full ${
          standard ? "bg-emerald-500" : "bg-amber-500"
        }`}
      />
      <div className="flex items-center gap-2 text-sm">
        <span className="font-bold text-slate-900">
          {entry.from_state ? `${entry.from_state} → ` : ""}{entry.to_state}
        </span>
        {tag ? (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-bold uppercase tracking-wide">
            {tag.replace(/_/g, " ")}
          </span>
        ) : null}
      </div>
      <div className="text-xs text-slate-500">
        {fmtDt(entry.at)} · {entry.by_name || "system"} <span className="text-slate-400">({entry.by_role || "—"})</span>
      </div>
      {entry.wait_reason ? (
        <div className="text-xs text-rose-700 mt-0.5">
          Wait reason: {entry.wait_reason.replace(/_/g, " ")}
        </div>
      ) : null}
      {entry.note ? (
        <div className="text-xs text-slate-600 mt-0.5 italic">&quot;{entry.note}&quot;</div>
      ) : null}
      {entry.correction_reason ? (
        <div className="text-xs text-amber-700 mt-0.5">
          Correction: {entry.correction_reason}
        </div>
      ) : null}
    </li>
  );
}

export default function AssignmentDrawer({
  assignment, tenantOverride, onClose, onChanged, onRemoved,
}) {
  const { t } = useT();
  const [magic, setMagic] = useState(null);          // { url, magic_token, expires_at }
  const [activeSessions, setActiveSessions] = useState([]);
  const [busy, setBusy] = useState(null);

  // Reassign form
  const [reassignOpen, setReassignOpen] = useState(false);
  const [newDriverId, setNewDriverId] = useState("");
  const [newDriverName, setNewDriverName] = useState("");
  const [newTruckId, setNewTruckId] = useState("");
  const [reassignReason, setReassignReason] = useState("");

  // Cancel form
  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

  // D-1.5 · Revise form
  const [reviseOpen, setReviseOpen] = useState(false);
  const [rSource, setRSource] = useState("");
  const [rDestination, setRDestination] = useState("");
  const [rMaterial, setRMaterial] = useState("");
  const [rLoadCount, setRLoadCount] = useState("");
  const [rNote, setRNote] = useState("");
  const [rReason, setRReason] = useState("");

  const open = !!assignment;

  // Load active driver sessions for this assignment's driver (for the
  // revoke action). Only the dispatcher needs this; the read is cheap.
  useEffect(() => {
    if (!open || !assignment?.driver_id) { setActiveSessions([]); return; }
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(
          `${API}/api/dispatch/driver/sessions?active_only=true&limit=20`,
          { headers: authHeaders(tenantOverride) },
        );
        const j = await r.json().catch(() => ({}));
        if (cancelled) return;
        const mine = (j.sessions || []).filter((s) => s.driver_id === assignment.driver_id);
        setActiveSessions(mine);
      } catch {
        if (!cancelled) setActiveSessions([]);
      }
    })();
    return () => { cancelled = true; };
  }, [open, assignment?.driver_id, assignment?.id, tenantOverride]);

  const reset = useCallback(() => {
    setMagic(null);
    setReassignOpen(false);
    setCancelOpen(false);
    setNewDriverId(""); setNewDriverName(""); setNewTruckId(""); setReassignReason("");
    setCancelReason("");
    setReviseOpen(false);
    setRSource(""); setRDestination(""); setRMaterial("");
    setRLoadCount(""); setRNote(""); setRReason("");
    setBusy(null);
  }, []);

  const close = useCallback(() => {
    reset();
    onClose && onClose();
  }, [onClose, reset]);

  const issueMagicLink = useCallback(async () => {
    if (!assignment?.driver_id) {
      toast.error("Assign a driver before issuing a magic link.");
      return;
    }
    setBusy("magic");
    try {
      const r = await fetch(`${API}/api/dispatch/driver/magic-link`, {
        method: "POST",
        headers: authHeaders(tenantOverride),
        body: JSON.stringify({
          driver_id: assignment.driver_id,
          driver_name: assignment.driver_name || "",
          truck_id: assignment.truck_id || "",
          assignment_id: assignment.id,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || !j.url) {
        toast.error(j.detail || "Could not issue magic link.");
        return;
      }
      // Rewrite the URL to use the public preview/prod host
      // (request.base_url on the backend gives the upstream cluster).
      const path = (j.url || "").split("/d/").pop();
      const publicHost = window.location.origin;
      const publicUrl = `${publicHost}/d/${path}${tenantOverride ? `?tenant=${encodeURIComponent(tenantOverride)}` : ""}`;
      setMagic({ ...j, public_url: publicUrl });
      toast.success("Magic link issued · valid 15 minutes");
    } catch {
      toast.error("Network error issuing magic link.");
    } finally {
      setBusy(null);
    }
  }, [assignment, tenantOverride]);

  const copyMagicLink = useCallback(async () => {
    if (!magic?.public_url) return;
    try {
      await navigator.clipboard.writeText(magic.public_url);
      toast.success("Link copied · hand to driver");
    } catch {
      toast.error("Could not copy — long-press the link to copy manually.");
    }
  }, [magic]);

  // D-2.4 · "Text Magic Link" · backend issues link + sends SMS in one call.
  // Always returns 200 — body carries sms_status. Any non-"sent" result
  // surfaces the copy-link fallback.
  const sendMagicSms = useCallback(async () => {
    if (!assignment?.id) return;
    setBusy("sms");
    try {
      const r = await fetch(
        `${API}/api/dispatch/assignments/${assignment.id}/send-magic-sms`,
        { method: "POST", headers: authHeaders(tenantOverride) },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        toast.error(j.detail || "Could not send SMS — copy the link instead.");
        // Still try to populate the link for fallback if backend included it.
        if (j.magic_link_url) {
          const path = (j.magic_link_url || "").split("/d/").pop();
          const publicHost = window.location.origin;
          setMagic({ public_url: `${publicHost}/d/${path}` });
        }
        return;
      }
      // Always update the magic state so copy-link is still available
      // as fallback if user wants it.
      if (j.magic_link_url) {
        const path = (j.magic_link_url || "").split("/d/").pop();
        const publicHost = window.location.origin;
        setMagic({ public_url: `${publicHost}/d/${path}` });
      }
      if (j.sms_status === "sent") {
        toast.success(
          `SMS sent to ${j.destination_phone_masked || "driver"}.`,
        );
      } else if (j.sms_status === "skipped" && /phone/i.test(j.error_summary || "")) {
        toast.error("No valid driver phone on file — copy link manually.");
      } else if (j.sms_status === "skipped") {
        toast.message("SMS disabled — copy link to hand off manually.");
      } else {
        toast.error(
          j.error_summary
            ? `SMS failed (${j.error_summary}) — copy link instead.`
            : "SMS failed — copy link instead.",
        );
      }
    } catch {
      toast.error("Network error — copy link instead.");
    } finally {
      setBusy(null);
    }
  }, [assignment?.id, tenantOverride]);

  const cancelAssignment = useCallback(async () => {
    if (!cancelReason.trim()) {
      toast.error("Provide a cancel reason.");
      return;
    }
    setBusy("cancel");
    try {
      const r = await fetch(
        `${API}/api/dispatch/assignments/${assignment.id}/cancel`,
        {
          method: "POST",
          headers: authHeaders(tenantOverride),
          body: JSON.stringify({ reason: cancelReason.trim() }),
        },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        toast.error(j.detail || "Cancel failed.");
        return;
      }
      onRemoved && onRemoved(assignment.id);
    } catch {
      toast.error("Network error cancelling.");
    } finally {
      setBusy(null);
    }
  }, [assignment?.id, cancelReason, onRemoved, tenantOverride]);

  // D-1.5 · Revise in-flight · POST /assignments/{id}/revise
  const reviseAssignment = useCallback(async () => {
    if (!rReason.trim()) {
      toast.error("Provide a revision reason.");
      return;
    }
    // Build the patch from non-empty fields.
    const patch = { reason: rReason.trim() };
    if (rSource.trim()) patch.source_location = rSource.trim();
    if (rDestination.trim()) patch.destination = rDestination.trim();
    if (rMaterial.trim()) patch.material = rMaterial.trim();
    if (rLoadCount.trim()) {
      const n = Number(rLoadCount);
      if (!Number.isFinite(n) || n < 0) {
        toast.error("Load count must be a non-negative number.");
        return;
      }
      patch.load_count = n;
    }
    if (rNote.trim()) patch.note = rNote.trim();
    if (Object.keys(patch).length === 1) {
      toast.error("Change at least one field.");
      return;
    }
    setBusy("revise");
    try {
      const r = await fetch(
        `${API}/api/dispatch/assignments/${assignment.id}/revise`,
        {
          method: "POST",
          headers: authHeaders(tenantOverride),
          body: JSON.stringify(patch),
        },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        toast.error(j.detail || "Revise failed.");
        return;
      }
      onChanged && onChanged(j.assignment);
      setReviseOpen(false);
      setRSource(""); setRDestination(""); setRMaterial("");
      setRLoadCount(""); setRNote(""); setRReason("");
      toast.success("Assignment revised · driver must re-acknowledge.");
    } catch {
      toast.error("Network error revising.");
    } finally {
      setBusy(null);
    }
  }, [assignment?.id, rSource, rDestination, rMaterial, rLoadCount, rNote, rReason, onChanged, tenantOverride]);

  const reassignAssignment = useCallback(async () => {
    if (!newDriverId && !newDriverName && !newTruckId) {
      toast.error("Provide at least one of: driver id, driver name, truck id.");
      return;
    }
    setBusy("reassign");
    try {
      const r = await fetch(
        `${API}/api/dispatch/assignments/${assignment.id}/reassign`,
        {
          method: "POST",
          headers: authHeaders(tenantOverride),
          body: JSON.stringify({
            new_driver_id: newDriverId || null,
            new_driver_name: newDriverName || "",
            new_truck_id: newTruckId || null,
            reason: reassignReason || "",
          }),
        },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        toast.error(j.detail || "Reassign failed.");
        return;
      }
      onChanged && onChanged(j.assignment);
      setReassignOpen(false);
      toast.success("Assignment reassigned.");
    } catch {
      toast.error("Network error reassigning.");
    } finally {
      setBusy(null);
    }
  }, [
    assignment?.id, newDriverId, newDriverName, newTruckId, reassignReason,
    onChanged, tenantOverride,
  ]);

  const revokeSession = useCallback(async (sessionId) => {
    setBusy(`revoke-${sessionId}`);
    try {
      const r = await fetch(
        `${API}/api/dispatch/driver/sessions/${sessionId}/revoke`,
        { method: "POST", headers: authHeaders(tenantOverride), body: "{}" },
      );
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        toast.error(j.detail || "Revoke failed.");
        return;
      }
      setActiveSessions((prev) => prev.filter((s) => s.id !== sessionId));
      toast.success("Driver session revoked.");
    } catch {
      toast.error("Network error revoking session.");
    } finally {
      setBusy(null);
    }
  }, [tenantOverride]);

  const history = useMemo(
    () => Array.isArray(assignment?.state_history) ? [...assignment.state_history].reverse() : [],
    [assignment],
  );

  if (!open) return null;

  return (
    <>
      {/* Scrim */}
      <div
        data-testid="drawer-scrim"
        className="fixed inset-0 bg-slate-950/40 z-40"
        onClick={close}
      />
      {/* Drawer */}
      <aside
        data-testid="assignment-drawer"
        className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-white shadow-2xl z-50 overflow-y-auto"
      >
        <header className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-start justify-between gap-3">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-orange-700 font-bold">
              {t("Assignment")}
            </div>
            <div className="text-lg font-black text-slate-900 mt-1" data-testid="drawer-truck">
              {assignment.truck_id || "—"}
            </div>
            <div className="text-xs text-slate-600">
              {assignment.driver_name || assignment.driver_id || t("No driver")}
            </div>
          </div>
          <button
            type="button"
            data-testid="drawer-close"
            onClick={close}
            className="inline-flex items-center justify-center h-10 w-10 -mr-2 text-slate-500 hover:text-slate-900"
            aria-label={t("Close")}
          >
            <X className="w-5 h-5" />
          </button>
        </header>

        <section className="px-5 py-4 space-y-3">
          {/* TRACK 16.13 · Dispatch Decision Surface · recommendation
              chip + Why drawer. Read-only intelligence — never blocks
              the existing assignment flow. */}
          <DispatchDecisionChip
            carrierId={assignment.carrier_id}
            currentDriverId={assignment.driver_id}
            currentTruckId={assignment.truck_id}
            onSelectRecommendation={(triple) => {
              if (triple?.driver?.driver_id) setNewDriverId(triple.driver.driver_id);
              if (triple?.truck?.truck_id) setNewTruckId(triple.truck.truck_id);
            }}
          />
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <div className="uppercase tracking-widest text-slate-400">{t("Current state")}</div>
              <div className="font-bold text-slate-900 mt-0.5">{assignment.current_state || "—"}</div>
            </div>
            <div>
              <div className="uppercase tracking-widest text-slate-400">{t("Project")}</div>
              <div className="font-bold text-slate-900 mt-0.5 truncate">
                {assignment.project_name || assignment.project_number || "—"}
              </div>
            </div>
            <div>
              <div className="uppercase tracking-widest text-slate-400">{t("Material")}</div>
              <div className="font-medium text-slate-700 mt-0.5">{assignment.material || "—"}</div>
            </div>
            <div>
              <div className="uppercase tracking-widest text-slate-400">{t("Assigned at")}</div>
              <div className="font-medium text-slate-700 mt-0.5">{fmtDt(assignment.assigned_at)}</div>
            </div>
          </div>
          {assignment.current_wait_reason ? (
            <div className="text-xs rounded border border-rose-300 bg-rose-50 text-rose-800 px-3 py-2 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5" />
              Waiting on: <strong>{assignment.current_wait_reason.replace(/_/g, " ")}</strong>
            </div>
          ) : null}
        </section>

        {/* Actions */}
        <section className="px-5 pb-4 space-y-3 border-t border-slate-100 pt-4">
          <h3 className="text-xs uppercase tracking-widest text-slate-500 font-bold">
            Dispatcher actions
          </h3>

          {/* Magic link */}
          <div className="space-y-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start"
              disabled={busy === "magic"}
              onClick={issueMagicLink}
              data-testid="drawer-issue-magic"
            >
              <Link2 className="w-4 h-4 mr-2" />
              Issue driver magic link
            </Button>
            {/* D-2.4 · Resend SMS Link · sends SMS via existing rails.
                Backend regenerates the magic link if expired, otherwise
                reuses the active token. Falls back to copy-link on any
                non-"sent" outcome. */}
            <Button
              variant="default"
              size="sm"
              className="w-full justify-start"
              disabled={busy === "sms"}
              onClick={sendMagicSms}
              data-testid="drawer-text-magic-sms"
            >
              <Send className="w-4 h-4 mr-2" />
              {busy === "sms" ? "Sending…" : "Resend SMS Link"}
            </Button>
            {magic ? (
              <div className="border border-emerald-300 bg-emerald-50 rounded p-2 space-y-1.5" data-testid="drawer-magic-output">
                <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                  Link valid 15 min · single-use
                </div>
                <div className="text-[11px] break-all font-mono text-slate-700 select-all">
                  {magic.public_url}
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-10 text-xs"
                  onClick={copyMagicLink}
                  data-testid="drawer-copy-magic"
                >
                  <Copy className="w-3.5 h-3.5 mr-1" /> Copy
                </Button>
              </div>
            ) : null}
          </div>

          {/* D-1.5 · Revise (mutable fields only) */}
          {!cancelOpen && !reassignOpen ? (
            <div>
              {!reviseOpen ? (
                <Button
                  variant="outline" size="sm" className="w-full justify-start"
                  onClick={() => setReviseOpen(true)}
                  data-testid="drawer-open-revise"
                >
                  <Pencil className="w-4 h-4 mr-2" /> Revise assignment
                </Button>
              ) : (
                <div className="border border-slate-200 rounded p-3 space-y-2">
                  <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Revise · driver will re-acknowledge
                  </div>
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder={`Load site (current: ${assignment.source_location || "—"})`}
                    value={rSource} onChange={(e) => setRSource(e.target.value)}
                    data-testid="revise-source"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder={`Dump / destination (current: ${assignment.destination || "—"})`}
                    value={rDestination} onChange={(e) => setRDestination(e.target.value)}
                    data-testid="revise-destination"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder={`Material (current: ${assignment.material || "—"})`}
                    value={rMaterial} onChange={(e) => setRMaterial(e.target.value)}
                    data-testid="revise-material"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder={`Load count (current: ${assignment.load_count ?? "—"})`}
                    inputMode="numeric"
                    value={rLoadCount} onChange={(e) => setRLoadCount(e.target.value)}
                    data-testid="revise-load-count"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder="Dispatcher note (optional)"
                    value={rNote} onChange={(e) => setRNote(e.target.value)}
                    data-testid="revise-note"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder="Reason for revision (required)"
                    value={rReason} onChange={(e) => setRReason(e.target.value)}
                    data-testid="revise-reason"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm" className="flex-1"
                      disabled={busy === "revise"}
                      onClick={reviseAssignment}
                      data-testid="revise-confirm"
                    >
                      Save revision
                    </Button>
                    <Button
                      size="sm" variant="ghost" className="flex-1"
                      onClick={() => setReviseOpen(false)}
                      data-testid="revise-cancel"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {/* Reassign */}
          {!cancelOpen ? (
            <div>
              {!reassignOpen ? (
                <Button
                  variant="outline" size="sm" className="w-full justify-start"
                  onClick={() => setReassignOpen(true)}
                  data-testid="drawer-open-reassign"
                >
                  <Replace className="w-4 h-4 mr-2" /> Reassign driver / truck
                </Button>
              ) : (
                <div className="border border-slate-200 rounded p-3 space-y-2">
                  <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Reassign
                  </div>
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder="New driver id (optional)"
                    value={newDriverId} onChange={(e) => setNewDriverId(e.target.value)}
                    data-testid="reassign-driver-id"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder="New driver name (optional)"
                    value={newDriverName} onChange={(e) => setNewDriverName(e.target.value)}
                    data-testid="reassign-driver-name"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder="New truck id (optional)"
                    value={newTruckId} onChange={(e) => setNewTruckId(e.target.value)}
                    data-testid="reassign-truck-id"
                  />
                  <input
                    className="w-full text-sm border border-slate-300 rounded px-2 py-1"
                    placeholder="Reason (optional)"
                    value={reassignReason} onChange={(e) => setReassignReason(e.target.value)}
                    data-testid="reassign-reason"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm" className="flex-1"
                      disabled={busy === "reassign"}
                      onClick={reassignAssignment}
                      data-testid="reassign-submit"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Save
                    </Button>
                    <Button
                      size="sm" variant="ghost"
                      onClick={() => setReassignOpen(false)}
                      data-testid="reassign-cancel"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {/* Cancel */}
          {!reassignOpen ? (
            <div>
              {!cancelOpen ? (
                <Button
                  variant="outline" size="sm"
                  className="w-full justify-start text-rose-700 border-rose-200 hover:bg-rose-50"
                  onClick={() => setCancelOpen(true)}
                  data-testid="drawer-open-cancel"
                >
                  <Ban className="w-4 h-4 mr-2" /> Cancel assignment
                </Button>
              ) : (
                <div className="border border-rose-300 rounded p-3 space-y-2 bg-rose-50/30">
                  <div className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Cancel assignment
                  </div>
                  <input
                    className="w-full text-sm border border-rose-300 rounded px-2 py-1 bg-white"
                    placeholder="Reason (required)"
                    value={cancelReason} onChange={(e) => setCancelReason(e.target.value)}
                    data-testid="cancel-reason"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm" variant="destructive" className="flex-1"
                      disabled={busy === "cancel"}
                      onClick={cancelAssignment}
                      data-testid="cancel-submit"
                    >
                      Confirm cancel
                    </Button>
                    <Button
                      size="sm" variant="ghost"
                      onClick={() => setCancelOpen(false)}
                      data-testid="cancel-cancel"
                    >
                      Keep
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </section>

        {/* Active sessions */}
        {activeSessions.length > 0 ? (
          <section className="px-5 pb-4 space-y-2 border-t border-slate-100 pt-4">
            <h3 className="text-xs uppercase tracking-widest text-slate-500 font-bold">
              Active driver sessions
            </h3>
            <ul className="space-y-2">
              {activeSessions.map((s) => (
                <li
                  key={s.id}
                  className="flex items-center justify-between gap-3 bg-slate-50 rounded border border-slate-200 px-3 py-2"
                  data-testid={`drawer-session-${s.id}`}
                >
                  <div className="text-xs">
                    <div className="font-bold text-slate-800 truncate max-w-[200px]">
                      {s.driver_name || s.driver_id}
                    </div>
                    <div className="text-slate-500">
                      issued {fmtDt(s.issued_at)} · expires {fmtDt(s.expires_at)}
                    </div>
                  </div>
                  <Button
                    size="sm" variant="ghost"
                    className="text-rose-700 hover:bg-rose-50"
                    disabled={busy === `revoke-${s.id}`}
                    onClick={() => revokeSession(s.id)}
                    data-testid={`revoke-session-${s.id}`}
                  >
                    <ShieldOff className="w-3.5 h-3.5 mr-1" />
                    Revoke
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* History timeline */}
        <section className="px-5 pb-8 pt-4 border-t border-slate-100">
          <h3 className="text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">
            State history (latest first)
          </h3>
          {history.length === 0 ? (
            <p className="text-sm text-slate-500">No history yet.</p>
          ) : (
            <ol className="space-y-0" data-testid="drawer-history">
              {history.map((entry, idx) => (
                <HistoryEntry
                  key={`${entry.at}-${idx}`}
                  entry={entry}
                  idx={idx}
                  isLatest={idx === 0}
                />
              ))}
            </ol>
          )}
        </section>

        {/* iter431 · Phase 29 · Operational Moments Rail (read-only ·
            merged chronology · lifecycle + recovery + continuity +
            attachments) */}
        <section
          className="border-t border-slate-100"
          data-testid="drawer-moments-section"
        >
          <h3 className="px-5 pt-4 pb-2 text-xs uppercase tracking-widest text-slate-500 font-bold">
            {t("Operational moments")}
          </h3>
          <OperationalMomentsRail
            assignmentId={assignment?.id}
            tenantOverride={tenantOverride}
          />
        </section>

        {/* iter417 · Phase 20.0 · Operational Attachments (load proof) */}
        <section className="px-5 sm:px-6 pb-8" data-testid="drawer-attachments-section">
          <AttachmentStrip assignmentId={assignment?.id} canWrite={true} />
        </section>
      </aside>
    </>
  );
}
