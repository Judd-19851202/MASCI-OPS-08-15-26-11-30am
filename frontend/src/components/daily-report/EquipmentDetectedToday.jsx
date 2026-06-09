// M-DR-1 · Equipment Auto-Discovery — "Equipment Detected Today" pane.
//
// Visibility + verification ONLY. Motive suggests; foreman verifies;
// foreman authors. This component never mutates a Daily Report without
// the foreman tapping Accept. Foreman taps:
//   • Accept → row is appended to the form's equipment[] array
//   • Remove → row hides locally (no DB write)
//   • Ignore → row stays visible, marked Ignored
//
// All decision state is ephemeral (component-local). On reload of the
// form, fresh suggestions are computed server-side.
import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2, XCircle, EyeOff, Radar, Loader2, MapPin, Info,
} from "lucide-react";
import { toast } from "sonner";

const BAND = {
  HIGH:   { label: "HIGH",   bg: "bg-emerald-50",  border: "border-emerald-400", text: "text-emerald-900" },
  MEDIUM: { label: "MEDIUM", bg: "bg-amber-50",    border: "border-amber-400",   text: "text-amber-900" },
};

/**
 * Props:
 *   projectNumber : string
 *   date          : string (YYYY-MM-DD)
 *   onAccept(detection): the parent inserts a row into data.equipment.
 *                        Component does NOT touch the form directly.
 */
