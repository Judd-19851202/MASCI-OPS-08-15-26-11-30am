// AdminUnifiedDirectoryPanel.jsx — Phase K4a · Unified Directory (read-only)
//
// Mounts inside /admin → People & Access right beneath the existing
// Access Control Center. Surfaces every row in `user_directory`,
// including the silently mirrored entries created by Phase K1, plus
// the K3 role-template catalog. **Strictly read-only this iteration —
// no portal toggles, no resets, no delete buttons here.** Mutations
// stay in the existing Access Control Center until K4b lands.
//
// Pulls from:
//   GET /api/admin/directory/k4/users         — list + filters
//   GET /api/admin/directory/k4/stats         — header counts
//   GET /api/admin/directory/k4/role-templates — K3 catalog (name lookup)
//
// Visual language matches existing /admin/people panels (Card +
// Lucide icon + slate dense table + mono uppercase column headers).

import React, { useEffect, useMemo, useState } from "react";
import { Database, Loader2, ShieldCheck, Link2, GitBranch, Search } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const PORTAL_COLORS = {
  admin: "bg-red-700 text-white",
  pm: "bg-red-600 text-white",
  shop: "bg-orange-600 text-white",
  hr: "bg-purple-700 text-white",
  safety: "bg-cyan-700 text-white",
  dispatch: "bg-amber-600 text-white",
};

const PORTAL_OPTIONS = ["admin", "pm", "shop", "hr", "safety", "dispatch"];
const SOURCE_OPTIONS = [
  { key: "", label: "All" },
  { key: "managed", label: "Managed" },
  { key: "mirrored", label: "Mirrored" },
];

