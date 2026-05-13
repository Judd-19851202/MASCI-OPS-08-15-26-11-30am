import React, { useEffect, useState } from "react";
import { Building2, Phone } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getCompanyInfo,
  saveCompanyInfo,
  buildTelHref,
} from "@/lib/companyInfo";
import { isAdmin } from "@/lib/adminAuth";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";
const inputClsLocked =
  "h-12 text-base border-2 border-slate-200 bg-slate-50 text-slate-700 cursor-not-allowed";

/**
 * Edit gate — only an authenticated admin in THIS browser may change
 * Company Info (it prints on every PDF footer + watermark, so a stray
 * field-worker edit corrupts every report they generate from that device).
 *
 * The dialog is rendered in 8 places (Hub, FieldSection, SafetySection,
 * Dashboard, SafetyFormsHub, AdminHub, PmHub, plus a couple of record
 * viewers). To keep call-sites unchanged, we detect the admin token via
 * `isAdmin()` rather than threading a prop through every mount point.
 * Callers can still force-unlock with `editable={true}` if needed.
 */

export const CompanyInfoDialog = ({ trigger, editable }) => {
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState(getCompanyInfo());
  const [canEdit, setCanEdit] = useState(false);
  const { t } = useT();

  useEffect(() => {
    if (open) {
      setInfo(getCompanyInfo());
      setCanEdit(editable ?? isAdmin());
    }
  }, [open, editable]);

  const set = (k, v) => setInfo((p) => ({ ...p, [k]: v }));

  const save = () => {
    if (!canEdit) return;
    saveCompanyInfo(info);
    toast.success(t("Company info saved — appears on every printed report"));
    setOpen(false);
  };

  const tel = buildTelHref(info.phone);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button
            variant="outline"
            className="h-12 sm:h-14 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 hover:text-white font-bold uppercase tracking-wide text-sm"
            data-testid="company-info-btn"
          >
            <Building2 className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">{t("Company Info")}</span>
            <span className="sm:hidden">{t("Info")}</span>
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg" data-testid="company-info-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl">
            {canEdit ? t("Company Info") : t("Need Help?")}
          </DialogTitle>
          <DialogDescription>
            {canEdit
              ? t("Appears on the print/PDF footer of every safety report. Stored only on this device.")
              : t("Office phone, address, and after-hours contact for MASCI General Contractors Inc.")}
          </DialogDescription>
        </DialogHeader>

        {/* Quick-call CTA — large red pill. Same for everyone. */}
        {tel && (
          <a
            href={tel}
            className="group inline-flex items-center justify-center gap-2 h-14 mt-1 mb-2 rounded-md bg-red-700 hover:bg-red-800 text-white font-display font-black text-lg tracking-tight border-b-4 border-red-900 transition-colors"
            data-testid="ci-call-now"
          >
            <Phone className="w-5 h-5 group-hover:animate-pulse" />
            {t("Call Office")} · {info.phone}
          </a>
        )}

        {canEdit ? (
          // ── Admin edit form ────────────────────────────────────────
          <>
            <div className="grid gap-3 py-2">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Company Name")}
                </Label>
                <Input
                  value={info.company_name}
                  onChange={(e) => set("company_name", e.target.value)}
                  className={inputCls}
                  data-testid="ci-company-name"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Street Address")}
                </Label>
                <Input
                  value={info.address}
                  onChange={(e) => set("address", e.target.value)}
                  className={inputCls}
                  placeholder="123 Main St"
                  data-testid="ci-address"
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("City, State, ZIP")}
                </Label>
                <Input
                  value={info.city_state_zip}
                  onChange={(e) => set("city_state_zip", e.target.value)}
                  className={inputCls}
                  placeholder="Orlando, FL 32801"
                  data-testid="ci-csz"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                    {t("Office Phone")}
                  </Label>
                  <Input
                    value={info.phone}
                    onChange={(e) => set("phone", e.target.value)}
                    className={inputCls}
                    placeholder="(555) 555-5555"
                    data-testid="ci-phone"
                    inputMode="tel"
                  />
                </div>
                <div>
                  <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                    {t("Email")}
                  </Label>
                  <Input
                    value={info.email}
                    onChange={(e) => set("email", e.target.value)}
                    className={inputCls}
                    placeholder="safety@masci.com"
                    data-testid="ci-email"
                  />
                </div>
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Website")}
                </Label>
                <Input
                  value={info.website}
                  onChange={(e) => set("website", e.target.value)}
                  className={inputCls}
                  placeholder="masci.com"
                  data-testid="ci-website"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setOpen(false)}
                data-testid="ci-cancel"
              >
                {t("Cancel")}
              </Button>
              <Button
                onClick={save}
                className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
                data-testid="ci-save"
              >
                {t("Save")}
              </Button>
            </DialogFooter>
          </>
        ) : (
          // ── Read-only contact card — business-card-style display ──
          <>
            <div className="space-y-3 py-2" data-testid="ci-readonly-card">
              <InfoRow
                label={t("Company")}
                value={info.company_name}
                testId="ci-display-company"
              />
              <InfoRow
                label={t("Address")}
                value={[info.address, info.city_state_zip].filter(Boolean).join(", ")}
                testId="ci-display-address"
              />
              <div className="grid grid-cols-2 gap-3">
                <InfoRow
                  label={t("Office Phone")}
                  value={info.phone}
                  testId="ci-display-phone"
                />
                <InfoRow
                  label={t("Website")}
                  value={info.website}
                  testId="ci-display-website"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setOpen(false)}
                data-testid="ci-cancel"
                className="w-full sm:w-auto"
              >
                {t("Close")}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

/** Plain read-only display row — looks like a business card, not a form. */
function InfoRow({ label, value, testId }) {
  if (!value) return null;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
        {label}
      </div>
      <div
        className="font-display text-base text-slate-900 leading-snug mt-0.5"
        data-testid={testId}
      >
        {value}
      </div>
    </div>
  );
}
