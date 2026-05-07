import React, { useEffect, useState } from "react";
import { Building2, Phone, Lock } from "lucide-react";
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
    toast.success("Company info saved — appears on every printed report");
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
            <span className="hidden sm:inline">Company Info</span>
            <span className="sm:hidden">Info</span>
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg" data-testid="company-info-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl">
            Company Info
          </DialogTitle>
          <DialogDescription>
            {canEdit
              ? "Appears on the print/PDF footer of every safety report. Stored only on this device."
              : "Appears on every printed report. Admin only — sign in as admin to make changes."}
          </DialogDescription>
        </DialogHeader>

        {!canEdit && (
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-md bg-amber-50 border border-amber-300 text-amber-900 text-xs font-mono uppercase tracking-[0.15em]"
            data-testid="ci-readonly-banner"
          >
            <Lock className="w-3.5 h-3.5" />
            View only · Admin login required to edit
          </div>
        )}

        {/* Quick-call CTA — large red pill at the top of the dialog. Uses
            the tel: URI so a tap on phone dials, on desktop pops the user's
            default phone app. Disabled silently when no phone is set. */}
        {tel && (
          <a
            href={tel}
            className="group inline-flex items-center justify-center gap-2 h-14 mt-1 mb-2 rounded-md bg-red-700 hover:bg-red-800 text-white font-display font-black text-lg tracking-tight border-b-4 border-red-900 transition-colors"
            data-testid="ci-call-now"
          >
            <Phone className="w-5 h-5 group-hover:animate-pulse" />
            Call Office · {info.phone}
          </a>
        )}

        <div className="grid gap-3 py-2">
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Company Name
            </Label>
            <Input
              value={info.company_name}
              onChange={(e) => set("company_name", e.target.value)}
              className={canEdit ? inputCls : inputClsLocked}
              readOnly={!canEdit}
              tabIndex={canEdit ? 0 : -1}
              data-testid="ci-company-name"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Street Address
            </Label>
            <Input
              value={info.address}
              onChange={(e) => set("address", e.target.value)}
              className={canEdit ? inputCls : inputClsLocked}
              readOnly={!canEdit}
              tabIndex={canEdit ? 0 : -1}
              placeholder="123 Main St"
              data-testid="ci-address"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              City, State, ZIP
            </Label>
            <Input
              value={info.city_state_zip}
              onChange={(e) => set("city_state_zip", e.target.value)}
              className={canEdit ? inputCls : inputClsLocked}
              readOnly={!canEdit}
              tabIndex={canEdit ? 0 : -1}
              placeholder="Orlando, FL 32801"
              data-testid="ci-csz"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Office Phone
              </Label>
              <Input
                value={info.phone}
                onChange={(e) => set("phone", e.target.value)}
                className={canEdit ? inputCls : inputClsLocked}
                readOnly={!canEdit}
                tabIndex={canEdit ? 0 : -1}
                placeholder="(555) 555-5555"
                data-testid="ci-phone"
                inputMode="tel"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Email
              </Label>
              <Input
                value={info.email}
                onChange={(e) => set("email", e.target.value)}
                className={canEdit ? inputCls : inputClsLocked}
                readOnly={!canEdit}
                tabIndex={canEdit ? 0 : -1}
                placeholder="safety@masci.com"
                data-testid="ci-email"
              />
            </div>
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Website
            </Label>
            <Input
              value={info.website}
              onChange={(e) => set("website", e.target.value)}
              className={canEdit ? inputCls : inputClsLocked}
              readOnly={!canEdit}
              tabIndex={canEdit ? 0 : -1}
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
            {canEdit ? "Cancel" : "Close"}
          </Button>
          {canEdit && (
            <Button
              onClick={save}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
              data-testid="ci-save"
            >
              Save
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