function PortalChip({ portal }) {
  const cls = PORTAL_COLORS[portal] || "bg-slate-600 text-white";
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${cls}`}
      data-testid={`udp-portal-chip-${portal}`}
    >
      {portal}
    </span>
  );
}

function SourceBadge({ source }) {
  if (source === "mirrored") {
    return (
      <span
        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-slate-200 text-slate-700 border border-slate-300"
        title="Auto-mirrored from a legacy per-portal collection (Phase K1)."
        data-testid="udp-source-mirrored"
      >
        <GitBranch className="w-3 h-3" /> Mirrored
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300"
      title="Master account managed via the Access Control Center."
      data-testid="udp-source-managed"
    >
      <Link2 className="w-3 h-3" /> Managed
    </span>
  );
}

export default function AdminUnifiedDirectoryPanel() {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [portal, setPortal] = useState("");
  const [source, setSource] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      if (portal) params.set("portal", portal);
      if (source) params.set("source", source);
      params.set("limit", "500");
      const [uRes, sRes, tRes] = await Promise.all([
        api.get(`/admin/directory/k4/users?${params.toString()}`),
        api.get("/admin/directory/k4/stats"),
        api.get("/admin/directory/k4/role-templates"),
      ]);
      setUsers(uRes.data?.users || []);
      setStats(sRes.data || null);
      setTemplates(tRes.data?.templates || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to load unified directory");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [portal, source]);

  const templateById = useMemo(() => {
    const m = {};
    for (const t of templates) m[t.id] = t;
    return m;
  }, [templates]);

  return (
    <Card className="p-5 border border-slate-200" data-testid="unified-directory-panel">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3">
          <div className="bg-slate-800 rounded p-2 mt-0.5">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-display text-lg font-black tracking-tight text-slate-900">
              Unified Directory{" "}
              <span className="ml-2 align-middle text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 font-bold">
                Phase K4a · Read-only
              </span>
            </h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Every account that lives in the unified <code className="px-1 bg-slate-100 rounded">user_directory</code>{" "}
              collection — including users silently mirrored from the legacy
              per-portal collections (HR / Shop / PM / Safety / Dispatch) by
              Phase K1. Role-template assignments shown here are non-enforcing;
              they will only gate access after Phase K6 lands.
            </p>
          </div>
        </div>
      </div>

      {/* Stats strip */}
      {stats && (
        <div
          className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 mb-4"
          data-testid="udp-stats-strip"
        >
          <StatTile label="Total" value={stats.total} />
          <StatTile label="Managed" value={stats.managed} />
          <StatTile label="Mirrored" value={stats.mirrored} />
          <StatTile label="Disabled" value={stats.disabled} />
          <StatTile label="With Template" value={stats.with_role_template} />
          {PORTAL_OPTIONS.slice(0, 3).map((p) => (
            <StatTile
              key={p}
              label={p.toUpperCase()}
              value={stats.by_portal?.[p] ?? 0}
            />
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-3" data-testid="udp-filters">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") refresh();
            }}
            placeholder="Search email or name…"
            className="pl-8 h-9 text-sm"
            data-testid="udp-search-input"
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refresh}
          className="h-9 text-xs font-mono uppercase tracking-wider"
          data-testid="udp-search-btn"
        >
          Search
        </Button>
        <div className="flex items-center gap-1 ml-2">
          <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500 font-bold">
            Portal:
          </span>
          <select
            value={portal}
            onChange={(e) => setPortal(e.target.value)}
            className="h-9 border border-slate-300 rounded px-2 text-xs font-mono uppercase tracking-wider bg-white"
            data-testid="udp-portal-filter"
          >
            <option value="">All</option>
            {PORTAL_OPTIONS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500 font-bold">
            Source:
          </span>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="h-9 border border-slate-300 rounded px-2 text-xs font-mono uppercase tracking-wider bg-white"
            data-testid="udp-source-filter"
          >
            {SOURCE_OPTIONS.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div
          className="flex items-center gap-2 text-slate-600 py-6"
          data-testid="udp-loading"
        >
          <Loader2 className="w-4 h-4 animate-spin" /> Loading unified directory…
        </div>
      ) : users.length === 0 ? (
        <div
          className="text-sm text-slate-500 italic py-4"
          data-testid="udp-empty"
        >
          No users match the current filter.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1100px] text-sm" data-testid="udp-table">
            <thead>
              <tr className="border-b border-slate-200 text-left">
                <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  User
                </th>
                <th className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Portals
                </th>
                <th className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Source
                </th>
                <th className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Role Template
                </th>
                <th className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Employee
                </th>
                <th className="py-2 px-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Last sign-in
                </th>
                <th className="py-2 pl-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const tpl = u.role_template_id
                  ? templateById[u.role_template_id]
                  : null;
                return (
                  <tr
                    key={u.id}
                    className={`border-b border-slate-100 ${u.disabled ? "opacity-50" : ""}`}
                    data-testid={`udp-row-${u.email}`}
                  >
                    <td className="py-2 pr-3 align-top">
                      <div className="flex items-start gap-2">
                        {u.is_super_admin && (
                          <ShieldCheck
                            className="w-4 h-4 text-red-700 mt-0.5 shrink-0"
                            title="Super admin"
                          />
                        )}
                        <div className="min-w-0">
                          <div className="font-bold text-slate-900 truncate">
                            {u.name || u.email.split("@")[0]}
                          </div>
                          <div className="text-xs text-slate-500 truncate">
                            {u.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-2 px-2 align-top">
                      <div className="flex flex-wrap gap-1 max-w-[180px]">
                        {(u.portals || []).map((p) => (
                          <PortalChip key={p} portal={p} />
                        ))}
                      </div>
                    </td>
                    <td className="py-2 px-2 align-top">
                      <SourceBadge source={u.source} />
                      {u.source === "mirrored" &&
                        u.mirror_sources &&
                        Object.keys(u.mirror_sources).length > 0 && (
                          <div className="text-[10px] text-slate-400 font-mono mt-1 max-w-[140px] truncate">
                            from: {Object.keys(u.mirror_sources).join(", ")}
                          </div>
                        )}
                    </td>
                    <td className="py-2 px-2 align-top">
                      {tpl ? (
                        <div>
                          <div className="text-xs font-bold text-slate-800">
                            {tpl.name}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {tpl.id}
                          </div>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 italic">
                          —
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-2 align-top">
                      <span className="text-xs font-mono text-slate-600">
                        {u.employee_id || (
                          <span className="text-slate-400">—</span>
                        )}
                      </span>
                    </td>
                    <td className="py-2 px-2 align-top">
                      <span className="text-xs text-slate-600 font-mono">
                        {u.last_login_at
                          ? new Date(u.last_login_at).toLocaleDateString()
                          : "—"}
                      </span>
                    </td>
                    <td className="py-2 pl-3 align-top">
                      {u.disabled ? (
                        <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-rose-100 text-rose-700 border border-rose-300">
                          Disabled
                        </span>
                      ) : (
                        <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-100 text-emerald-700 border border-emerald-300">
                          Active
                        </span>
                      )}
                      {u.must_change_password && (
                        <div className="text-[10px] text-amber-700 font-mono mt-0.5">
                          must rotate pw
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 text-[10px] text-slate-400 font-mono leading-relaxed border-t border-slate-100 pt-3">
        Phase K4a · Read-only surface. Role-template assignment, "convert
        mirrored → managed", and per-user audit views land in Phase K4b
        following user approval. Mutations to existing accounts continue to
        live in the Access Control Center above.
      </div>
    </Card>
  );
}

function StatTile({ label, value }) {
  return (
    <div
      className="border border-slate-200 rounded px-2 py-1.5 bg-slate-50"
      data-testid={`udp-stat-${label.toLowerCase().replace(/\s+/g, "-")}`}
    >
      <div className="text-[9px] font-mono uppercase tracking-[0.18em] text-slate-500 font-bold leading-tight">
        {label}
      </div>
      <div className="text-lg font-black text-slate-900 leading-tight">
        {value ?? 0}
      </div>
    </div>
  );
}
