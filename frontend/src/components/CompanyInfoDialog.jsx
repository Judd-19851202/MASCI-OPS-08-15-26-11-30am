import React, { useEffect, useState } from "react";
import { Building2 } from "lucide-react";
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
import { getCompanyInfo, saveCompanyInfo } from "@/lib/companyInfo";
import { toast } from "sonner";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2";

export const CompanyInfoDialog = ({ trigger }) => {
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState(getCompanyInfo());

  useEffect(() => {
    if (open) setInfo(getCompanyInfo());
  }, [open]);

  const set = (k, v) => setInfo((p) => ({ ...p, [k]: v }));

  const save = () => {
    saveCompanyInfo(info);
    toast.success("Company info saved — appears on every printed report");
    setOpen(false);
  };

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
            Appears on the print/PDF footer of every inspection report.
            Stored only on this device.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-3 py-2">
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Company Name
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
              Street Address
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
              City, State, ZIP
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
                Phone
              </Label>
              <Input
                value={info.phone}
                onChange={(e) => set("phone", e.target.value)}
                className={inputCls}
                placeholder="(555) 555-5555"
                data-testid="ci-phone"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Email
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
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                License #
              </Label>
              <Input
                value={info.license_number}
                onChange={(e) => set("license_number", e.target.value)}
                className={inputCls}
                placeholder="CGC1234567"
                data-testid="ci-license"
              />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                Website
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
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            data-testid="ci-cancel"
          >
            Cancel
          </Button>
          <Button
            onClick={save}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
            data-testid="ci-save"
          >
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
