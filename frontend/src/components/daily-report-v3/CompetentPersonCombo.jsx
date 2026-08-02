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
import { useT } from "@/lib/i18n";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  try {
    const map = {
      "masci.hr.token": "X-HR-Token",
      "masci.safety.token": "X-Safety-Token",
      "masci.pm.token": "X-PM-Token",
      "masci.admin.token": "X-Admin-Token",
      "masci.fl.token": "X-FL-Token",
    };
    for (const [key, header] of Object.entries(map)) {
      const v =
        window.localStorage?.getItem(key) ||
        window.sessionStorage?.getItem(key);
      if (v) h[header] = v;
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
  const { t } = useT();
  const [items, setItems] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState(null);
  const [filter, setFilter] = React.useState("");

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true); setErr(null);
    // TRACK 24.9 · Public DR V3 (`/daily/new`) has no portal token.
    // Try the authenticated endpoint first (richer projection for
    // authed users) and fall back to the public-safe projection on
    // 401 so anonymous foremen can still complete the excavation
    // section.
    const authed = `${API}/employees/qualifications?type=COMPETENT_PERSON&active=true`;
    const publicUrl = `${API}/employees/competent-persons/public`;
    const headers = authHeaders();
    const useAuthed = Object.keys(headers).length > 0;
    fetch(useAuthed ? authed : publicUrl, useAuthed ? { headers } : undefined)
      .then((r) => {
        if (r.ok) return r.json();
        if (useAuthed && r.status === 401) {
          return fetch(publicUrl).then((r2) =>
            r2.ok ? r2.json() : Promise.reject(r2.status),
          );
        }
        return Promise.reject(r.status);
      })
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
    const headers = authHeaders();
    if (Object.keys(headers).length === 0) {
      onChange?.({ qualification_id: qid, snapshot: null, row: it });
      return;
    }
    try {
      const r = await fetch(`${API}/hr/qualifications/${encodeURIComponent(qid)}/snapshot`, {
        headers,
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
            : t("— not set —")}
        </div>
      ) : (
        <>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2.5" />
            <input
              type="search"
              placeholder={t("Search active Competent Persons…")}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="h-9 w-full pl-7 pr-3 text-sm border-2 border-slate-300 rounded"
              data-testid={`${testidPrefix}-filter`}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          {loading ? (
            <div className="text-xs text-slate-500 mt-2">{t("Loading…")}</div>
          ) : err ? (
            <div className="text-xs text-rose-700 mt-2 flex items-center gap-1"
                 data-testid={`${testidPrefix}-error`}>
              <AlertTriangle className="w-3.5 h-3.5" /> {t("Could not load registry")} ({err})
            </div>
          ) : items.length === 0 ? (
            <div className="text-xs text-amber-800 mt-2 p-2 border border-amber-300 rounded bg-amber-50"
                 data-testid={`${testidPrefix}-empty`}>
              {t("No Active Competent Persons in the registry. HR must issue a qualification from")}{" "}
              <strong>/hr/qualifications</strong> {t("before this section can be completed.")}
            </div>
          ) : (
            <select
              value={value || ""}
              onChange={(e) => pick(e.target.value)}
              className="wp17-native-select mt-2"
              data-testid={`${testidPrefix}-select`}
            >
              <option value="">{t("— Select Competent Person —")}</option>
              {filtered.map((it) => (
                <option
                  key={it.qualification_id}
                  value={it.qualification_id}
                  data-testid={`${testidPrefix}-option-${it.qualification_id}`}
                >
                  {it.employee_name} · {it.employee_trade}
                  {it.employee_crew ? ` · ${it.employee_crew}` : ""}
                  {` · ${t("exp")} `}{it.expires_at || t("n/a")}
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
              {` · ${t("Qualification")} `}{selected.qualification_type}
              {` · ${t("Status")} `}{selected.verification_status?.toUpperCase()}
              {` · ${t("Expires")} `}{selected.expires_at || t("n/a")}
              {selected.warning ? ` · ${t("EXPIRES SOON")} ⚠` : ""}
            </div>
          )}
        </>
      )}
    </div>
  );
}
