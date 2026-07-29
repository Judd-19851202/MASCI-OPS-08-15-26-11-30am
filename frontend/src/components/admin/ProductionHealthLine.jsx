// ProductionHealthLine.jsx — iter439 · Item I.
//
// Calm read-only one-line indicator of production health for /admin/system.
// Hits the admin-strict /api/admin-strict/diag/production-health endpoint
// and renders ONE of three states:
//
//   ✅ Production probes healthy · 5/5 healthy · 2m ago
//   ❌ Production unreachable · 0/5 healthy · 2m ago
//   ⏳ Checking production…
//
// Doctrine
// --------
// - Admin-only surface (the endpoint itself is admin-strict — caller
//   is already admin-gated by /admin/system).
// - NEVER becomes a dashboard · NEVER lists individual probes by
//   default · the failing endpoint names appear inline only when the
//   pill is red (operational truth, not a graph).
// - Auto-polls every 60s while mounted · NEVER more often.
// - Calm color · no animations · no flashing.

import React, { useEffect, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 60 * 1000;

function _relative(ts, t) {
  if (!ts) return "";
  const secs = Math.max(0, Math.round(Date.now() / 1000 - ts));
  if (secs < 30) return t("just now");
  if (secs < 90) return t("a moment ago");
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins} ${t("min ago")}`;
  return `${Math.round(mins / 60)} ${t("hr ago")}`;
}

export default function ProductionHealthLine({ testId = "production-health-line" }) {
  const { t } = useT();
  const [state, setState] = useState({ status: "loading", data: null });

  const probe = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/admin-strict/diag/production-health`, {
        headers: buildScopedPortalAuthHeaders(["admin"]),
      });
      if (!r.ok) {
        setState({ status: "error", data: { httpCode: r.status } });
        return;
      }
      const body = await r.json();
      setState({ status: "ok", data: body });
    } catch (e) {
      setState({ status: "error", data: { message: e?.message || "network" } });
    }
  }, []);

  useEffect(() => {
    probe();
    const id = setInterval(probe, POLL_MS);
    return () => clearInterval(id);
  }, [probe]);

  if (state.status === "loading") {
    return (
      <div
        data-testid={testId}
        className="flex items-center gap-2 text-xs text-slate-500 italic"
      >
        <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
        <span>{t("Checking production probes…")}</span>
      </div>
    );
  }

  if (state.status === "error" || !state.data?.ok) {
    const total = state.data?.results?.length || 0;
    const healthy = (state.data?.results || []).filter((r) => r.ok).length;
    const failures = (state.data?.results || []).filter((r) => !r.ok);
    return (
      <div
        data-testid={testId}
        className="flex flex-col gap-1"
      >
        <div className="flex items-center gap-2 text-xs text-rose-700">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
          <span className="font-medium">
            {t("Production probes failing")}
            {total > 0 && (
              <span className="text-rose-600 font-normal">
                {" · "}{healthy}/{total} {t("healthy")}{" · "}
                {_relative(state.data?.probed_at, t)}
              </span>
            )}
          </span>
        </div>
        {failures.length > 0 && (
          <ul
            data-testid={`${testId}-failures`}
            className="ml-5 text-[11px] text-rose-600 space-y-0.5"
          >
            {failures.slice(0, 5).map((f) => (
              <li key={f.path}>
                <span className="font-mono">{f.method} {f.path}</span>
                {" · "}
                <span>HTTP {f.http_code || "—"}</span>
                {f.error && <span> · {f.error}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  // ok
  const total = state.data?.results?.length || 0;
  const healthy = (state.data?.results || []).filter((r) => r.ok).length;
  return (
    <div
      data-testid={testId}
      className="flex items-center gap-2 text-xs text-emerald-700"
    >
      <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
      <span className="font-medium">
        {t("Production probes healthy")}
        <span className="text-emerald-600 font-normal">
          {" · "}{healthy}/{total} {t("healthy")}{" · "}
          {_relative(state.data?.probed_at, t)}
        </span>
      </span>
    </div>
  );
}
