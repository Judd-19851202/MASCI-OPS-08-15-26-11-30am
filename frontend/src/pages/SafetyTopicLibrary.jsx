// SafetyTopicLibrary — F2-A · Safety/Admin Topic Library MVP (iter266).
//
// Lean operational tool · NOT an LMS · NOT a public library · NOT analytics.
// Lets Safety/Admin filter the 136-topic library by severity + domain,
// multi-select topics, choose EN / ES / Both, and download a server-rendered
// multi-topic PDF pack for mobilization prep.
//
// Scope discipline (per /app/memory/SAFETY_MEETING_POST_PHASE_H_EVAL_iter265.md §5
// and the operator's Operational Value Gate directive):
//   ✅ filter · multi-select · PDF download
//   ❌ no presets/saved packs (deferred to F2-B)
//   ❌ no analytics, no usage tracking, no recommendations
//   ❌ no engagement scoring, no "recently viewed", no favorites
//   ❌ no font/color/layout customization
//
// Severity rendering on this page is the ONLY surface in the entire app
// where severity is visible. Every other surface (NewMeeting, ViewMeeting,
// future F1 public library) keeps severity invisible.

import React, { useMemo, useState } from "react";
import { BookOpen, FileText, Loader2 } from "lucide-react";
import SafetyShell from "@/components/SafetyShell";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useT } from "@/lib/i18n";
import { HelpTipBlock } from "@/components/HelpTip";
import { usePageTitle } from "@/lib/usePageTitle";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { TOPIC_LIBRARY } from "@/lib/topics/index";
import { TOPIC_LIBRARY_ES } from "@/lib/topics/index.es";
import { toast } from "sonner";

// Domain chip labels — mirrors TopicPicker.jsx; kept duplicated to avoid
// importing a forms component into this admin page.
const DOMAIN_CHIPS = [
  { key: null, en: "All", es: "Todos" },
  { key: "pipe", en: "Pipe", es: "Tubería" },
  { key: "excavation", en: "Excavation", es: "Excavación" },
  { key: "grading", en: "Grading", es: "Movimiento" },
  { key: "concrete", en: "Concrete", es: "Concreto" },
  { key: "paving", en: "Paving", es: "Pavimento" },
  { key: "milling", en: "Milling", es: "Milling" },
  { key: "mot", en: "MOT / Traffic", es: "MOT / Tráfico" },
  { key: "trucking", en: "Trucking", es: "Camiones" },
  { key: "dewatering", en: "Dewatering", es: "Desagüe" },
  { key: "shop", en: "Shop", es: "Taller" },
  { key: "plant", en: "Plant", es: "Planta" },
  { key: "lab", en: "Lab", es: "Laboratorio" },
  { key: "airport", en: "Airport", es: "Aeropuerto" },
  { key: "utilities", en: "Utilities", es: "Servicios" },
  { key: "rigging", en: "Rigging / Crane", es: "Aparejo / Grúa" },
  { key: "fall_protection", en: "Fall Protection", es: "Caídas" },
  { key: "electrical", en: "Electrical", es: "Eléctrico" },
  { key: "confined_space", en: "Confined Space", es: "Esp. Confinado" },
  { key: "environmental", en: "Environmental", es: "Ambiental" },
  { key: "wellness", en: "Heat / Fatigue / MH", es: "Calor / Fatiga / SM" },
  { key: "office", en: "Office", es: "Oficina" },
  { key: "general", en: "General", es: "General" },
];

const SEVERITY_CHIPS = [
  {
    key: "fatal_risk",
    en: "Fatal-risk",
    es: "Riesgo fatal",
  },
  {
    key: "serious_injury",
    en: "Serious-injury",
    es: "Lesión grave",
  },
  {
    key: "lost_time",
    en: "Lost-time",
    es: "Tiempo perdido",
  },
];

const SEVERITY_BADGE_STYLE = {
  fatal_risk: "bg-red-50 text-red-700 ring-red-200",
  serious_injury: "bg-amber-50 text-amber-700 ring-amber-200",
  lost_time: "bg-slate-100 text-slate-600 ring-slate-200",
};

