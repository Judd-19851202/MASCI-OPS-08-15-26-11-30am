import React, { useCallback, useEffect, useState } from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { usePageTitle } from "@/lib/usePageTitle";
import { operationalError } from "@/lib/errors";

export default function AdminGovernanceListPage({
  title,
  subtitle,
  breadcrumb,
  testidPrefix,
  loader,
  itemKey = "items",
  transform = (data) => data,
}) {
  usePageTitle(`${title} · Admin`);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const raw = await loader();
      setData(transform(raw));
      setError("");
    } catch (e) {
      setError(operationalError(e, `Could not load ${title}.`));
    }
  }, [loader, title, transform]);

  useEffect(() => { load(); }, [load]);

  const items = data?.[itemKey] || [];
  const normalized = Array.isArray(items)
    ? items
    : Object.entries(items).map(([id, value]) => ({ id, ...(typeof value === "object" ? value : { value }) }));

  return (
    <LegacyAdminModernShell title={title} subtitle={subtitle} breadcrumb={breadcrumb} testidPrefix={testidPrefix}>
      {error ? <div className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid={`${testidPrefix}-error`}>{error}</div> : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid={`${testidPrefix}-list`}>
        {normalized.map((item, index) => (
          <div key={item.id || item.email || item.user_id || index} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm" data-testid={`${testidPrefix}-item-${item.id || index}`}>
            <div className="text-sm font-semibold text-slate-950 break-words">{item.label || item.display_name || item.email || item.id || item.name || "Unnamed item"}</div>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-slate-600">{JSON.stringify(item, null, 2)}</pre>
          </div>
        ))}
      </div>
    </LegacyAdminModernShell>
  );
}
