/**
 * pm/command/PmProjectSelector.jsx — single-project filter.
 *
 * Calls /api/pm/jobs (existing PM-scoped jobs endpoint) so PMs see
 * only their assigned projects in the dropdown. Admins see all jobs.
 * No new backend route needed.
 */
import React, { useEffect, useState } from "react";
import { getAdminToken } from "@/lib/adminAuth";
import { getDirectoryToken } from "@/lib/directoryAuth";
import { getPmToken } from "@/lib/pmAuth";
import { containsOperatorUnsafeLanguage, formatOperatorJobLabel } from "@/lib/operatorLanguage";

const API = process.env.REACT_APP_BACKEND_URL;

async function fetchPmProjects() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const p = getPmToken();
  const d = getDirectoryToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  if (d) h["X-Directory-Token"] = d;
  // /api/pm/jobs returns either array or { jobs: [...] }; handle both.
  try {
    const r = await fetch(`${API}/api/pm/jobs`, { headers: h });
    if (!r.ok) return [];
    const j = await r.json();
    const rows = Array.isArray(j) ? j : (j.items || j.jobs || j.rows || []);
    return rows
      .map((x) => ({
        project_number: x.project_number || x.number || "",
        project_name: x.project_name || x.name || x.title || "",
      }))
      .filter((x) => x.project_number);
  } catch (_e) { return []; }
}

export default function PmProjectSelector({ value, projectNumber, onChange }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const selectedValue = value ?? projectNumber ?? "";

  useEffect(() => {
    let live = true;
    fetchPmProjects().then((rows) => {
      if (!live) return;
      // Deduplicate by project_number, preserve order
      const seen = new Set();
      const out = [];
      const currentValue = selectedValue || "";
      for (const r of rows) {
        if (!seen.has(r.project_number)) {
          seen.add(r.project_number);
          out.push(r);
        }
      }
      if (currentValue && !seen.has(currentValue)) {
        out.unshift({ project_number: currentValue, project_name: "Current project" });
      }
      setOptions(out);
      setLoading(false);
    });
    return () => { live = false; };
  }, [selectedValue]);

  return (
    <div className="flex items-center gap-2" data-testid="pm-project-selector-wrapper">
      <label className="text-[10px] uppercase tracking-widest font-bold text-slate-500" htmlFor="pm-cc-project-select">
        Project
      </label>
      <select
        id="pm-cc-project-select"
        data-testid="pm-project-selector"
        value={selectedValue}
        onChange={(e) => onChange(e.target.value || null)}
        className="text-xs sm:text-sm border border-slate-300 rounded px-2 py-1 bg-white text-slate-900 focus:border-slate-500 focus:ring-1 focus:ring-slate-400 focus:outline-none max-w-xs"
      >
        <option value="">{loading ? "Loading projects…" : "All my projects"}</option>
        {options.map((o) => (
          <option key={o.project_number} value={o.project_number}>
            {containsOperatorUnsafeLanguage(`${o.project_number} ${o.project_name || ""}`)
              ? "Project support"
              : formatOperatorJobLabel(o.project_number, o.project_name || o.project_number)}
          </option>
        ))}
      </select>
    </div>
  );
}