export default function EquipmentDetectedToday({ projectNumber, date, onAccept }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detections, setDetections] = useState([]);
  const [reason, setReason] = useState(null);
  const [decisions, setDecisions] = useState({}); // detection_key → 'accept'|'remove'|'ignore'
  const [diagnostics, setDiagnostics] = useState({});

  useEffect(() => {
    let cancelled = false;
    if (!projectNumber || !date) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await api.get(`/equipment-detection/${encodeURIComponent(projectNumber)}/${encodeURIComponent(date)}`);
        if (cancelled) return;
        setDetections(r.data.detections || []);
        setReason(r.data.no_detection_reason || null);
        setDiagnostics({
          verified_geofences: r.data.verified_geofences,
          events_considered: r.data.events_considered,
        });
      } catch (e) {
        if (!cancelled) setError(e?.response?.data?.detail || e.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [projectNumber, date]);

  const visible = useMemo(
    () => detections.filter((d) => decisions[d.detection_key] !== "remove"),
    [detections, decisions],
  );

  const counts = useMemo(() => {
    const c = { high: 0, medium: 0, accepted: 0, ignored: 0, removed: 0 };
    for (const d of detections) {
      if (d.confidence === "HIGH") c.high += 1;
      if (d.confidence === "MEDIUM") c.medium += 1;
      const dec = decisions[d.detection_key];
      if (dec === "accept") c.accepted += 1;
      if (dec === "ignore") c.ignored += 1;
      if (dec === "remove") c.removed += 1;
    }
    return c;
  }, [detections, decisions]);

  const handleAccept = (d) => {
    if (decisions[d.detection_key] === "accept") return;
    onAccept?.({
      description: d.label,
      hours_used: "",
      time_delivered: d.first_seen || "",
      time_removed: d.last_seen || "",
      notes: `Detected by Motive · ${d.confidence} · ${d.dwell_minutes} min on site${d.geofence ? ` · geofence: ${d.geofence.name}` : ""}`,
    });
    setDecisions((p) => ({ ...p, [d.detection_key]: "accept" }));
    toast.success(`Added: ${d.label}`);
  };

  const handleRemove = (d) => {
    setDecisions((p) => ({ ...p, [d.detection_key]: "remove" }));
  };

  const handleIgnore = (d) => {
    setDecisions((p) => ({ ...p, [d.detection_key]: "ignore" }));
  };

  // Nothing to show? Render a quiet hint.
  if (!projectNumber) return null;

  return (
    <div
      className="rounded border-2 border-slate-300 bg-white p-3 mb-3"
      data-testid="equipment-detected-today"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <Radar className="w-4 h-4 text-slate-600" />
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
              Equipment Detected Today
            </div>
            <div className="text-xs text-slate-600 mt-0.5">
              Detected by Motive · You confirm what was on site
            </div>
          </div>
        </div>
        {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
      </div>

      {error && (
        <div className="text-xs text-amber-800 bg-amber-50 border border-amber-300 rounded px-2 py-1.5 mb-2" data-testid="equipment-detected-error">
          Suggestion service unavailable: {error}. You can keep entering equipment manually.
        </div>
      )}

      {!loading && !error && detections.length === 0 && (
        <div className="text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded px-2 py-2 flex items-start gap-2" data-testid="equipment-detected-empty">
          <Info className="w-3.5 h-3.5 mt-0.5 text-slate-400" />
          <div>
            {reason === "no_verified_geofence"
              ? "No Motive geofence linked to this project. Admin → Geofence Reconciliation."
              : reason === "no_motive_geofence_id_linked"
                ? "Project linked, but the geofence record is missing a Motive id."
                : "No equipment detected by Motive on this date."}
          </div>
        </div>
      )}

      {!loading && visible.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2" data-testid="equipment-detected-counts">
            <MiniStat label="High"    value={counts.high}     tone="emerald" />
            <MiniStat label="Medium"  value={counts.medium}   tone="amber" />
            <MiniStat label="Accepted" value={counts.accepted} tone="slate" />
            <MiniStat label="Ignored" value={counts.ignored}  tone="slate" />
          </div>
          <div className="space-y-1.5">
            {visible.map((d) => {
              const dec = decisions[d.detection_key];
              const band = BAND[d.confidence] || BAND.MEDIUM;
              const ignored = dec === "ignore";
              const accepted = dec === "accept";
              return (
                <div
                  key={d.detection_key}
                  className={`rounded border ${band.border} ${ignored ? "opacity-50" : ""} flex items-center justify-between gap-2 p-2`}
                  data-testid={`equipment-detected-row-${d.detection_key.replace(":", "-")}`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-1.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wider ${band.bg} ${band.text}`}>
                        {band.label}
                      </span>
                      <span className="font-bold text-slate-900 truncate">{d.label}</span>
                      {accepted && (
                        <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 font-mono text-[10px] font-bold uppercase">
                          Added to report
                        </span>
                      )}
                      {ignored && (
                        <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-mono text-[10px] font-bold uppercase">
                          Ignored
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-600 font-mono mt-0.5 flex flex-wrap gap-2">
                      <span>{d.first_seen || "—"} → {d.last_seen || "—"}</span>
                      <span>·</span>
                      <span>{d.dwell_minutes} min on site</span>
                      {d.geofence?.name && (
                        <>
                          <span>·</span>
                          <span className="flex items-center gap-0.5"><MapPin className="w-3 h-3" />{d.geofence.name}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      size="sm"
                      onClick={() => handleAccept(d)}
                      disabled={accepted}
                      className="h-7 bg-emerald-700 hover:bg-emerald-800 text-white text-xs"
                      data-testid={`equipment-detected-accept-${d.detection_key.replace(":", "-")}`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-0.5" />
                      Accept
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRemove(d)}
                      className="h-7 border-2 border-red-300 text-red-700 hover:bg-red-50 text-xs"
                      data-testid={`equipment-detected-remove-${d.detection_key.replace(":", "-")}`}
                    >
                      <XCircle className="w-3.5 h-3.5 mr-0.5" />
                      Remove
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleIgnore(d)}
                      disabled={ignored}
                      className="h-7 border-2 text-xs"
                      data-testid={`equipment-detected-ignore-${d.detection_key.replace(":", "-")}`}
                    >
                      <EyeOff className="w-3.5 h-3.5 mr-0.5" />
                      Ignore
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
          {(diagnostics.verified_geofences != null || diagnostics.events_considered != null) && (
            <div
              className="text-[10px] font-mono text-slate-400 mt-2"
              data-testid="equipment-detected-diagnostics"
            >
              {diagnostics.verified_geofences ?? "?"} verified geofence(s) · {diagnostics.events_considered ?? "?"} events considered
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MiniStat({ label, value, tone }) {
  const tones = {
    emerald: "bg-emerald-50 text-emerald-900 border border-emerald-300",
    amber:   "bg-amber-50 text-amber-900 border border-amber-300",
    slate:   "bg-slate-50 text-slate-700 border border-slate-200",
  };
  return (
    <div className={`px-2 py-1 rounded ${tones[tone] || tones.slate}`}>
      <div className="font-mono text-[10px] uppercase tracking-wider opacity-80">{label}</div>
      <div className="text-lg font-black leading-none">{value}</div>
    </div>
  );
}
