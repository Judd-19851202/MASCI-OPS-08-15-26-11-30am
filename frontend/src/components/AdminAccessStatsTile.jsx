// AdminAccessStatsTile.jsx — iter346-A
//
// Small, calm, admin-only quick-stats tile that gives operators a single
// glanceable view of master-directory access posture:
//   • total users
//   • total portal grants
//   • cross-portal users (≥ 2 portals)
//   • disabled users
//
// Reads the existing `/api/admin/directory` endpoint (no new backend
// route). Matches the iter338 widget calm rhythm — slate-700 stripe,
// mono numerals, uppercase tracking kicker, single white card.
//
// Mounted at the top of /admin/people, above AdminAccessControlPanel.
import React, { useEffect, useState } from "react";
import { Users, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";

function StatNumber({ value, label, testid }) {
  return (
    <div className="flex flex-col" data-testid={testid}>
      <div className="font-mono text-2xl font-black text-slate-900 leading-none">
        {value === null || value === undefined ? "—" : value}
      </div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mt-1.5">
        {label}
      </div>
    </div>
  );
}

export default function AdminAccessStatsTile() {
  const { t } = useT();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.get("/admin/directory");
      const users = Array.isArray(r.data?.users) ? r.data.users : [];
      let totalUsers = 0;
      let totalGrants = 0;
      let crossPortal = 0;
      let disabled = 0;
      for (const u of users) {
        totalUsers += 1;
        const portals = Array.isArray(u?.portals) ? u.portals : [];
        totalGrants += portals.length;
        if (portals.length >= 2) crossPortal += 1;
        if (u?.disabled) disabled += 1;
      }
      setStats({ totalUsers, totalGrants, crossPortal, disabled });
    } catch (e) {
      setError(operationalError(e, t("Access stats temporarily unavailable.")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className="bg-white border border-slate-200 rounded-md border-l-4 border-l-slate-700 p-5"
      data-testid="admin-access-stats-tile"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-500" />
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
            {t("Access Control · Quick Stats")}
          </div>
        </div>
        {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
      </div>
      {error ? (
        <div
          className="font-mono text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded px-3 py-2"
          data-testid="admin-access-stats-error"
        >
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatNumber
            value={stats?.totalUsers}
            label={t("Total Users")}
            testid="admin-access-stat-total"
          />
          <StatNumber
            value={stats?.totalGrants}
            label={t("Total Grants")}
            testid="admin-access-stat-grants"
          />
          <StatNumber
            value={stats?.crossPortal}
            label={t("Cross-Portal")}
            testid="admin-access-stat-crossportal"
          />
          <StatNumber
            value={stats?.disabled}
            label={t("Disabled")}
            testid="admin-access-stat-disabled"
          />
        </div>
      )}
    </div>
  );
}
