import React, { useCallback, useEffect, useState } from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { usePageTitle } from "@/lib/usePageTitle";
import { operationalError } from "@/lib/errors";
import { fetchGovernanceRegistry } from "@/lib/enterpriseGovernanceApi";

export default function AdminGovernanceRegistryPage() {
  usePageTitle("Governance Registry · Admin");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setData(await fetchGovernanceRegistry());
      setError("");
    } catch (e) {
      setError(operationalError(e, "Could not load governance registry."));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <LegacyAdminModernShell title="Governance Registry" subtitle="Canonical enterprise governance artifacts." breadcrumb={[{ label: "Enterprise Governance", to: "/admin/governance" }, { label: "Registry" }]} testidPrefix="admin-governance-registry">
      {error ? <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid="gov-registry-error">{error}</div> : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {[
          ["constitutional_principles", data?.constitutional_principles || []],
          ["roles", Object.keys(data?.roles || {})],
          ["permissions", Object.keys(data?.permissions || {})],
          ["policies", Object.keys(data?.policies || {})],
          ["approval_flows", Object.keys(data?.approval_flows || {})],
          ["separation_rules", Object.keys(data?.separation_rules || {})],
        ].map(([label, items]) => (
          <div key={label} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm" data-testid={`gov-registry-${label}`}>
            <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{label}</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {items.map((item) => <div key={item} className="rounded-xl bg-slate-50 px-3 py-2 break-words">{item}</div>)}
            </div>
          </div>
        ))}
      </div>
    </LegacyAdminModernShell>
  );
}
