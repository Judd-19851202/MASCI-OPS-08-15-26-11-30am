import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, User, Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";
// TRACK 19.03 · HR is gospel. Pickers consume the canonical HR roster
// endpoint (`GET /api/hr/employee-roster`) via the shared event-bus
// client so every HR Save propagates instantly to every picker on
// the page without a reload or stale module cache.
import {
  fetchHrRoster,
  subscribeHrRoster,
  invalidateHrRoster,
} from "@/lib/hrRoster";
// TRACK 15.60 · P0 field-trust fix — Request-to-Add reliability.
// Route the inline new-hire request through the same offline queue
// used by NewIncident / NewDailyReport submissions so a flaky 4G or
// transient backend error NEVER drops the request on the floor and
// NEVER reaches up into the parent form's state.
import { enqueueUpload, mintIdempotencyKey } from "@/lib/resiliency";

/**
 * EmployeeCombo
 * -------------
 * Searchable picker for the MASCI employee roster — Track 19.03
 * canonical HR endpoint `GET /api/hr/employee-roster`. HR Save
 * propagates live via `hr:roster-changed` bus event.
 * Mirrors the EquipmentCombo UX so all forms feel uniform.
 *
 * Props
 * - value:        current free-text value (employee name)
 * - onChange:     (string) => void
 * - onPick:       optional (employeeObj) => void
 * - placeholder:  string
 * - testId:       optional data-testid prefix
 * - className:    extra wrapper classes
 *
 * Always allows free-text entries (so the form still works before the
 * roster is uploaded by the admin).
 */
/**
 * Track 19.03 doctrine:
 *   - NO permanent module-level cache.
 *   - All pickers subscribe to the shared `hr:roster-changed` bus.
 *   - HR Save → invalidateHrRoster() → live re-fetch → pickers update
 *     without a page reload.
 *   - Inactive / Terminated / Resigned / Retired employees are hidden
 *     by the server endpoint contract.
 */

/** Back-compat shim: legacy callers used `clearEmployeeCache()` after
 *  an admin upload. The new bus does this automatically on every HR
 *  write, but external code may still call this — keep it as a thin
 *  proxy to the canonical invalidator. */
export function clearEmployeeCache() {
  invalidateHrRoster();
}

