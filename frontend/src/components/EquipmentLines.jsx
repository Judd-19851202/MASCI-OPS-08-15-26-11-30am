// Equipment Checkout — multi-line entry component for the
// Field Leadership / equipment_checkout form. Replaces the schema-driven
// field renderer with a richer per-item experience:
//  - Searchable equipment dropdown (auto-fills name + replacement value
//    + default manufacturer from the admin-managed catalog)
//  - Searchable manufacturer dropdown w/ "Other / Custom" fallback
//  - Per-line: name, manufacturer, model, serial, qty, replacement value,
//    condition, notes, photos
//  - Add Custom Equipment button (lets the user type any equipment name
//    when it's not in the catalog)
//  - Running grand total visible above the signature block
//
// Lines are stored on the form's `details.equipment_lines` array.

import React, { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, Search, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { PhotoUpload } from "@/components/PhotoUpload";

const inputCls =
  "h-11 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600";
const smallCls =
  "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600";

const CONDITIONS = [
  { en: "New", es: "Nuevo" },
  { en: "Good", es: "Bueno" },
  { en: "Fair", es: "Aceptable" },
  { en: "Damaged", es: "Dañado" },
];

const blankLine = () => ({
  catalog_id: null,        // null when custom
  name: "",
  manufacturer: "",        // dropdown value or custom string
  manufacturer_custom: "", // when manufacturer === "Other"
  model: "",
  serial: "",
  qty: 1,
  replacement_value: 0,
  condition: "Good",
  notes: "",
  photos: [],
});

const fmtMoney = (n) =>
  `$${(Number(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export function EquipmentLines({ value, onChange, lang, t }) {
  const lines = Array.isArray(value) ? value : [];
  const [catalog, setCatalog] = useState([]);
  const [makes, setMakes] = useState([]);
  const [openCatalogIdx, setOpenCatalogIdx] = useState(null);
  const [catalogQuery, setCatalogQuery] = useState("");

  useEffect(() => {
    api.get("/field-leadership/equipment-catalog").then((r) => setCatalog(r.data?.items || [])).catch(() => {});
    api.get("/field-leadership/equipment-makes").then((r) => setMakes(r.data?.items || [])).catch(() => {});
  }, []);

  const filteredCatalog = useMemo(() => {
    const q = catalogQuery.trim().toLowerCase();
    if (!q) return catalog.slice(0, 50);
    return catalog
      .filter((c) => (c.name || "").toLowerCase().includes(q) || (c.default_make || "").toLowerCase().includes(q))
      .slice(0, 50);
  }, [catalog, catalogQuery]);

  const addLine = (preset = {}) =>
    onChange([...lines, { ...blankLine(), ...preset }]);

  const removeLine = (idx) => onChange(lines.filter((_, i) => i !== idx));

  const updateLine = (idx, patch) =>
    onChange(lines.map((l, i) => (i === idx ? { ...l, ...patch } : l)));

  const pickCatalog = (idx, item) => {
    updateLine(idx, {
      catalog_id: item.id,
      name: item.name,
      manufacturer: item.default_make || "",
      manufacturer_custom: "",
      replacement_value: Number(item.replacement_value || 0),
    });
    setOpenCatalogIdx(null);
    setCatalogQuery("");
  };

  const grandTotal = useMemo(
    () =>
      lines.reduce((sum, l) => {
        const qty = Number(l.qty) || 0;
        const rv = Number(l.replacement_value) || 0;
        return sum + qty * rv;
      }, 0),
    [lines]
  );

  return (
    <div className="space-y-4" data-testid="equipment-lines">
      {/* Header + Add buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-t-2 border-slate-200 pt-5">
        <div>
          <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
            {t("Equipment Issued")}
          </Label>
          <p className="text-xs text-slate-500 mt-1">
            {t("Add each tool, vehicle, or asset issued. Search the catalog or add a custom item.")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            onClick={() => addLine()}
            className="bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs uppercase tracking-wide h-10"
            data-testid="equipment-add-line"
          >
            <Plus className="w-4 h-4 mr-1" /> {t("Add Equipment")}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => addLine({ catalog_id: null, name: "", replacement_value: 0 })}
            className="h-10 border-2"
            data-testid="equipment-add-custom"
          >
            <Plus className="w-4 h-4 mr-1" /> {t("Add Custom")}
          </Button>
        </div>
      </div>

      {lines.length === 0 && (
        <div className="border-2 border-dashed border-slate-300 rounded-md p-6 text-center text-slate-500 text-sm" data-testid="equipment-lines-empty">
          {t("No equipment added yet. Tap \"Add Equipment\" to issue the first item.")}
        </div>
      )}

      {lines.map((line, idx) => {
        const lineTotal = (Number(line.qty) || 0) * (Number(line.replacement_value) || 0);
        const useCustomMake = line.manufacturer === "Other";
        return (
          <div
            key={idx}
            className="border-2 border-slate-300 rounded-md p-4 sm:p-5 bg-white shadow-sm"
            data-testid={`equipment-line-${idx}`}
          >
            <div className="flex items-start justify-between gap-2 mb-3">
              <span className="inline-flex items-center px-2 py-1 rounded bg-blue-50 text-blue-800 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
                {t("Item")} #{idx + 1}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => removeLine(idx)}
                className="border-red-300 text-red-700 hover:bg-red-50 h-8"
                data-testid={`equipment-remove-${idx}`}
              >
                <Trash2 className="w-3.5 h-3.5 mr-1" /> {t("Remove")}
              </Button>
            </div>

            {/* Catalog picker */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Equipment / Tool")}</Label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setOpenCatalogIdx(openCatalogIdx === idx ? null : idx)}
                    className="w-full h-11 px-3 text-base border-2 border-slate-300 rounded-md flex items-center justify-between bg-white hover:border-blue-500"
                    data-testid={`equipment-catalog-trigger-${idx}`}
                  >
                    <span className={line.name ? "text-slate-900" : "text-slate-400"}>
                      {line.name || t("Search catalog or type custom name…")}
                    </span>
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  </button>
                  {openCatalogIdx === idx && (
                    <div className="absolute top-12 left-0 right-0 bg-white border-2 border-slate-300 rounded-md shadow-lg z-20 max-h-72 overflow-y-auto">
                      <div className="sticky top-0 bg-white p-2 border-b border-slate-200">
                        <div className="relative">
                          <Search className="absolute left-2 top-2.5 w-4 h-4 text-slate-400" />
                          <Input
                            autoFocus
                            value={catalogQuery}
                            onChange={(e) => setCatalogQuery(e.target.value)}
                            placeholder={t("Search equipment…")}
                            className="h-9 pl-8 border-slate-300"
                            data-testid={`equipment-catalog-search-${idx}`}
                          />
                        </div>
                      </div>
                      {filteredCatalog.length === 0 ? (
                        <div className="p-3 text-sm text-slate-500">{t("No matches.")}</div>
                      ) : (
                        filteredCatalog.map((c) => (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => pickCatalog(idx, c)}
                            className="w-full text-left px-3 py-2 hover:bg-blue-50 text-sm border-b border-slate-100 flex justify-between items-center"
                            data-testid={`equipment-catalog-item-${c.id}`}
                          >
                            <span>
                              <span className="font-semibold">{c.name}</span>
                              {c.default_make && <span className="text-slate-500 ml-2 text-xs">· {c.default_make}</span>}
                            </span>
                            <span className="font-mono text-blue-700 font-bold text-xs">{fmtMoney(c.replacement_value)}</span>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
                {/* Manual name override (always editable) */}
                <Input
                  value={line.name}
                  onChange={(e) => updateLine(idx, { name: e.target.value, catalog_id: null })}
                  placeholder={t("Or type custom equipment name")}
                  className={`${smallCls} mt-1`}
                  data-testid={`equipment-name-${idx}`}
                />
              </div>

              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Manufacturer / Make")}</Label>
                <Select
                  value={line.manufacturer || ""}
                  onValueChange={(v) => updateLine(idx, { manufacturer: v, manufacturer_custom: v === "Other" ? line.manufacturer_custom : "" })}
                >
                  <SelectTrigger className={inputCls} data-testid={`equipment-make-${idx}`}>
                    <SelectValue placeholder={t("Select manufacturer…")} />
                  </SelectTrigger>
                  <SelectContent>
                    {makes.map((m) => (
                      <SelectItem key={m.id} value={m.name}>{m.name}</SelectItem>
                    ))}
                    <SelectItem value="Other">{t("Other / Custom")}</SelectItem>
                  </SelectContent>
                </Select>
                {useCustomMake && (
                  <Input
                    value={line.manufacturer_custom || ""}
                    onChange={(e) => updateLine(idx, { manufacturer_custom: e.target.value })}
                    placeholder={t("Custom manufacturer")}
                    className={`${smallCls} mt-2`}
                    data-testid={`equipment-make-custom-${idx}`}
                  />
                )}
              </div>
            </div>

            {/* Model + Serial */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Model")}</Label>
                <Input
                  value={line.model || ""}
                  onChange={(e) => updateLine(idx, { model: e.target.value })}
                  className={smallCls}
                  data-testid={`equipment-model-${idx}`}
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Serial / Asset ID")}</Label>
                <Input
                  value={line.serial || ""}
                  onChange={(e) => updateLine(idx, { serial: e.target.value })}
                  className={smallCls}
                  data-testid={`equipment-serial-${idx}`}
                />
              </div>
            </div>

            {/* Qty + Replacement + Condition */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Quantity")}</Label>
                <Input
                  type="number"
                  min="1"
                  step="1"
                  value={line.qty}
                  onChange={(e) => updateLine(idx, { qty: Number(e.target.value) || 0 })}
                  className={smallCls}
                  data-testid={`equipment-qty-${idx}`}
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Replacement $")}</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={line.replacement_value}
                  onChange={(e) => updateLine(idx, { replacement_value: Number(e.target.value) || 0 })}
                  className={smallCls}
                  data-testid={`equipment-rv-${idx}`}
                />
              </div>
              <div className="col-span-2 sm:col-span-1">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Condition")}</Label>
                <Select value={line.condition || "Good"} onValueChange={(v) => updateLine(idx, { condition: v })}>
                  <SelectTrigger className={smallCls} data-testid={`equipment-condition-${idx}`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONDITIONS.map((o) => (
                      <SelectItem key={o.en} value={o.en}>{lang === "es" ? o.es : o.en}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2 sm:col-span-1 flex flex-col justify-end">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Line Total")}</Label>
                <div className="h-10 px-3 flex items-center font-mono text-base font-black text-blue-800 bg-blue-50 border-2 border-blue-200 rounded-md" data-testid={`equipment-line-total-${idx}`}>
                  {fmtMoney(lineTotal)}
                </div>
              </div>
            </div>

            <div className="mb-3">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Notes")}</Label>
              <Textarea
                rows={2}
                value={line.notes || ""}
                onChange={(e) => updateLine(idx, { notes: e.target.value })}
                className="border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600"
                data-testid={`equipment-notes-${idx}`}
              />
            </div>

            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Photos (optional)")}</Label>
              <PhotoUpload
                photos={line.photos || []}
                onChange={(p) => updateLine(idx, { photos: p })}
                testIdBase={`equipment-photos-${idx}`}
              />
            </div>
          </div>
        );
      })}

      {/* Grand total */}
      {lines.length > 0 && (
        <div
          className="rounded-md border-4 border-amber-400 bg-amber-50 px-5 py-4 flex items-center justify-between shadow-sm"
          data-testid="equipment-grand-total"
        >
          <div>
            <div className="font-mono text-xs uppercase tracking-[0.25em] text-amber-800 font-bold">
              {t("Total Replacement Value Issued")}
            </div>
            <div className="text-xs text-amber-900 mt-0.5">
              {lines.length} {lines.length === 1 ? t("item") : t("items")}
            </div>
          </div>
          <div className="font-display text-3xl sm:text-4xl font-black text-slate-900 tabular-nums" data-testid="equipment-grand-total-amount">
            {fmtMoney(grandTotal)}
          </div>
        </div>
      )}
    </div>
  );
}
