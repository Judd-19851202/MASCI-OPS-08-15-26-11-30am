/**
 * <TenantBrandingPanel>
 *
 * Track 15.66 Phase 2 — tenant-level sender / branding configuration.
 * Lets the operator change sender, reply-to, support email, and brand
 * strings without redeploying. The routing resolver picks up branding
 * changes through `email_routing_v2.invalidate_cache()` on save.
 *
 * Backed by:
 *   GET /api/admin/email-routing/v2/branding
 *   PUT /api/admin/email-routing/v2/branding
 */
import React, { useEffect, useState } from "react";
import { Building2, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useBranding } from "@/lib/BrandingProvider";

const FIELDS = [
  ["company_name", "Company name"],
  ["platform_display_name", "Platform display name"],
  ["sender_name", "Sender (from-name)"],
  ["from_email", "From email"],
  ["reply_to", "Reply-to email"],
  ["support_email", "Support email"],
  ["safety_email", "Safety email"],
  ["hr_email", "HR email"],
  ["operations_email", "Operations email"],
  ["primary_color", "Primary color (hex)"],
  ["logo_url", "Logo URL"],
];

export default function TenantBrandingPanel() {
  const [doc, setDoc] = useState(null);
  const [draft, setDraft] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { refresh: refreshBranding } = useBranding();

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/email-routing/v2/branding");
      setDoc(r?.data || {});
      setDraft(r?.data || {});
    } catch {
      toast.error("Failed to load branding");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      // Only send fields that changed
      const body = {};
      for (const [k] of FIELDS) {
        if (draft[k] !== (doc?.[k] ?? "")) body[k] = draft[k] ?? "";
      }
      if (Object.keys(body).length === 0) {
        toast.message("Nothing changed");
        return;
      }
      await api.put("/admin/email-routing/v2/branding", body);
      toast.success("Branding saved");
      await load();
      // Track 15.67 Phase 3 · live-refresh the global branding context so
      // every page picks up the new strings without a hard reload.
      try { await refreshBranding(); } catch { /* silent */ }
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Save failed";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      data-testid="tenant-branding-panel"
      className="rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <header className="px-5 py-4 border-b border-slate-200 flex items-center gap-2">
        <Building2 className="h-4 w-4 text-rose-600" />
        <div className="flex-1">
          <h2 className="text-base font-semibold text-slate-900">
            Tenant Branding · sender + support identity
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Main source for sender / reply-to / support text across email,
            PDFs, and help text. Current source: <span className="font-mono">{doc?.source || "env_defaults"}</span>
          </p>
        </div>
      </header>
      {loading ? (
        <div className="p-8 flex items-center justify-center text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          {FIELDS.map(([key, label]) => (
            <label key={key} className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
              {label}
              <Input
                type="text"
                value={draft[key] || ""}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, [key]: e.target.value }))
                }
                placeholder={key.includes("email") ? "name@yourcompany.com" : ""}
                className="mt-1 text-[12px] font-mono"
                data-testid={`branding-field-${key}`}
              />
            </label>
          ))}
          <div className="md:col-span-2 flex justify-end pt-2">
            <Button
              size="sm"
              onClick={save}
              disabled={saving}
              data-testid="branding-save"
            >
              {saving ? (
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
              ) : (
                <Save className="h-3 w-3 mr-1" />
              )}
              Save branding
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
