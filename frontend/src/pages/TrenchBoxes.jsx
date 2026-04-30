import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Box, Search, ChevronDown, ChevronRight, FileText } from "lucide-react";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import TabulatedDataPrimer from "@/components/TabulatedDataPrimer";
import TrenchBoxTabulatedLibrary from "@/components/TrenchBoxTabulatedLibrary";

const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Field = ({ label, value, accent }) => (
  <div className="flex flex-col">
    <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500">{label}</span>
    <span className={`text-sm font-bold ${accent || "text-slate-900"}`}>{value || "—"}</span>
  </div>
);

export default function TrenchBoxes() {
  const { t } = useT();
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [openId, setOpenId] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/trench-boxes");
        if (alive) setBoxes(r.data || []);
      } catch {
        if (alive) setBoxes([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return boxes;
    return boxes.filter(
      (b) =>
        b.manufacturer.toLowerCase().includes(term) ||
        b.model.toLowerCase().includes(term) ||
        (b.serial_number || "").toLowerCase().includes(term)
    );
  }, [boxes, q]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link to="/" className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide" data-testid="back-link">
            <ArrowLeft className="w-4 h-4 mr-1" /> Hub
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="mb-6">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">{t("Trench Box Tabulated Data")}</span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("OSHA-compliant trench shields in MASCI fleet")}
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            {t("Tap any box to see its size, weight, and maximum allowable depth by soil type (OSHA 1926 Subpart P).")}
          </p>
        </div>

        <TabulatedDataPrimer />

        <TrenchBoxTabulatedLibrary adminMode={false} />

        <div className="mb-4 mt-8">
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900">
            {t("Fleet — Trench Box Details")}
          </h2>
          <p className="text-slate-600 text-sm mt-1">
            {t("Every active trench shield with manufacturer data and OSHA soil ratings.")}
          </p>
        </div>

        <div className="relative mb-5">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("Search by manufacturer, model, serial…")} className="h-12 pl-9 border-2 border-slate-300" data-testid="trench-search" />
        </div>

        {loading ? (
          <p className="text-sm text-slate-500 italic">{t("Loading…")}</p>
        ) : boxes.length === 0 ? (
          <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-6 text-amber-900">
            <div className="font-display text-lg font-black mb-1 flex items-center gap-2">
              <Box className="w-5 h-5" /> {t("No trench boxes have been added yet")}
            </div>
            <p className="text-sm">
              {t("An admin will add MASCI's trench-box fleet here. Once added, the data will be searchable on every device.")}
            </p>
          </div>
        ) : (
          <ul className="bg-white border-2 border-slate-300 rounded-md divide-y-2 divide-slate-100 overflow-hidden">
            {filtered.map((b) => {
              const isOpen = openId === b.id;
              return (
                <li key={b.id} data-testid={`trench-row-${b.id}`}>
                  <button
                    type="button"
                    onClick={() => setOpenId(isOpen ? null : b.id)}
                    className="w-full p-4 sm:p-5 flex items-center gap-3 text-left hover:bg-slate-50"
                  >
                    {isOpen ? <ChevronDown className="w-5 h-5 text-slate-400 shrink-0" /> : <ChevronRight className="w-5 h-5 text-slate-400 shrink-0" />}
                    <Box className="w-5 h-5 text-red-700 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-display font-bold text-slate-900 truncate">
                        {b.manufacturer} · {b.model}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5 truncate">
                        {b.serial_number ? `S/N ${b.serial_number} · ` : ""}{b.length_ft ? `${b.length_ft} ft long` : ""}{b.weight_lbs ? ` · ${b.weight_lbs} lbs` : ""}
                      </div>
                    </div>
                    {b.max_depth_type_c_60_ft && (
                      <span className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded bg-red-50 text-red-700 border border-red-200 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
                        Type C max {b.max_depth_type_c_60_ft} ft
                      </span>
                    )}
                  </button>

                  {isOpen && (
                    <div className="px-4 sm:px-5 pb-5 pt-2 grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 border-t border-slate-200">
                      <Field label={t("Type")} value={b.box_type} />
                      <Field label={t("Length (ft)")} value={b.length_ft} />
                      <Field label={t("Width Min/Max (ft)")} value={[b.width_min_ft, b.width_max_ft].filter(Boolean).join(" – ")} />
                      <Field label={t("Sidewall H × Thickness")} value={[b.sidewall_height_ft && `${b.sidewall_height_ft} ft`, b.sidewall_thickness_in && `${b.sidewall_thickness_in}"`].filter(Boolean).join(" / ")} />
                      <Field label={t("Weight (lbs)")} value={b.weight_lbs} />
                      <Field label={t("Spreaders")} value={b.spreader_count} />
                      <Field label={t("Stacking")} value={b.stacking_allowed === "Yes" ? `Yes — max ${b.stacking_max || 1}` : "No"} />
                      <div></div>

                      <div className="col-span-2 sm:col-span-4 mt-2 pt-3 border-t border-slate-200">
                        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">{t("Maximum Allowable Depth (OSHA 1926.652)")}</div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          <Field label="Type A" value={b.max_depth_type_a_ft && `${b.max_depth_type_a_ft} ft`} accent="text-emerald-700" />
                          <Field label="Type B" value={b.max_depth_type_b_ft && `${b.max_depth_type_b_ft} ft`} accent="text-amber-700" />
                          <Field label="Type C-60" value={b.max_depth_type_c_60_ft && `${b.max_depth_type_c_60_ft} ft`} accent="text-red-700" />
                          <Field label="Type C-80" value={b.max_depth_type_c_80_ft && `${b.max_depth_type_c_80_ft} ft`} accent="text-red-700" />
                        </div>
                      </div>

                      {b.notes && (
                        <div className="col-span-2 sm:col-span-4 mt-2">
                          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">{t("Notes")}</div>
                          <div className="text-sm text-slate-700 whitespace-pre-wrap">{b.notes}</div>
                        </div>
                      )}

                      <div className="col-span-2 sm:col-span-4 mt-2">
                        <a href={`${REACT_APP_BACKEND_URL}/api/trench-boxes/${b.id}/file`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 h-10 px-4 rounded bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs uppercase tracking-wide" data-testid={`view-tabdata-${b.id}`}>
                          <FileText className="w-4 h-4" /> {t("View Manufacturer Tabulated Data PDF")}
                        </a>
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
            {filtered.length === 0 && (
              <li className="p-8 text-center text-slate-500 italic">{t("No matches.")}</li>
            )}
          </ul>
        )}
      </main>
    </div>
  );
}
