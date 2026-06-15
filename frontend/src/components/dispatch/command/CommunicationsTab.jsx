/**
 * CommunicationsTab.jsx · Broadcast history + send form.
 *
 * Phase 3.2 — Comms handoff completion. The SendForm now reliably
 * pre-fills audience + message when a cross-tab `contact_driver` action
 * arrives. Approach:
 *
 *   1. Every publish gets a unique `id`.
 *   2. CommunicationsTab subscribes + holds the latest action in state.
 *   3. SendForm is REMOUNTED via React `key={preset?.id || "empty"}` so
 *      its useState initializers run fresh with the new preset — this
 *      bypasses the Radix-Tabs-lazy-mount × StrictMode timing problem.
 *   4. A useRef guard prevents the same `id` from being applied twice.
 *   5. `clearPendingCommandAction()` runs after the SendForm applies the
 *      preset (so a page refresh doesn't re-prefill the same action).
 *   6. Form is fully editable after pre-fill; Send still stub-safe when
 *      provider is absent.
 */
import React, { useEffect, useState, useCallback, useRef } from "react";
import { Send, MessageSquare, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { commandApi } from "./commandApi";
import {
  consumePendingCommandAction,
  clearPendingCommandAction,
  subscribeCommandAction,
} from "./commandActions";
import { BoardShell, StatusChip } from "./BoardShell";
import { formatEmployeeIdentity } from "@/lib/identity";

const POLL_MS = 60000;

function fmtAgo(iso) {
  if (!iso) return "—";
  try {
    const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
    if (m < 1) return "now";
    if (m < 60) return `${m}m`;
    if (m < 1440) return `${Math.floor(m / 60)}h`;
    return `${Math.floor(m / 1440)}d`;
  } catch { return "—"; }
}

function _audienceFromPreset(presetAudience) {
  if (!presetAudience) return { sel: "all_active", text: "" };
  if (presetAudience.startsWith("project:")) {
    return { sel: "project", text: presetAudience.slice("project:".length) };
  }
  if (presetAudience.startsWith("drivers:")) {
    return { sel: "drivers", text: presetAudience.slice("drivers:".length) };
  }
  return { sel: "all_active", text: "" };
}

function SendForm({ provider, onSent, preset, onPresetApplied }) {
  // useState INITIALIZERS run when this component mounts. Because the
  // parent re-keys SendForm whenever `preset?.id` changes, this is the
  // canonical place to apply the preset — no useEffect race with Radix
  // lazy mount / React StrictMode double-mount.
  const init = _audienceFromPreset(preset?.audience);
  const [audience, setAudience] = useState(init.sel);
  const [audienceText, setAudienceText] = useState(init.text);
  const [kind, setKind] = useState(
    preset?.kind && preset.kind !== "contact_driver" ? preset.kind : "general"
  );
  const [message, setMessage] = useState(preset?.suggested_message || "");
  const [sending, setSending] = useState(false);

  // Tell the parent the preset is consumed (clears sessionStorage so a
  // refresh doesn't re-prefill the same context).
  const appliedRef = useRef(null);
  useEffect(() => {
    if (preset?.id && appliedRef.current !== preset.id) {
      appliedRef.current = preset.id;
      onPresetApplied && onPresetApplied(preset.id);
    }
  }, [preset?.id, onPresetApplied]);

  const onSend = async () => {
    if (!message.trim()) {
      toast.error("Message is required");
      return;
    }
    let aud = audience;
    if (audience === "project" && audienceText.trim()) {
      aud = `project:${audienceText.trim()}`;
    } else if (audience === "drivers" && audienceText.trim()) {
      aud = `drivers:${audienceText.trim().replace(/\s+/g, "")}`;
    } else if (audience !== "all_active") {
      toast.error("Audience target is required");
      return;
    }
    setSending(true);
    try {
      const res = await commandApi.sendBroadcast({
        audience: aud, message: message.trim(), kind,
      });
      const label = res.provider_status === "active"
        ? `Sent: ${res.sent}/${res.recipient_count}`
        : `Provider not configured · ${res.recipient_count} recipient(s) audited only`;
      toast.success(`Broadcast ${res.broadcast_id?.slice(0, 8)} · ${label}`);
      setMessage("");
      onSent && onSent();
    } catch (e) {
      toast.error(`Broadcast failed: ${e.message || e}`);
    } finally { setSending(false); }
  };

  return (
    <div
      className="bg-slate-50 border border-slate-200 rounded p-3 space-y-3"
      data-testid="broadcast-form"
    >
      <div className="flex items-center justify-between">
        <div className="font-display text-sm font-black text-slate-900 flex items-center gap-1.5">
          <Send className="w-4 h-4" /> Broadcast SMS
        </div>
        <StatusChip tone={provider?.status === "active" ? "active" : "pending"}>
          {provider?.status === "active" ? "Provider Active" : "Provider Not Configured"}
        </StatusChip>
      </div>

      {preset?.driver_name ? (
        <div
          data-testid="broadcast-preset-summary"
          className="bg-sky-50 border border-sky-200 text-sky-900 rounded px-2.5 py-1.5 text-xs flex items-center justify-between"
        >
          <span>
            Pre-filled from <b>Contact →</b> on <b>{formatEmployeeIdentity(preset) || preset.driver_name}</b>
            {preset.truck_id ? <> · truck <span className="font-mono">{preset.truck_id}</span></> : null}
            {preset.project_number && preset.project_number !== "no_job"
              ? <> · job <span className="font-mono">{preset.project_number}</span></> : null}
          </span>
        </div>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div>
          <label className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Audience</label>
          <select
            value={audience} onChange={(e) => setAudience(e.target.value)}
            data-testid="broadcast-audience-select"
            className="w-full mt-0.5 border border-slate-300 rounded px-2 py-1.5 text-sm"
          >
            <option value="all_active">All active drivers</option>
            <option value="project">Specific project</option>
            <option value="drivers">Specific driver IDs (csv)</option>
          </select>
        </div>
        {audience !== "all_active" ? (
          <div>
            <label className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
              {audience === "project" ? "Project Number" : "Driver IDs (csv)"}
            </label>
            <input
              type="text"
              value={audienceText}
              onChange={(e) => setAudienceText(e.target.value)}
              data-testid="broadcast-audience-text"
              className="w-full mt-0.5 border border-slate-300 rounded px-2 py-1.5 text-sm"
              placeholder={audience === "project" ? "25-21" : "id1,id2,id3"}
            />
          </div>
        ) : <div />}
        <div>
          <label className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Kind</label>
          <select
            value={kind} onChange={(e) => setKind(e.target.value)}
            data-testid="broadcast-kind-select"
            className="w-full mt-0.5 border border-slate-300 rounded px-2 py-1.5 text-sm"
          >
            <option value="general">General</option>
            <option value="safety_alert">Safety Alert</option>
            <option value="road_closure">Road Closure</option>
          </select>
        </div>
      </div>

      <div>
        <label className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Message · {message.length}/280</label>
        <textarea
          value={message}
          maxLength={280}
          onChange={(e) => setMessage(e.target.value)}
          rows={3}
          data-testid="broadcast-message"
          className="w-full mt-0.5 border border-slate-300 rounded px-2 py-1.5 text-sm resize-y"
          placeholder="Type the broadcast message (≤280 chars)…"
        />
      </div>

      <Button
        onClick={onSend}
        disabled={sending || !message.trim()}
        data-testid="broadcast-send"
        className="bg-slate-900 hover:bg-slate-800 text-white"
      >
        {sending ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : <Send className="w-4 h-4 mr-1.5" />}
        Send Broadcast
      </Button>
    </div>
  );
}

export default function CommunicationsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Pull any pending action from sessionStorage on first mount so the
  // SendForm initial useState gets the preset. We do NOT clear it here
  // — clearing happens in onPresetApplied so React StrictMode's
  // double-mount cannot consume the action before the visible mount.
  const [preset, setPreset] = useState(() => consumePendingCommandAction());

  const load = useCallback(async () => {
    try {
      setRefreshing(true);
      const d = await commandApi.broadcasts(50);
      setData(d); setError(null);
    } catch (e) { setError(e.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  // Subscribe to LIVE contact_driver events (e.g. operator stays on the
  // Comms tab and clicks Contact on another driver).
  useEffect(() => {
    const unsub = subscribeCommandAction((a) => {
      if (a && a.kind === "contact_driver") setPreset(a);
    });
    return unsub;
  }, []);

  // Called by SendForm once it has applied the preset — clear the
  // sessionStorage slot so a page refresh doesn't re-apply the same
  // context (a stale broadcast is worse than no pre-fill).
  const onPresetApplied = useCallback((_id) => {
    clearPendingCommandAction();
  }, []);

  const rows = data?.rows || [];
  const provider = data?.provider;

  return (
    <BoardShell
      testId="communications-tab"
      title="Communications"
      subtitle={data?.as_of ? `as of ${fmtAgo(data.as_of)} ago` : ""}
      count={rows.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={false}
    >
      <SendForm
        key={preset?.id || "default"}
        provider={provider}
        onSent={load}
        preset={preset}
        onPresetApplied={onPresetApplied}
      />

      <div className="mt-4">
        <h3 className="font-display text-sm font-black text-slate-900 mb-2 flex items-center gap-1.5">
          <MessageSquare className="w-4 h-4" /> History
        </h3>
        <div className="overflow-x-auto -mx-3 sm:-mx-4">
          <div className="min-w-[700px] max-h-[45vh] overflow-y-auto" data-testid="broadcast-history-list">
            <table className="w-full text-xs sm:text-sm">
              <thead className="sticky top-0 bg-slate-50 z-10 border-b border-slate-200">
                <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-slate-600">
                  <th className="px-3 py-2">When</th>
                  <th className="px-2 py-2">Kind</th>
                  <th className="px-2 py-2">Audience</th>
                  <th className="px-2 py-2">Message</th>
                  <th className="px-2 py-2 text-right">Recipients</th>
                  <th className="px-2 py-2 text-right">Sent</th>
                  <th className="px-2 py-2 text-right">Skipped</th>
                  <th className="px-2 py-2 text-right">Failed</th>
                  <th className="px-2 py-2">Provider</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-3 py-6 text-center text-slate-500 text-sm">
                      No broadcasts yet.
                    </td>
                  </tr>
                ) : rows.map((r) => (
                  <tr
                    key={r.id}
                    data-testid={`broadcast-row-${r.id}`}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="px-3 py-2 text-slate-700">{fmtAgo(r.issued_at)}</td>
                    <td className="px-2 py-2 text-[10px] uppercase tracking-widest text-slate-700">{r.kind || "general"}</td>
                    <td className="px-2 py-2 text-slate-700 truncate max-w-[120px]" title={r.audience}>{r.audience}</td>
                    <td className="px-2 py-2 text-slate-700 truncate max-w-[260px]" title={r.message}>{r.message}</td>
                    <td className="px-2 py-2 text-right font-mono">{r.recipient_count}</td>
                    <td className="px-2 py-2 text-right font-mono text-emerald-700">{r.sent}</td>
                    <td className="px-2 py-2 text-right font-mono text-slate-600">{r.skipped}</td>
                    <td className="px-2 py-2 text-right font-mono text-rose-700">{r.failed}</td>
                    <td className="px-2 py-2">
                      <StatusChip tone={r.provider_status === "active" ? "active" : "pending"}>
                        {r.provider_status === "active" ? "Active" : "Not Configured"}
                      </StatusChip>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </BoardShell>
  );
}
