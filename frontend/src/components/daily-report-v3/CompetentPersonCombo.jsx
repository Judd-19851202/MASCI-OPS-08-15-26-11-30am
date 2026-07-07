// TRACK 23.10-E · CompetentPersonCombo
//
// Consumes the Track 23.10-B active Qualifications Engine registry.
// NO manual typing. NO free-text fallback. NO temporary picker.
// Expired · suspended · revoked · pending qualifications never appear.
//
// Props:
//   value: string                   — currently-selected qualification_id
//   onChange({ qualification_id, snapshot }) → void
//   readOnly?: boolean
//   testidPrefix?: string           — default "cp-combo"
//
// Backend:
//   GET /api/employees/qualifications?type=COMPETENT_PERSON&active=true
//   GET /api/hr/qualifications/{id}/snapshot   (called on selection)
import React from "react";
import { AlertTriangle, ShieldCheck, Search } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  try {
    for (const k of ["hr_token", "safety_token", "pm_token", "admin_token", "field_token"]) {
      const v = window.localStorage?.getItem(k);
      if (v) {
        if (k === "hr_token") h["X-HR-Token"] = v;
        if (k === "safety_token") h["X-Safety-Token"] = v;
        if (k === "pm_token") h["X-PM-Token"] = v;
        if (k === "admin_token") h["X-Admin-Token"] = v;
        if (k === "field_token") h["X-Field-Token"] = v;
      }
    }
  } catch (e) { /* ignore */ }
  return h;
}

export default function CompetentPersonCombo({
  value = "",
  onChange,
  readOnly = false,
  testidPrefix = "cp-combo",
}) {
  const [items, setItems] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState(null);
  const [filter, setFilter] = React.useState("");

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true); setErr(null);
    fetch(`${API}/employees/qualifications?type=COMPETENT_PERSON&active=true`, {
      headers: authHeaders(),
    })
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((d) => { if (!cancelled) { setItems(d.items || []); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setErr(String(e)); setLoading(false); } });
    return () => { cancelled = true; };
  }, []);

  const selected = items.find((it) => it.qualification_id === value);

  const filtered = React.useMemo(() => {
    const q = (filter || "").toLowerCase();
    if (!q) return items;
    return items.filter((it) =>
      (it.employee_name || "").toLowerCase().includes(q)
      || (it.employee_id || "").toLowerCase().includes(q)
      || (it.employee_trade || "").toLowerCase().includes(q));
  }, [items, filter]);

  async function pick(qid) {
    const it = items.find((x) => x.qualification_id === qid);
    if (!it) { onChange?.({ qualification_id: "", snapshot: null }); return; }
    try {
      const r = await fetch(`${API}/hr/qualifications/${encodeURIComponent(qid)}/snapshot`, {
        headers: authHeaders(),
      });
      const snap = r.ok ? await r.json() : null;
      onChange?.({ qualification_id: qid, snapshot: snap, row: it });
    } catch {
      onChange?.({ qualification_id: qid, snapshot: null, row: it });
    }
  }

  return (
    <div data-testid={`${testidPrefix}-root`}>
      {readOnly ? (
        <div className="text-sm font-mono px-2 py-1 rounded border border-slate-300 bg-slate-50">
          {selected
            ? `${selected.employee_name} · ${selected.employee_trade}`
            : "— not set —"}
        </div>
      ) : (
        <>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2.5" />
            <input
              type="search"
              placeholder="Search active Competent Persons…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="h-9 w-full pl-7 pr-3 text-sm border-2 border-slate-300 rounded"
              data-testid={`${testidPrefix}-filter`}
              autoComplete="off"
            />
          </div>
          {loading ? (
            <div className="text-xs text-slate-500 mt-2">Loading…</div>
          ) : err ? (
            <div className="text-xs text-rose-700 mt-2 flex items-center gap-1"
                 data-testid={`${testidPrefix}-error`}>
              <AlertTriangle className="w-3.5 h-3.5" /> Could not load registry ({err})
            </div>
          ) : items.length === 0 ? (
            <div className="text-xs text-amber-800 mt-2 p-2 border border-amber-300 rounded bg-amber-50"
                 data-testid={`${testidPrefix}-empty`}>
              No Active Competent Persons in the registry. HR must issue a qualification
              from <strong>/hr/qualifications</strong> before this section can be completed.
            </div>
          ) : (
            <select
              value={value || ""}
              onChange={(e) => pick(e.target.value)}
              className="mt-2 h-9 w-full text-sm border-2 border-slate-300 rounded px-2"
              data-testid={`${testidPrefix}-select`}
            >
              <option value="">— Select Competent Person —</option>
              {filtered.map((it) => (
                <option
                  key={it.qualification_id}
                  value={it.qualification_id}
                  data-testid={`${testidPrefix}-option-${it.qualification_id}`}
                >
                  {it.employee_name} · {it.employee_trade}
                  {it.employee_crew ? ` · ${it.employee_crew}` : ""}
                  {" · exp "}{it.expires_at || "n/a"}
                  {it.warning ? " ⚠" : ""}
                </option>
              ))}
            </select>
          )}
          {selected && (
            <div
              className="mt-2 text-xs p-2 rounded border border-emerald-300 bg-emerald-50 text-emerald-900"
              data-testid={`${testidPrefix}-selected-snapshot`}
            >
              <ShieldCheck className="w-3.5 h-3.5 inline mr-1" />
              <strong>{selected.employee_name}</strong>
              {" · "}{selected.employee_trade}
              {selected.employee_crew ? ` · ${selected.employee_crew}` : ""}
              {" · Qualification "}{selected.qualification_type}
              {" · Status "}{selected.verification_status?.toUpperCase()}
              {" · Expires "}{selected.expires_at || "n/a"}
              {selected.warning ? " · EXPIRES SOON ⚠" : ""}
            </div>
          )}
        </>
      )}
    </div>
  );
}