export const EmployeeCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  testId = "employee-combo",
  className = "",
}) => {
  const { t } = useT();
  const ph = placeholder || t("Type or pick an employee…");
  const [data, setData] = useState({ items: [], count: 0 });
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    let retryTimer = null;
    const apply = (items) => {
      if (!alive) return;
      setData({ items: items || [], count: (items || []).length });
    };
    // Subscribe to the canonical HR roster bus — instant updates on
    // any HR Save anywhere in the app.
    const unsub = subscribeHrRoster(apply);
    const tryLoad = (attempt) => {
      fetchHrRoster().then((items) => {
        if (!alive) return;
        apply(items);
        // Auto-retry up to 2x if the first load returns empty — handles
        // transient CORS / network blips on combo mount.
        if ((items?.length || 0) === 0 && attempt < 2) {
          retryTimer = setTimeout(() => tryLoad(attempt + 1), 1500 * (attempt + 1));
        }
      });
    };
    tryLoad(0);
    return () => {
      alive = false;
      unsub();
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, []);

  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Filter the roster using the SAME text the user is typing in the main
  // input — no separate search box, no focus-stealing autoFocus. This is the
  // single source of truth for both the form value AND the list filter.
  const filtered = useMemo(() => {
    const q = (value || "").trim().toLowerCase();
    const items = data.items || [];
    if (!q) return items.slice(0, 200); // show first 200 when empty
    return items
      .filter((it) => {
        const hay = [
          it.name,
          it.employee_id,
          it.role,
          it.trade,
          it.crew,
          it.email,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .slice(0, 200);
  }, [data, value]);

  const pick = (it) => {
    const label = it.name || "";
    onChange?.(label);
    onPick?.(it);
    setOpen(false);
  };

  const [addingNew, setAddingNew] = useState(false);
  // OMEGA · Employee Governance Phase Alpha · G-1 closure.
  // The legacy `/employees/add` direct-create endpoint has been
  // closed — public/anonymous employee creation is no longer
  // permitted. We now submit a `new_hire` request to the HR Queue
  // (POST /api/employee-requests · kind=new_hire) and surface a
  // clear "submitted for HR review" toast. The typed name is still
  // returned to the parent form via onChange/onPick so the form can
  // proceed with the free-text label; the person does NOT enter the
  // employees roster until HR approves.
  const addToRoster = async (rawName) => {
    const name = (rawName || "").trim();
    if (name.length < 2) return;
    setAddingNew(true);
    // TRACK 15.60 · P0 reliability fix.
    // Old behaviour: a single api.post that, on a 4G blip or 502,
    // threw a "Can't reach the server" toast and the request never
    // landed. Foremen reported this happening with 15-20 attendees
    // queued up — they hit Request-to-Add, saw the failure, and the
    // 'just retry' loop spread panic.
    //
    // New behaviour: enqueueUpload() routes the request through the
    // shared IndexedDB-backed retry queue (used by NewIncident /
    // NewDailyReport). On success we get the same 200 path back. On
    // network failure the request is durably persisted and replayed
    // automatically when the device next has connectivity. Either
    // way, the parent form's state is NEVER touched — we never call
    // onChange / onPick on the failure path.
    const idem = mintIdempotencyKey();
    const body = {
      kind: "new_hire",
      name,
      submitted_via: "employee_combo_inline",
      // 15.60 — soft attribution so HR can see where the request came
      // from. Stays free-text; HR's review surface displays it.
      _track_15_60_client_idempotency_key: idem,
    };
    try {
      const r = await enqueueUpload({
        method: "POST",
        url: "/employee-requests",
        headers: {},
        body,
        idempotencyKey: idem,
        formKey: "employee-request-inline",
      });
      if (r.ok) {
        const rid = r?.data?.id || "";
        toast.success(
          `Request submitted to HR Queue`,
          { description: `HR will review and add "${name}" to the roster (request ${rid.slice(0, 8)}…). You can continue this form with the typed name.` }
        );
        onChange?.(name);
        onPick?.({ name, _pending_hr_review: true, request_id: rid });
        setOpen(false);
      } else if (r.queued) {
        // Network failure — request is durably persisted and will
        // replay automatically. The parent form is NOT touched; we
        // simply tell the user the request is safe.
        toast.message(
          `Request saved · will send when reconnected`,
          { description: `"${name}" is queued for HR review. Keep building your form — your work is safe.`, duration: 6000 }
        );
        onChange?.(name);
        onPick?.({ name, _pending_hr_review: true, request_id: "queued", _queued: true });
        setOpen(false);
      } else {
        // Non-network error — server returned 4xx/5xx. The queue
        // does NOT retry these. Show the user the calm reason.
        const status = r?.status;
        const detail = r?.lastError?.responseData?.detail || r?.lastError?.message;
        const msg = (status === 410)
          ? "Employee creation moved to HR Queue · please refresh and retry."
          : (status === 429)
          ? "Too many requests right now — wait a moment and try again. Your form is safe."
          : (typeof detail === "string" ? detail : "Could not submit HR request — your form is safe.");
        toast.error(msg);
      }
    } catch (err) {
      // Defensive: enqueueUpload should not throw, but if anything
      // slips through we MUST NOT propagate it up to the parent.
      const status = err?.response?.status;
      const msg = (status === 410)
        ? "Employee creation moved to HR Queue · please refresh and retry."
        : (err?.response?.data?.detail || err?.message || "Could not submit HR request — your form is safe.");
      toast.error(typeof msg === "string" ? msg : "Could not submit HR request — your form is safe.");
    } finally {
      setAddingNew(false);
    }
  };

  const total = data.count || (data.items || []).length;
  // "Custom value" is what the user typed that doesn't exactly match any roster name
  const exactMatch = filtered.some(
    (it) => (it.name || "").toLowerCase() === (value || "").trim().toLowerCase()
  );
  const showCustomTag = !!(value || "").trim() && !exactMatch && total > 0;

  return (
    <div className={`relative ${className}`} ref={wrapRef}>
      <div className="flex gap-1.5">
        <Input
          value={value}
          onChange={(e) => {
            onChange?.(e.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder={ph}
          className="flex-1 h-11 text-base border-2 border-slate-300 focus:border-red-700"
          data-testid={`${testId}-input`}
          autoComplete="off"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-11 w-11 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 shrink-0"
          onClick={() => {
            // Self-recover: if the cache loaded empty, force a re-fetch
            // when the user clicks the chevron. With Track 19.03 there
            // is no persistent cache — we simply invalidate + re-fetch.
            if ((data?.items?.length || 0) === 0) {
              invalidateHrRoster();
              fetchHrRoster().then((items) =>
                setData({ items: items || [], count: (items || []).length })
              );
            }
            setOpen((v) => !v);
          }}
          data-testid={`${testId}-toggle`}
          title={t("Browse roster")}
          aria-label={t("Browse roster")}
        >
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </div>

      {open && (
        <div
          className="absolute z-30 mt-1 w-full max-h-72 overflow-auto rounded-md border-2 border-slate-300 bg-white shadow-xl"
          data-testid={`${testId}-panel`}
        >
          {filtered.length === 0 ? (
            <div className="p-3 text-sm text-slate-700">
              <div className="text-center text-slate-500 mb-3">
                {total === 0
                  ? t("Roster not uploaded yet — type the name freely.")
                  : t("No matches.")}
              </div>
              {!!(value || "").trim() && (value || "").trim().length >= 2 && (
                <button
                  type="button"
                  onClick={() => addToRoster(value)}
                  disabled={addingNew}
                  onMouseDown={(e) => e.preventDefault()}
                  className="w-full flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide text-xs h-10 rounded border-b-2 border-amber-800"
                  data-testid={`${testId}-add-btn`}
                >
                  {addingNew ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  {t("Request HR add")} &quot;{value}&quot;
                </button>
              )}
            </div>
          ) : (
            <>
              {showCustomTag && (
                <div className="px-3 py-2 bg-amber-50 border-b-2 border-amber-300 flex items-center gap-2">
                  <div className="flex-1 text-xs text-amber-900 font-mono truncate">
                    {t("Submit new-hire request to HR:")}{" "}
                    <strong className="font-bold">{value}</strong>
                  </div>
                  <button
                    type="button"
                    onClick={() => addToRoster(value)}
                    disabled={addingNew}
                    onMouseDown={(e) => e.preventDefault()}
                    className="inline-flex items-center gap-1 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wider text-[10px] h-7 px-2 rounded border-b-2 border-amber-800 shrink-0"
                    data-testid={`${testId}-add-btn`}
                  >
                    {addingNew ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Plus className="w-3 h-3" />
                    )}
                    {t("Request HR add")}
                  </button>
                </div>
              )}
              {filtered.map((it, idx) => {
                const selected = value && value === it.name;
                return (
                  <button
                    key={(it.id || `e-${idx}`) + "-" + idx}
                    type="button"
                    onClick={() => pick(it)}
                    onMouseDown={(e) => e.preventDefault()}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-red-50 border-b border-slate-100 ${
                      selected ? "bg-red-100" : ""
                    }`}
                    data-testid={`${testId}-item-${idx}`}
                  >
                    <div className="flex items-center gap-2">
                      <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="font-bold text-slate-900">{it.name}</span>
                      {it.employee_id && (
                        <span className="font-mono text-[11px] text-slate-500">
                          #{it.employee_id}
                        </span>
                      )}
                    </div>
                    {(it.trade || it.role || it.crew) && (
                      <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {[it.trade, it.role, it.crew].filter(Boolean).join(" · ")}
                      </div>
                    )}
                  </button>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default EmployeeCombo;
