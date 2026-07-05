// PreviewValidationIdentities.jsx — TRACK 22.4b-followup.
//
// Admin-only preview page for minting short-lived role tokens used to
// unblock role-scoped workflow verification. Hard-disabled outside
// preview/staging/dev/test environments (the backend returns 404 when
// disabled — this page mirrors that check and refuses to render).
//
// Doctrine:
//   • Big warning banner. This is NOT a production credential tool.
//   • Every token is short-lived (default 4h, max 24h).
//   • Raw token is shown ONCE at mint time; nowhere else.
//   • Revoke is one click.
//   • Audit log surfaces every action.
import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle, KeyRound, ShieldOff, RefreshCcw, Loader2,
  Copy, X as XIcon,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";

const ROLES = [
  "admin", "pm", "safety", "hr", "shop",
  "dispatch", "driver", "field_leadership",
];

function fmtTime(iso) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString(); } catch { return String(iso); }
}

function fmtRelativeFuture(iso) {
  if (!iso) return "—";
  try {
    const s = Math.floor((new Date(iso).getTime() - Date.now()) / 1000);
    if (s < 0) return "expired";
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.floor(s / 60)}m`;
    return `${Math.floor(s / 3600)}h`;
  } catch { return "—"; }
}

function MintForm({ onMinted }) {
  const [role, setRole] = useState("safety");
  const [purpose, setPurpose] = useState("");
  const [ttl, setTtl] = useState(240);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!purpose.trim()) {
      toast.error("Purpose is required — every token must be traceable.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post(
        "/admin/preview-validation-identities/mint",
        { role, purpose, ttl_minutes: Number(ttl) },
      );
      onMinted(data);
      setPurpose("");
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Mint failed");
    } finally { setBusy(false); }
  };

  return (
    <div data-testid="pvi-mint-form" className="rounded-2xl border border-slate-200 bg-white p-5">
      <h3 className="mb-3 text-sm font-mono uppercase tracking-widest font-bold text-slate-800">
        Mint validation identity
      </h3>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
        <label className="flex flex-col text-xs">
          <span className="mb-1 text-slate-500">Role</span>
          <select
            data-testid="pvi-mint-role"
            className="rounded border border-slate-300 px-2 py-1.5 text-sm"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <label className="flex flex-col text-xs md:col-span-2">
          <span className="mb-1 text-slate-500">Purpose (required · traceable)</span>
          <Input
            data-testid="pvi-mint-purpose"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder="e.g. Track 22.4b-followup-Safety · exercise CAPA lifecycle"
          />
        </label>
        <label className="flex flex-col text-xs">
          <span className="mb-1 text-slate-500">TTL minutes (max 1440)</span>
          <Input
            data-testid="pvi-mint-ttl"
            type="number"
            min="1"
            max="1440"
            value={ttl}
            onChange={(e) => setTtl(e.target.value)}
          />
        </label>
      </div>
      <div className="mt-3 flex justify-end">
        <Button
          data-testid="pvi-mint-submit"
          onClick={submit}
          disabled={busy}
          className="bg-slate-800 text-white hover:bg-slate-900"
        >
          {busy ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <KeyRound className="mr-1 h-3.5 w-3.5" />}
          Mint token
        </Button>
      </div>
    </div>
  );
}

function MintedTokenModal({ minted, onClose }) {
  const copy = () => {
    navigator.clipboard?.writeText(minted.token);
    toast.success("Token copied. Paste into the browser's role token slot.");
  };
  return (
    <div
      data-testid="pvi-minted-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
    >
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl">
        <div className="mb-3 flex items-center gap-2 rounded-md border-2 border-amber-400 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <AlertTriangle className="h-4 w-4" />
          <span>
            <strong>Copy this token now.</strong> It will NEVER be shown again
            after you close this modal. This is a preview validation identity,
            not a production credential.
          </span>
        </div>
        <div className="mb-2 text-xs text-slate-600">
          role: <strong>{minted.role}</strong> · expires: <strong>{fmtTime(minted.expires_at)}</strong> ·
          use as header <code className="rounded bg-slate-100 px-1">{minted.token_header_hint}</code>
        </div>
        <textarea
          data-testid="pvi-minted-token"
          readOnly
          className="w-full rounded border border-slate-300 bg-slate-50 p-3 font-mono text-xs"
          rows={4}
          value={minted.token}
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button data-testid="pvi-minted-copy" variant="outline" onClick={copy}>
            <Copy className="mr-1 h-3.5 w-3.5" /> Copy
          </Button>
          <Button data-testid="pvi-minted-close" onClick={onClose}>
            <XIcon className="mr-1 h-3.5 w-3.5" /> Close
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function PreviewValidationIdentities() {
  const [envStatus, setEnvStatus] = useState(null);
  const [identities, setIdentities] = useState([]);
  const [audit, setAudit] = useState([]);
  const [minted, setMinted] = useState(null);
  const [loading, setLoading] = useState(true);
  const [includeInactive, setIncludeInactive] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [envR, listR, auditR] = await Promise.all([
        api.get("/admin/preview-validation-identities/env"),
        api.get("/admin/preview-validation-identities", { params: { include_inactive: includeInactive } }),
        api.get("/admin/preview-validation-identities/audit", { params: { limit: 50 } }),
      ]);
      setEnvStatus(envR.data);
      setIdentities(listR.data?.identities || []);
      setAudit(auditR.data?.audit || []);
    } catch (e) {
      // If backend returns 404 (not available in this env), reflect honestly.
      const status = e?.response?.status;
      if (status === 404) setEnvStatus({ available: false, is_production: null });
      else toast.error(e?.message || "Failed to load");
    } finally { setLoading(false); }
  }, [includeInactive]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const revoke = async (id) => {
    try {
      await api.post(`/admin/preview-validation-identities/${id}/revoke`);
      toast.success("Validation identity revoked");
      loadAll();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Revoke failed");
    }
  };

  // Preview-only render gate
  if (!loading && envStatus && envStatus.available === false) {
    return (
      <AdminShell>
        <div
          data-testid="pvi-unavailable"
          className="mx-auto max-w-3xl p-6"
        >
          <div className="rounded-md border-2 border-red-300 bg-red-50 p-4 text-sm text-red-900">
            <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest font-bold">
              <ShieldOff className="h-4 w-4" /> Preview validation identities are disabled in this environment
            </div>
            <p className="mt-2">
              This tool is hard-disabled in production and requires an
              explicit <code>ENABLE_PREVIEW_VALIDATION_IDENTITIES=true</code> flag
              in a preview/staging/development/test environment. That is by design.
            </p>
          </div>
        </div>
      </AdminShell>
    );
  }

  return (
    <AdminShell>
      <div
        data-testid="preview-validation-identities-page"
        className="mx-auto max-w-6xl space-y-4 p-6"
      >
        <header className="rounded-2xl border-2 border-red-300 bg-red-50 p-4">
          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest font-bold text-red-900">
            <AlertTriangle className="h-4 w-4" /> Preview validation identities — not production credentials
          </div>
          <p className="mt-2 text-sm text-red-900">
            These identities exist only to verify role-scoped workflows in
            preview. They are not real users, not production credentials, and
            must never be used for live operations. Every mint is audited;
            every token auto-expires; every token can be revoked instantly.
          </p>
          {envStatus ? (
            <div className="mt-2 text-xs text-red-800">
              env: <code>{envStatus.env_marker}</code> · available:{" "}
              <strong>{String(envStatus.available)}</strong> · default TTL{" "}
              {envStatus.default_ttl_minutes}m · max TTL{" "}
              {envStatus.max_ttl_minutes}m
            </div>
          ) : null}
        </header>

        <MintForm onMinted={(m) => { setMinted(m); loadAll(); }} />

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-mono uppercase tracking-widest font-bold text-slate-800">
              Active identities
            </h3>
            <label className="flex items-center gap-2 text-xs text-slate-600">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
                data-testid="pvi-include-inactive"
              />
              include expired/revoked
            </label>
          </div>
          {loading ? (
            <div className="py-6 text-center text-sm text-slate-500">
              <Loader2 className="mx-auto mb-1 h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : identities.length === 0 ? (
            <div className="py-6 text-center text-sm text-slate-500">
              No validation identities.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-3">Role</th>
                    <th className="py-2 pr-3">Purpose</th>
                    <th className="py-2 pr-3">Status</th>
                    <th className="py-2 pr-3">Expires</th>
                    <th className="py-2 pr-3">Track</th>
                    <th className="py-2 pr-3">Created by</th>
                    <th className="py-2 pr-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {identities.map((i) => (
                    <tr key={i.validation_identity_id} className="border-b border-slate-100 last:border-b-0" data-testid={`pvi-row-${i.validation_identity_id}`}>
                      <td className="py-2 pr-3 font-mono text-xs">{i.role}</td>
                      <td className="py-2 pr-3 text-xs text-slate-700">{i.purpose}</td>
                      <td className="py-2 pr-3 text-xs">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider font-bold ${i.status === "active" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
                          {i.status}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-xs text-slate-600">
                        {fmtTime(i.expires_at)}
                        <span className="ml-1 text-slate-400">({fmtRelativeFuture(i.expires_at)})</span>
                      </td>
                      <td className="py-2 pr-3 text-[11px] font-mono text-slate-600">{i.validation_track}</td>
                      <td className="py-2 pr-3 text-xs text-slate-600">{i.created_by_admin_email}</td>
                      <td className="py-2 pr-3 text-right">
                        {i.status === "active" ? (
                          <button
                            data-testid={`pvi-revoke-${i.validation_identity_id}`}
                            onClick={() => revoke(i.validation_identity_id)}
                            className="rounded border border-red-300 px-2 py-1 text-[11px] font-mono uppercase tracking-widest font-bold text-red-700 hover:bg-red-50"
                          >
                            Revoke
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-mono uppercase tracking-widest font-bold text-slate-800">
              Audit log
            </h3>
            <Button size="sm" variant="outline" onClick={loadAll} data-testid="pvi-refresh">
              <RefreshCcw className="mr-1 h-3.5 w-3.5" /> Refresh
            </Button>
          </div>
          {audit.length === 0 ? (
            <div className="py-4 text-center text-xs text-slate-500">
              No audit rows yet.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100 text-xs">
              {audit.map((row, idx) => (
                <li key={idx} className="py-1.5" data-testid={`pvi-audit-${idx}`}>
                  <span className="font-mono text-slate-500">{fmtTime(row.at)}</span>{" · "}
                  <span className="font-mono uppercase text-slate-800">{row.event}</span>{" · "}
                  role <strong>{row.role}</strong>{" · "}
                  by {row.actor_email}
                  {row.purpose ? <span className="text-slate-500"> · {row.purpose}</span> : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        {minted ? <MintedTokenModal minted={minted} onClose={() => setMinted(null)} /> : null}
      </div>
    </AdminShell>
  );
}
