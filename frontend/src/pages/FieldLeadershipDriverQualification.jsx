// iter353b · Field Leadership Portal · Driver Readiness page.
// iter353d · row click opens FL Accountability Mini-Widget drawer.
// UXS-11E: wrapped in PortalShell (Field Leadership Portal).
import React, { useState } from "react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { PortalShell } from "@/design-system";
import DriverQualificationReadOnlyView from "@/components/DriverQualificationReadOnlyView";
import FlAccountabilityWidget from "@/components/FlAccountabilityWidget";
import { getFlToken } from "@/lib/flAuth";
import { useT } from "@/lib/i18n";

export default function FieldLeadershipDriverQualification() {
  const { t } = useT();
  const [drawerEmp, setDrawerEmp] = useState(null);
  const authHeaders = () => ({ "X-FL-Token": getFlToken() || "" });

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Field Leadership · Driver Readiness"
      pageTitle={t("Driver Qualification")}
      subtitle={t("Field Leadership read-only view of approved drivers and CDL readiness.")}
      showBack
      backHref="/field-leadership/portal/dashboard"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5" data-testid="fl-driver-qualification-page">
        <DriverQualificationReadOnlyView
          endpoint="/field-leadership/portal/driver-qualification"
          authHeaders={authHeaders}
          accent="red"
          testidPrefix="dq-fl"
          onRowClick={(emp) => setDrawerEmp(emp)}
        />
      </div>

      {/* iter353d · accountability mini-widget drawer */}
      <Sheet open={!!drawerEmp} onOpenChange={(v) => !v && setDrawerEmp(null)}>
        <SheetContent side="right" className="w-full sm:max-w-md p-0" data-testid="fl-widget-drawer">
          <SheetTitle className="sr-only">Employee Accountability</SheetTitle>
          {drawerEmp ? (
            <div className="p-4 h-full overflow-y-auto">
              <FlAccountabilityWidget employeeId={drawerEmp.id} onClose={() => setDrawerEmp(null)} />
            </div>
          ) : null}
        </SheetContent>
      </Sheet>
    </PortalShell>
  );
}
