import React, { useEffect, useState } from "react";
import { Mail, Save, Loader2, RotateCcw, Send, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { sanitizeOperatorError, sanitizeOperatorReference } from "@/lib/operatorLanguage";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

/**
 * <AdminEmailRoutingPanel>
 *
 * Lets the admin edit "who gets what email" without a redeploy.
 * 6 routing keys (5 lists + 1 single email) overlay the env-derived
 * defaults. Each row shows: the live value, the env default, and a
 * "Reset to default" button. Save persists via PUT /api/admin/email-routing.
 *
 * Backend reads via email_routing.load(db) which caches 60s; we
 * invalidate on every save so admin edits take effect immediately.
 */

const ROUTES = [
  {
    key: "always_cc",
    label: "Compliance always-CC",
    type: "list",
    description:
      "Office addresses CC'd on every Site Inspection, Toolbox Meeting, JHA, Incident Report, and QA/QC Inspection. Goes after the assigned PM and any co-PMs.",
  },
  {
    key: "safety_forms_to",
    label: "Safety Forms To: list",
    type: "list",
    description:
      "Recipients for Safety Equipment Issuance, Use & Care Training, and Equipment Check-In/Return Receipt PDFs.",
  },
  {
    key: "leadership_always_to",
    label: "Field Leadership always-CC",
    type: "list",
    description:
      "Always copied on every Field Leadership form (write-up, coaching, equipment checkout/return, supervisor notes, etc.). Joins the assigned PM in the To: field.",
  },
  {
    key: "severe_incident_cc",
    label: "Severe Incident extra-CC",
    type: "list",
    description:
      "Additional addresses appended ONLY when an incident is flagged as Severe (recordable, hospitalization, fatality, or work stopped). Set to empty to silence the fan-out.",
  },
  {
    key: "shop_manager_fallback",
    label: "Shop Manager fallback (single email)",
    type: "single",
    description:
      "Used as the recipient on Pre-Op FAIL emails when there are zero active mechanics in the Shop Users panel. After you seed shop users this fallback is rarely used.",
  },
  {
    key: "backup_email_to",
    label: "Daily backup destination",
    type: "list",
    description:
      "Recipients of the auto-backup zip (02:00 + 18:00 platform time) and the manual 'Backup + email + download NOW' button. Typically a single ops/IT address.",
  },
];

function listToText(list) {
  return Array.isArray(list) ? list.join(", ") : "";
}
function textToList(text) {
  return (text || "")
    .split(/[,;\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function AdminEmailRoutingPanel() {
  const [config, setConfig] = useState(null);
  const [envDefaults, setEnvDefaults] = useState(null);
  const [drafts, setDrafts] = useState({}); // key -> string (textarea value)
  const [busy, setBusy] = useState(false);
  const [savingKey, setSavingKey] = useState("");
  const [testTo, setTestTo] = useState("");
  const [testBusy, setTestBusy] = useState(false);

  const load = async () => {
    try {
      const res = await api.get("/admin/email-routing");
      setConfig(res.data.config);
      setEnvDefaults(res.data.env_defaults);
      // Seed drafts from current config so the textareas show what's live.
      const next = {};
      for (const r of ROUTES) {
        const v = res.data.config[r.key];
        next[r.key] = r.type === "list" ? listToText(v) : (v || "");
      }
      setDrafts(next);
    } catch {
      toast.error("Failed to load routing settings");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const saveOne = async (key) => {
    const route = ROUTES.find((r) => r.key === key);
    const value =
      route.type === "list" ? textToList(drafts[key] || "") : (drafts[key] || "").trim();
    setSavingKey(key);
    setBusy(true);
    try {
      const res = await api.put("/admin/email-routing", { [key]: value });
      setConfig(res.data.config);
      toast.success(`Saved · ${sanitizeOperatorReference(route.label, "routing rule")}`);
    } catch (e) {
      toast.error(`Save failed: ${sanitizeOperatorError(e?.response?.data?.detail || e.message, "Please review this routing rule and try again.")}`);
    } finally {
      setBusy(false);
      setSavingKey("");
    }
  };

  const resetOne = (key) => {
    if (!envDefaults) return;
    const route = ROUTES.find((r) => r.key === key);
    const def = envDefaults[key];
    const text = route.type === "list" ? listToText(def) : (def || "");
    setDrafts((p) => ({ ...p, [key]: text }));
    toast.message("Reset to shared default — click Save to keep this change");
  };

  const sendTest = async () => {
    if (!testTo.trim()) {
      toast.error("Enter an address to test");
      return;
    }
    setTestBusy(true);
    try {
      const res = await api.post("/admin/email-routing/test", { to: testTo.trim() });
      toast.success(`Test email sent to ${res.data.to}`);
    } catch (e) {
      toast.error(`Test failed: ${sanitizeOperatorError(e?.response?.data?.detail || e.message, "The test message could not be sent.")}`);
    } finally {
      setTestBusy(false);
    }
  };

  if (!config) {
    return (
      <section
        className="bg-white border border-slate-200 rounded p-6"
        data-testid="admin-email-routing-panel"
      >
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading email routing…
        </div>
      </section>
    );
  }

  const meta = config._meta || {};
  return (
    <section
      className="bg-white border border-slate-200 rounded shadow-sm"
      data-testid="admin-email-routing-panel"
    >
      <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-3">
        <Mail className="w-5 h-5 text-red-700" />
        <div>
          <h2 className="font-display text-xl font-black text-slate-900">
            Email Routing
          </h2>
          <p className="text-xs text-slate-600 mt-0.5">
            Update who receives automatic emails on every form without leaving this page.
            Empty list = silence. Comma, semicolon, or newline-separate addresses.
          </p>
        </div>
        <span
          className={`ml-auto px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider ${
            meta.source === "db"
              ? "bg-amber-100 text-amber-800 border border-amber-300"
              : "bg-slate-100 text-slate-600 border border-slate-300"
          }`}
          data-testid="routing-source-badge"
        >
          {meta.source === "db" ? "Saved custom rules" : "Shared defaults"}
        </span>
      </div>

      <div className="divide-y divide-slate-100">
        {ROUTES.map((r) => {
          const liveValue =
            r.type === "list" ? listToText(config[r.key]) : (config[r.key] || "");
          const envValue =
            r.type === "list" ? listToText(envDefaults?.[r.key]) : (envDefaults?.[r.key] || "");
          const draft = drafts[r.key] ?? "";
          const dirty = draft.trim() !== liveValue.trim();
          const isOverride =
            (r.type === "list" ? listToText(config[r.key]).toLowerCase() : (config[r.key] || "").toLowerCase())
            !== envValue.toLowerCase();

          return (
            <div key={r.key} className="px-5 py-4" data-testid={`routing-row-${r.key}`}>
              <div className="flex items-start justify-between gap-3 mb-2 flex-wrap">
                <div className="flex-1 min-w-[250px]">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-slate-900 text-sm">{r.label}</h3>
                    {isOverride && (
                      <span className="text-[9px] uppercase font-mono tracking-wider bg-amber-100 border border-amber-300 text-amber-800 px-1.5 py-0.5 rounded">
                        Override
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{sanitizeOperatorReference(r.description, "Update who receives this message.")}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => resetOne(r.key)}
                    disabled={busy}
                    data-testid={`routing-reset-${r.key}`}
                    title={`Reset to shared default: ${envValue || "(empty)"}`}
                  >
                    <RotateCcw className="w-3.5 h-3.5 mr-1" /> Default
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => saveOne(r.key)}
                    disabled={busy || !dirty}
                    className={
                      dirty
                        ? "bg-red-700 hover:bg-red-800 text-white"
                        : "bg-slate-200 text-slate-500"
                    }
                    data-testid={`routing-save-${r.key}`}
                  >
                    {savingKey === r.key ? (
                      <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                    ) : (
                      <Save className="w-3.5 h-3.5 mr-1" />
                    )}
                    Save
                  </Button>
                </div>
              </div>
              {r.type === "list" ? (
                <textarea
                  value={draft}
                  onChange={(e) => setDrafts((p) => ({ ...p, [r.key]: e.target.value }))}
                  className="w-full font-mono text-xs border border-slate-300 rounded p-2 h-16 focus:ring-2 focus:ring-red-700 focus:border-red-700 outline-none"
                  placeholder="email1@example.com, email2@example.com"
                  spellCheck={false}
                  data-testid={`routing-input-${r.key}`}
                />
              ) : (
                <Input
                  value={draft}
                  onChange={(e) => setDrafts((p) => ({ ...p, [r.key]: e.target.value }))}
                  className="font-mono text-xs"
                  placeholder="single@example.com"
                  spellCheck={false}
                  data-testid={`routing-input-${r.key}`}
                />
              )}
              <div className="text-[10px] font-mono text-slate-400 mt-1 truncate">
                Shared default: {envValue || "(empty)"}
              </div>
            </div>
          );
        })}
      </div>

      {/* Test email row */}
      <div className="px-5 py-4 border-t-2 border-slate-200 bg-slate-50">
        <div className="flex items-start gap-3 flex-wrap">
          <div className="flex-1 min-w-[240px]">
            <h3 className="font-bold text-slate-900 text-sm">Send test email</h3>
            <p className="text-xs text-slate-600 mt-0.5">
              Sends a one-off message to confirm delivery before you add an address to a routing list above.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Input
              value={testTo}
              onChange={(e) => setTestTo(e.target.value)}
              placeholder="test-recipient@example.com"
              className="font-mono text-xs w-72"
              data-testid="routing-test-input"
            />
            <Button
              type="button"
              size="sm"
              onClick={sendTest}
              disabled={testBusy || !testTo.trim()}
              className="bg-emerald-700 hover:bg-emerald-800 text-white"
              data-testid="routing-test-send"
            >
              {testBusy ? (
                <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5 mr-1" />
              )}
              Send test
            </Button>
          </div>
        </div>
        {meta.updated_at && (
          <div className="text-[10px] font-mono text-slate-400 mt-2 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Last updated: {formatPlatformTime(meta.updated_at)} by {meta.updated_by || "—"}
          </div>
        )}
        {meta.source !== "db" && (
          <div className="text-[10px] font-mono text-slate-500 mt-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            No DB overrides yet — every list is using its env default.
          </div>
        )}
      </div>
    </section>
  );
}