function severityLabel(sev, lang) {
  const chip = SEVERITY_CHIPS.find((s) => s.key === sev);
  if (!chip) return sev;
  return lang === "es" ? chip.es : chip.en;
}

function titleFor(topic, lang) {
  if (lang === "es" && TOPIC_LIBRARY_ES[topic.key]?.title) {
    return TOPIC_LIBRARY_ES[topic.key].title;
  }
  return topic.title;
}

function domainLabel(key, lang) {
  const chip = DOMAIN_CHIPS.find((d) => d.key === key);
  if (!chip) return key;
  return lang === "es" ? chip.es : chip.en;
}

export default function SafetyTopicLibrary() {
  const { t, lang } = useT();
  usePageTitle(t("Topic Library · MASCI Safety"));

  const [severityFilters, setSeverityFilters] = useState(new Set());
  const [domainFilter, setDomainFilter] = useState(null);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(new Set());
  const [packOpen, setPackOpen] = useState(false);
  const [packLanguage, setPackLanguage] = useState(lang || "en");
  const [generating, setGenerating] = useState(false);

  // Filtered topic list.
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return TOPIC_LIBRARY.filter((topic) => {
      if (severityFilters.size > 0 && !severityFilters.has(topic.severity)) {
        return false;
      }
      if (domainFilter && topic.domain !== domainFilter) return false;
      if (q) {
        const enTitle = (topic.title || "").toLowerCase();
        const esTitle = (TOPIC_LIBRARY_ES[topic.key]?.title || "").toLowerCase();
        if (!enTitle.includes(q) && !esTitle.includes(q)) return false;
      }
      return true;
    });
  }, [severityFilters, domainFilter, search]);

  const severityCounts = useMemo(() => {
    const counts = { fatal_risk: 0, serious_injury: 0, lost_time: 0 };
    TOPIC_LIBRARY.forEach((tt) => {
      if (tt.severity in counts) counts[tt.severity]++;
    });
    return counts;
  }, []);

  const domainCounts = useMemo(() => {
    const counts = { __all: TOPIC_LIBRARY.length };
    TOPIC_LIBRARY.forEach((tt) => {
      counts[tt.domain] = (counts[tt.domain] || 0) + 1;
    });
    return counts;
  }, []);

  function toggleSeverity(key) {
    setSeverityFilters((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleSelect(topicKey) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(topicKey)) next.delete(topicKey);
      else next.add(topicKey);
      return next;
    });
  }

  function selectAllVisible() {
    setSelected(new Set(filtered.map((tt) => tt.key)));
  }

  function clearSelection() {
    setSelected(new Set());
  }

  function openPackDialog() {
    if (selected.size === 0) {
      toast.error(t("Select at least one topic before generating a pack."));
      return;
    }
    setPackLanguage(lang === "es" ? "es" : "en");
    setPackOpen(true);
  }

  async function generatePack() {
    const selectedTopics = TOPIC_LIBRARY.filter((tt) => selected.has(tt.key));
    if (selectedTopics.length === 0) {
      toast.error(t("Select at least one topic before generating a pack."));
      return;
    }
    const payload = {
      languages: packLanguage,
      topics: selectedTopics.map((tt) => {
        const es = TOPIC_LIBRARY_ES[tt.key];
        const enContent = {
          key: tt.key,
          domain: tt.domain,
          title: tt.title,
          severity: tt.severity,
          incident_pattern: tt.incident_pattern || "",
          hazards_reviewed: tt.hazards_reviewed || "",
          discussion_notes: tt.discussion_notes || "",
          references_cited: tt.references_cited || "",
          action_items: tt.action_items || "",
        };
        const esContent = es
          ? {
              key: tt.key,
              domain: tt.domain,
              title: es.title || tt.title,
              severity: tt.severity,
              incident_pattern: es.incident_pattern || "",
              hazards_reviewed: es.hazards_reviewed || "",
              discussion_notes: es.discussion_notes || "",
              references_cited: es.references_cited || "",
              action_items: es.action_items || "",
            }
          : null;
        return { en: enContent, es: esContent };
      }),
    };

    setGenerating(true);
    try {
      const headers = { "Content-Type": "application/json" };
      const safetyTok = getSafetyToken();
      const adminTok = getAdminToken();
      if (safetyTok) headers["X-Safety-Token"] = safetyTok;
      else if (adminTok) headers["X-Admin-Token"] = adminTok;

      const resp = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/safety/library/pack`,
        {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        },
      );
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${txt}`);
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const stamp = new Date().toISOString().slice(0, 10);
      a.download = `MASCI_Safety_Topic_Pack_${stamp}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(
        t("PDF pack generated · {n} topic(s)").replace(
          "{n}",
          selectedTopics.length,
        ),
      );
      setPackOpen(false);
    } catch (e) {
      toast.error(t("PDF generation failed: ") + (e?.message || "unknown"));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <SafetyShell>
      <div className="space-y-6" data-testid="safety-topic-library-root">
        <header className="space-y-2">
          <div className="flex items-center gap-2 text-slate-500 text-sm uppercase tracking-wider">
            <BookOpen className="h-4 w-4" />
            <span>{t("Safety / Admin")}</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900">
            {t("Topic Library · Operational Prep")}
          </h1>
          <p className="text-sm text-slate-600 max-w-3xl">
            {t(
              "Filter the 136-topic safety library by severity and domain. Pick the topics you need, choose the language, and generate a PDF pack. For kickoffs, mobilizations, and high-risk job prep — not for distribution outside MASCI Safety/Admin.",
            )}
          </p>
        </header>

        {/* iter275 · page-root coaching · canonical 4 kinds */}
        <HelpTipBlock formKey="topic-library" className="-mt-2" showCounter />

        {/* Filters */}
        <section
          className="bg-white rounded-2xl border border-slate-200 p-4 space-y-4"
          data-testid="library-filters"
        >
          {/* iter275 · filter coaching · why filtering drives selection */}
          <HelpTipBlock formKey="topic-library.filter" />
          <div className="space-y-2">
            <Label className="text-xs uppercase tracking-wider text-slate-500">
              {t("Severity")} ·{" "}
              <span className="text-slate-400 italic normal-case">
                {t(
                  "Safety/Admin operational metadata · not for field display",
                )}
              </span>
            </Label>
            <div className="flex flex-wrap gap-2">
              {SEVERITY_CHIPS.map((sev) => {
                const active = severityFilters.has(sev.key);
                return (
                  <button
                    key={sev.key}
                    type="button"
                    onClick={() => toggleSeverity(sev.key)}
                    data-testid={`sev-chip-${sev.key}`}
                    className={`px-3 py-1.5 rounded-full text-sm ring-1 transition ${
                      active
                        ? `${SEVERITY_BADGE_STYLE[sev.key]} ring-current`
                        : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {lang === "es" ? sev.es : sev.en}
                    <span className="ml-2 text-xs opacity-70">
                      {severityCounts[sev.key]}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-xs uppercase tracking-wider text-slate-500">
              {t("Domain")}
            </Label>
            <div className="flex flex-wrap gap-2">
              {DOMAIN_CHIPS.map((d) => {
                const active = domainFilter === d.key;
                const count =
                  d.key === null ? domainCounts.__all : domainCounts[d.key] || 0;
                return (
                  <button
                    key={d.key || "__all"}
                    type="button"
                    onClick={() => setDomainFilter(d.key)}
                    data-testid={`domain-chip-${d.key || "all"}`}
                    className={`px-3 py-1.5 rounded-full text-sm ring-1 transition ${
                      active
                        ? "bg-slate-900 text-white ring-slate-900"
                        : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {lang === "es" ? d.es : d.en}
                    <span className="ml-2 text-xs opacity-70">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-2 items-center">
            <Input
              placeholder={t("Search by title (EN or ES)…")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              data-testid="library-search"
            />
            <Button
              type="button"
              variant="outline"
              onClick={selectAllVisible}
              data-testid="library-select-all"
            >
              {t("Select all visible")} ({filtered.length})
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={clearSelection}
              disabled={selected.size === 0}
              data-testid="clear-selection"
            >
              {t("Clear selection")}
            </Button>
          </div>
        </section>

        {/* Selection summary + Generate */}
        <section
          className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 rounded-xl border border-slate-200 px-4 py-3"
          data-testid="library-selection-bar"
        >
          <div className="text-sm text-slate-700">
            <strong data-testid="selection-count">{selected.size}</strong>{" "}
            {t("topics selected")} · {filtered.length} {t("shown")}
          </div>
          <Button
            type="button"
            onClick={openPackDialog}
            disabled={selected.size === 0}
            data-testid="open-pack-dialog"
            className="bg-red-700 hover:bg-red-800 text-white"
          >
            <FileText className="h-4 w-4 mr-2" />
            {t("Generate PDF Pack")}
          </Button>
        </section>

        {/* Results list */}
        {filtered.length === 0 ? (
          <div
            className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500"
            data-testid="library-empty"
          >
            <p className="text-sm">
              {t("No topics match the current filters.")}
            </p>
            <p className="text-xs mt-1">
              {t("Try clearing severity, domain, or search.")}
            </p>
          </div>
        ) : (
          <ul
            className="space-y-2"
            data-testid="library-list"
          >
            {filtered.map((topic) => {
              const isSelected = selected.has(topic.key);
              return (
                <li
                  key={topic.key}
                  data-testid={`library-row-${topic.key}`}
                  className={`bg-white rounded-xl border p-3 sm:p-4 flex items-start gap-3 transition ${
                    isSelected
                      ? "border-red-300 ring-2 ring-red-100"
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleSelect(topic.key)}
                    data-testid={`row-select-${topic.key}`}
                    className="mt-1"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center flex-wrap gap-2 mb-1">
                      <span className="text-[10px] uppercase tracking-wider text-slate-500">
                        {domainLabel(topic.domain, lang)}
                      </span>
                      <span
                        data-testid={`sev-badge-${topic.key}`}
                        className={`text-[10px] px-2 py-0.5 rounded-full ring-1 ${
                          SEVERITY_BADGE_STYLE[topic.severity] ||
                          "bg-slate-100 text-slate-600 ring-slate-200"
                        }`}
                      >
                        {severityLabel(topic.severity, lang)}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleSelect(topic.key)}
                      className="text-left w-full"
                    >
                      <p className="font-semibold text-slate-900 leading-snug">
                        {titleFor(topic, lang)}
                      </p>
                      {topic.incident_pattern && (
                        <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                          {topic.incident_pattern.slice(0, 220)}
                          {topic.incident_pattern.length > 220 ? "…" : ""}
                        </p>
                      )}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        {/* Pack-generation dialog */}
        <Dialog open={packOpen} onOpenChange={setPackOpen}>
          <DialogContent data-testid="pack-dialog">
            <DialogHeader>
              <DialogTitle>{t("Generate PDF Pack")}</DialogTitle>
              <DialogDescription>
                {t("Choose the language for the generated pack.")} ·{" "}
                {selected.size} {t("topics selected")}
              </DialogDescription>
            </DialogHeader>
            {/* iter275 · pack coaching · live-generation discipline */}
            <HelpTipBlock formKey="topic-library.pdf-pack" className="mb-2" />
            <div className="space-y-2">
              {[
                { v: "en", label: t("English only") },
                { v: "es", label: t("Spanish only") },
                {
                  v: "both",
                  label: t("Both languages (EN page · ES page · per topic)"),
                },
              ].map((opt) => (
                <label
                  key={opt.v}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition ${
                    packLanguage === opt.v
                      ? "border-red-300 bg-red-50"
                      : "border-slate-200 hover:bg-slate-50"
                  }`}
                  data-testid={`pack-lang-${opt.v}`}
                >
                  <input
                    type="radio"
                    name="pack-language"
                    value={opt.v}
                    checked={packLanguage === opt.v}
                    onChange={() => setPackLanguage(opt.v)}
                    className="accent-red-700"
                  />
                  <span className="text-sm text-slate-800">{opt.label}</span>
                </label>
              ))}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setPackOpen(false)}
                disabled={generating}
              >
                {t("Cancel")}
              </Button>
              <Button
                type="button"
                onClick={generatePack}
                disabled={generating}
                data-testid="confirm-generate"
                className="bg-red-700 hover:bg-red-800 text-white"
              >
                {generating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {t("Generating…")}
                  </>
                ) : (
                  t("Generate")
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </SafetyShell>
  );
}
