import React, { useEffect, useState, useMemo } from "react";
import { Loader2, X, Check, AlertOctagon, Wrench } from "lucide-react";
import { api } from "@/lib/api";

/**
 * OutstandingEquipmentLookup — auto-link block used by the Employee
 * Termination form. When an employee is selected/typed, we query the
 * equipment_checkout records via the existing Field Leadership records
 * endpoint and surface every un-returned line as a red chip the
 * supervisor must acknowledge (✓) or remove (✗) one-by-one.
 *
 * The `value` is a list of acknowledged line refs:
 *     [{checkout_id, line_index, serial, name, status}]
 * where status is "still_outstanding" | "returned_at_termination" | "removed".
 *
 * The form serializes that list into `details.outstanding_equipment_acknowledged`
 * so the PDF + admin records list can display the resolution.
 */
export function OutstandingEquipmentLookup({ employeeName, value, onChange, lang, t }) {
  const acknowledged = useMemo(
    () => (Array.isArray(value) ? value : []),
    [value]
  );
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    const name = (employeeName || "").trim();
    if (!name) {
      setLines([]);
      return;
    }
    let alive = true;
    setLoading(true);
    setErr("");
    api
      .get("/field-leadership", {
        params: { kind: "equipment_checkout", q: name, limit: 100 },
      })
      .then((r) => {
        if (!alive) return;
        const all = r.data?.items || [];
        // Only records where employee_name fuzzy-matches.
        const target = name.toLowerCase();
        const out = [];
        for (const rec of all) {
          if (!(rec.employee_name || "").toLowerCase().includes(target)) continue;
          const eqLines = (rec.details || {}).equipment_lines || [];
          eqLines.forEach((line, idx) => {
            if (!line || line.returned) return;
            out.push({
              checkout_id: rec.id,
              line_index: idx,
              project_number: rec.project_number,
              project_name: rec.project_name,
              checkout_date: rec.occurred_at || rec.created_at,
              name: line.name || "",
              manufacturer: line.manufacturer || "",
              model: line.model || "",
              serial: line.serial || "",
              qty: line.qty || 1,
              replacement_value: line.replacement_value || 0,
              condition: line.condition || "",
            });
          });
        }
        setLines(out);
      })
      .catch((e) => {
        if (!alive) return;
        setErr(e?.response?.data?.detail || e.message || "Lookup failed");
        setLines([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [employeeName]);

  const setLineStatus = (key, status) => {
    const filtered = acknowledged.filter((a) => a.key !== key);
    if (status) {
      const line = lines.find((l) => `${l.checkout_id}#${l.line_index}` === key);
      if (line) {
        filtered.push({
          key,
          checkout_id: line.checkout_id,
          line_index: line.line_index,
          name: line.name,
          serial: line.serial,
          status,
        });
      }
    }
    onChange(filtered);
  };

  const statusFor = (key) => acknowledged.find((a) => a.key === key)?.status || null;

  if (!employeeName || !employeeName.trim()) {
    return (
      <div className="text-xs text-slate-500 italic border-2 border-dashed border-slate-200 rounded p-3">
        {t("Select an employee above to auto-check for outstanding equipment.")}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-600 border-2 border-slate-200 rounded p-3 bg-slate-50">
        <Loader2 className="w-4 h-4 animate-spin" />
        {t("Checking outstanding equipment…")}
      </div>
    );
  }

  if (err) {
    return (
      <div className="text-xs text-red-700 border-2 border-red-300 rounded p-3 bg-red-50">
        {err}
      </div>
    );
  }

  if (lines.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-emerald-800 border-2 border-emerald-300 rounded p-3 bg-emerald-50"
           data-testid="outstanding-equipment-clear">
        <Check className="w-4 h-4" />
        {t("No outstanding equipment on file for this employee.")}
      </div>
    );
  }

  return (
    <div className="border-2 border-red-300 rounded-md bg-red-50 p-3 space-y-2"
         data-testid="outstanding-equipment-list">
      <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] font-bold text-red-800">
        <AlertOctagon className="w-3.5 h-3.5" />
        {t("Outstanding equipment on file — review each item")}
        <span className="ml-auto bg-red-700 text-white px-2 py-0.5 rounded-sm">
          {lines.length}
        </span>
      </div>
      {lines.map((line) => {
        const key = `${line.checkout_id}#${line.line_index}`;
        const status = statusFor(key);
        return (
          <div key={key}
               className="bg-white border-2 border-red-200 rounded-md p-2.5 flex flex-wrap sm:flex-nowrap gap-2 items-start"
               data-testid={`outstanding-item-${line.serial || line.line_index}`}>
            <Wrench className="w-4 h-4 mt-1 text-red-700 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-bold text-sm break-words">
                {line.name || t("(unnamed)")}
                {line.manufacturer ? ` · ${line.manufacturer}` : ""}
                {line.model ? ` · ${line.model}` : ""}
              </div>
              <div className="text-[11px] font-mono text-slate-600 mt-0.5">
                {line.serial && <span>SN/ASSET · <strong>{line.serial}</strong></span>}
                {line.qty ? <span className="ml-3">QTY · {line.qty}</span> : null}
                {line.replacement_value
                  ? <span className="ml-3">VALUE · ${Number(line.replacement_value).toFixed(2)}</span>
                  : null}
                {line.project_number && <span className="ml-3">JOB · {line.project_number}</span>}
              </div>
            </div>
            <div className="flex gap-1 shrink-0">
              <button
                type="button"
                onClick={() => setLineStatus(key, status === "returned_at_termination" ? null : "returned_at_termination")}
                className={`h-8 px-2 rounded border-2 text-[11px] font-bold uppercase tracking-wide ${
                  status === "returned_at_termination"
                    ? "bg-emerald-700 text-white border-emerald-800"
                    : "bg-white text-emerald-700 border-emerald-400 hover:bg-emerald-50"
                }`}
                data-testid={`outstanding-${key}-returned`}
              >
                {t("Returned")}
              </button>
              <button
                type="button"
                onClick={() => setLineStatus(key, status === "still_outstanding" ? null : "still_outstanding")}
                className={`h-8 px-2 rounded border-2 text-[11px] font-bold uppercase tracking-wide ${
                  status === "still_outstanding"
                    ? "bg-red-700 text-white border-red-800"
                    : "bg-white text-red-700 border-red-400 hover:bg-red-50"
                }`}
                data-testid={`outstanding-${key}-unreturned`}
              >
                {t("Unreturned")}
              </button>
              <button
                type="button"
                onClick={() => setLineStatus(key, status === "removed" ? null : "removed")}
                className={`h-8 w-8 rounded border-2 flex items-center justify-center ${
                  status === "removed"
                    ? "bg-slate-700 text-white border-slate-800"
                    : "bg-white text-slate-500 border-slate-300 hover:bg-slate-50"
                }`}
                title={t("Not assigned to this employee")}
                data-testid={`outstanding-${key}-remove`}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        );
      })}
      <div className="text-[11px] font-mono text-slate-600 mt-2">
        {t("Mark each item as Returned, Unreturned, or remove (not assigned to this employee).")}
      </div>
    </div>
  );
}

export default OutstandingEquipmentLookup;
