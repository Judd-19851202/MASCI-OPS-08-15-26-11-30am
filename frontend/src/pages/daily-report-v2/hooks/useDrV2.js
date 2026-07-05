/*
 * DR-ROI-001 · Phase C · React hooks for V2 AI + autosave.
 *
 * useDrV2Draft:       debounced autosave of the supervisor draft
 *                     (returns { reportId, evidenceHash, savedAt, saving })
 * useDrV2Ai:          debounced multi-agent synthesis; consumes reportId +
 *                     structured draft and returns cached AI outputs.
 * useDrV2Approvals:   supervisor approval helpers + audit log fetcher.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  saveDrV2Draft,
  synthesizeDrV2Ai,
  approveDrV2Ai,
  auditDrV2Ai,
  fetchDrV2Meta,
} from "@/lib/drV2Api";

/** Deep, sort-stable JSON stringify for change detection. */
function stableJson(obj) {
  const seen = new WeakSet();
  return JSON.stringify(obj, (_k, v) => {
    if (v && typeof v === "object" && !Array.isArray(v)) {
      if (seen.has(v)) return undefined;
      seen.add(v);
      const out = {};
      Object.keys(v).sort().forEach((k) => (out[k] = v[k]));
      return out;
    }
    return v;
  });
}

/** Autosave the V2 draft to /api/dr-v2/drafts with a debounce. */
export function useDrV2Draft(draft, { debounceMs = 900 } = {}) {
  const [reportId, setReportId] = useState(null);
  const [evidenceHash, setEvidenceHash] = useState(null);
  const [savedAt, setSavedAt] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const timer = useRef(null);
  const lastSig = useRef(null);

  useEffect(() => {
    const sig = stableJson(draft || {});
    if (sig === lastSig.current) return;
    lastSig.current = sig;

    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      try {
        setSaving(true);
        setError(null);
        const payload = { ...draft };
        if (reportId) payload.report_id = reportId;
        const data = await saveDrV2Draft(payload);
        setReportId(data.report_id);
        setEvidenceHash(data.evidence_hash);
        setSavedAt(data.saved_at);
      } catch (e) {
        setError(e?.message || "save failed");
      } finally {
        setSaving(false);
      }
    }, debounceMs);

    return () => timer.current && clearTimeout(timer.current);
  }, [draft, reportId, debounceMs]);

  return { reportId, evidenceHash, savedAt, saving, error };
}

/** Debounced synthesis: fires when reportId or evidence_hash changes. */
export function useDrV2Ai(reportId, evidenceHash, { debounceMs = 1500 } = {}) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [meta, setMeta] = useState(null);
  const timer = useRef(null);

  // Load provider meta once.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const m = await fetchDrV2Meta();
        if (alive) setMeta(m);
      } catch (e) {
        if (alive) setError(e?.message || "meta load failed");
      }
    })();
    return () => { alive = false; };
  }, []);

  const run = useCallback(async (opts = {}) => {
    if (!reportId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await synthesizeDrV2Ai({ report_id: reportId, force: !!opts.force });
      setResult(data);
    } catch (e) {
      setError(e?.message || "synthesis failed");
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    if (!reportId || !evidenceHash) return;
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { run(); }, debounceMs);
    return () => timer.current && clearTimeout(timer.current);
  }, [reportId, evidenceHash, debounceMs, run]);

  return { meta, result, loading, error, regenerate: () => run({ force: true }) };
}

/** Approval + audit helpers. */
export function useDrV2Approvals(reportId) {
  const [audit, setAudit] = useState({ log: [], last_action: null });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!reportId) return;
    try {
      const data = await auditDrV2Ai(reportId);
      setAudit(data);
    } catch (e) {
      setError(e?.message || "audit load failed");
    }
  }, [reportId]);

  useEffect(() => { refresh(); }, [refresh]);

  const submit = useCallback(async (action, extras = {}) => {
    if (!reportId) return null;
    try {
      setBusy(true);
      setError(null);
      const data = await approveDrV2Ai({ report_id: reportId, action, ...extras });
      setAudit(data.state);
      return data;
    } catch (e) {
      setError(e?.message || "approval failed");
      return null;
    } finally {
      setBusy(false);
    }
  }, [reportId]);

  return { audit, busy, error, submit, refresh };
}
