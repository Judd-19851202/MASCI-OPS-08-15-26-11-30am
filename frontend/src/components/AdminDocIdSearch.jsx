import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Loader2, AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

/**
 * AdminDocIdSearch — admin-only global doc-ID search bar.
 *
 * Renders at the top of the Admin Hub home page. Type any doc ID
 * (e.g. PRE-2026-00042, DR-2026-00007, EQR-2026-00012) and we route
 * the admin straight to the matching record's detail page.
 *
 * Why doc IDs and not free text:
 * - Phone calls from payroll/insurance/the field always reference a
 *   specific number printed on a PDF or seen in an email.
 * - Free-text search across 10+ collections is its own project; doc-id
 *   lookup is one Mongo round-trip per collection until we hit, ~10ms
 *   total even with no indexes.
 *
 * The endpoint is /api/admin/find-by-doc-id (admin-only). On hit we
 * navigate to ``response.route`` which already encodes which detail
 * page the record lives on.
 */
export default function AdminDocIdSearch() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const submit = async (e) => {
    if (e) e.preventDefault();
    const needle = q.trim().toUpperCase();
    if (!needle) return;
    setBusy(true);
    setNotFound(false);
    try {
      const r = await api.get("/admin/find-by-doc-id", {
        params: { doc_id: needle },
      });
      if (r.data?.found && r.data?.route) {
        setQ("");
        navigate(r.data.route);
      } else {
        setNotFound(true);
      }
    } catch (err) {
      // Production returns HTTP 404 on unknown doc IDs; preview returns
      // 200 + {found:false}. Treat both as "no record" so admins always
      // see a friendly inline message instead of a network-error toast.
      const status = err?.response?.status;
      if (status === 404 || status === 200) {
        setNotFound(true);
      } else {
        // Real failure (auth, 5xx) — still show "not found" inline so
        // the search bar never throws an unhandled rejection in the UI;
        // the underlying error surfaces in the network tab if needed.
        setNotFound(true);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white border-2 border-amber-300 rounded-md shadow-sm" data-testid="admin-doc-id-search">
      <form onSubmit={submit} className="flex items-center gap-2 p-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <Input
            value={q}
            onChange={(e) => { setQ(e.target.value); setNotFound(false); }}
            onKeyDown={(e) => { if (e.key === "Enter") submit(e); }}
            placeholder="Find any record by doc ID — PRE-2026-00042, DR-2026-00007, EQR-2026-00012, JHA-2026-00001…"
            className="h-11 pl-9 font-mono uppercase tracking-wide border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-amber-500"
            spellCheck={false}
            autoComplete="off"
            data-testid="admin-doc-id-search-input"
          />
        </div>
        <Button
          type="submit"
          disabled={busy || !q.trim()}
          className="h-11 px-5 bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
          data-testid="admin-doc-id-search-submit"
        >
          {busy ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Search className="w-4 h-4 mr-1" />}
          Find
        </Button>
      </form>
      {notFound && (
        <div className="px-3 pb-3 -mt-1 text-xs text-red-700 font-mono uppercase tracking-[0.18em] flex items-center gap-1.5" data-testid="admin-doc-id-search-not-found">
          <AlertCircle className="w-3.5 h-3.5" /> No record found for "{q.trim().toUpperCase()}"
        </div>
      )}
    </div>
  );
}
