// TRACK 15.46 · FR-07 · Safety-Meeting attendee bulk multi-select.
//
// Replaces the "tap Add Attendee N times" pattern with a single dialog
// that lets the foreman pick every crew member at once from the
// certified `employees` roster (the same roster `EmployeeCombo` uses).
//
// Design choices (kept tight on purpose):
//   • Reuses GET /api/employees via the shared `EmployeeCombo` cache.
//     No new endpoint, no new collection — Track 15.40's directory
//     resolution still works because we capture canonical
//     `employee_id` on every row we add.
//   • Pure additive UI — the existing single-row "Add Attendee" stays.
//     If the foreman prefers the original flow, nothing changes.
//   • Signature + acknowledgement are intentionally NOT pre-filled.
//     Bulk-add removes the typing burden; the legal weight of the
//     meeting still requires each person to sign on the form.

import React, { useEffect, useMemo, useState } from "react";
import { brandCompanyName } from "@/lib/brandFilename";
import { Users, Search, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { toast } from "sonner";

export function AttendeeBulkAddDialog({ onAdd, existing = [] }) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [roster, setRoster] = useState([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState({}); // employee id → true

  // Existing employee_ids — keeps the dialog from offering duplicates.
  const existingIds = useMemo(() => {
    const s = new Set();
    for (const a of existing) {
      if (a && a.employee_id) s.add(a.employee_id);
    }
    return s;
  }, [existing]);

  useEffect(() => {
    if (!open) return;
    let alive = true;
    setLoading(true);
    api
      .get("/employees", { timeout: 30000 })
      .then((r) => {
        if (!alive) return;
        const items = Array.isArray(r?.data?.items) ? r.data.items : [];
        setRoster(items);
      })
      .catch(() => {
        if (alive) toast.error(t("Could not load roster"));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [open, t]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return roster.filter((e) => {
      const name = String(e?.name || e?.full_name || "").toLowerCase();
      const trade = String(e?.trade || e?.role || e?.position || "").toLowerCase();
      if (!q) return true;
      return name.includes(q) || trade.includes(q);
    });
  }, [roster, query]);

  const pickedCount = Object.values(picked).filter(Boolean).length;

  const togglePick = (id) => {
    setPicked((p) => ({ ...p, [id]: !p[id] }));
  };

  const selectAllVisible = () => {
    setPicked((p) => {
      const next = { ...p };
      for (const e of filtered) {
        const id = e.id || e.employee_id;
        if (!id) continue;
        if (existingIds.has(id)) continue;
        next[id] = true;
      }
      return next;
    });
  };

  const clearAll = () => setPicked({});

  const submit = () => {
    const additions = [];
    for (const e of roster) {
      const id = e.id || e.employee_id;
      if (!id || !picked[id]) continue;
      if (existingIds.has(id)) continue;
      additions.push({
        name: e.name || e.full_name || "",
        employee_id: id,
        non_masci: false,
        // Track 15.73 Slice 2 · default to MASCI (the canonical OurCo
        // name), not "Customer". The roster picker only loads MASCI
        // employees (GET /api/employees is the OurCo-scoped endpoint),
        // so a bulk-added person from this list is, by definition, a
        // MASCI employee. The backend `normalize_meeting_attendees`
        // guard re-verifies and locks this value at submit time.
        company: brandCompanyName("MASCI"),
        trade: e.trade || e.role || e.position || e.job_title || "",
        signature: "",
        acknowledged: false,
        acknowledged_at: "",
        // Track 15.73 Slice 2 · derived identity hints (backend re-derives
        // these authoritatively from the canonical `employees` lookup).
        attendee_type: "employee",
        source: "employee_master",
        is_masci_employee: true,
        is_subcontractor: false,
        is_manual: false,
      });
    }
    if (additions.length === 0) {
      toast.error(t("Pick at least one person"));
      return;
    }
    onAdd(additions);
    toast.success(
      t("{n} attendees added — collect signatures").replace(
        "{n}",
        String(additions.length),
      ),
    );
    setPicked({});
    setQuery("");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className="w-full h-12 border-2 border-dashed border-blue-400 hover:border-blue-700 hover:text-blue-700 font-bold uppercase tracking-wide text-sm"
          data-testid="attendee-bulk-add-open"
        >
          <Users className="w-4 h-4 mr-2" />
          {t("Bulk Add from Roster")}
        </Button>
      </DialogTrigger>
      <DialogContent
        className="max-w-2xl"
        data-testid="attendee-bulk-add-dialog"
      >
        <DialogHeader>
          <DialogTitle>{t("Bulk Add Attendees")}</DialogTitle>
          <DialogDescription>
            {t(
              "Pick everyone on this crew. Names + trades pre-fill from the certified roster. Signatures and acknowledgements still get collected on the form.",
            )}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("Search name or trade…")}
              className="pl-9"
              data-testid="attendee-bulk-add-search"
            />
          </div>
          <div className="flex items-center justify-between text-xs text-slate-600">
            <span data-testid="attendee-bulk-add-counts">
              {t("{n} of {m} shown")
                .replace("{n}", String(filtered.length))
                .replace("{m}", String(roster.length))}
              {" · "}
              {t("{n} picked").replace("{n}", String(pickedCount))}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={selectAllVisible}
                className="text-blue-700 font-medium hover:text-blue-900"
                data-testid="attendee-bulk-add-select-all"
              >
                {t("Select visible")}
              </button>
              <span className="text-slate-300">·</span>
              <button
                type="button"
                onClick={clearAll}
                className="text-slate-600 font-medium hover:text-slate-900"
                data-testid="attendee-bulk-add-clear"
              >
                {t("Clear")}
              </button>
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto border border-slate-200 rounded-md">
            {loading ? (
              <div className="p-6 text-center text-slate-500 text-sm">
                <Loader2 className="w-4 h-4 inline animate-spin mr-2" />
                {t("Loading roster…")}
              </div>
            ) : filtered.length === 0 ? (
              <div
                className="p-6 text-center text-slate-500 text-sm"
                data-testid="attendee-bulk-add-empty"
              >
                {t("No matches")}
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {filtered.map((e) => {
                  const id = e.id || e.employee_id;
                  if (!id) return null;
                  const already = existingIds.has(id);
                  const selected = !!picked[id];
                  return (
                    <li
                      key={id}
                      className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-slate-50 ${
                        selected ? "bg-blue-50" : ""
                      } ${already ? "opacity-50 cursor-not-allowed" : ""}`}
                      onClick={() => {
                        if (already) return;
                        togglePick(id);
                      }}
                      data-testid={`attendee-bulk-add-row-${id}`}
                    >
                      <span
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                          selected
                            ? "border-blue-700 bg-blue-700 text-white"
                            : "border-slate-300 bg-white"
                        }`}
                      >
                        {selected && <Check className="w-3.5 h-3.5" />}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">
                          {e.name || e.full_name || "—"}
                        </div>
                        <div className="text-xs text-slate-500 truncate">
                          {e.trade || e.role || e.position || e.job_title || "—"}
                          {already && (
                            <span className="ml-2 text-amber-700">
                              · {t("already added")}
                            </span>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setOpen(false)}
            data-testid="attendee-bulk-add-cancel"
          >
            {t("Cancel")}
          </Button>
          <Button
            type="button"
            onClick={submit}
            disabled={pickedCount === 0}
            className="bg-red-700 hover:bg-red-800 text-white"
            data-testid="attendee-bulk-add-submit"
          >
            {t("Add {n} attendees").replace("{n}", String(pickedCount))}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
