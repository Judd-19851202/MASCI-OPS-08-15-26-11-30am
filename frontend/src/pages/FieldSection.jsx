// iter319 · Field Hub Calm Pass (Platform UX Governance Phase A).
//
// Apply the iter317-C / iter318 / iter319-FL calm pattern: left-edge
// stripe tiles, H1 toned down to interior-hub size, three lightweight
// operational groups (Daily Ops · Weekly Checks · Tools). NO sidebar,
// NO IA redesign, NO route changes. All 6 tile testids preserved.

import React from "react";
import {
  ClipboardList, Wrench, HardHat, Calculator, Truck, Send,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import { PortalShell } from "@/design-system/PortalShell";
import { InformationCard, ModuleCard, WorkflowCard } from "@/components/CanonicalCard";
import { SectionHeading } from "@/components/SectionHeading";

const FIELD_GROUPS = {
  reporting: [
    {
      to: "/daily/submit",
      icon: ClipboardList,
      title: "Daily Reports",
      description: "End-of-day site log covering crews, subs, visitors, equipment, materials, weather, and jobsite photos.",
      tone: "red",
      ctaLabel: "Start report",
      testId: "field-tile-daily",
      Card: ModuleCard,
    },
  ],
  equipment: [
    {
      to: "/equipment/submit",
      icon: Wrench,
      title: "Equipment Pre-Op",
      description: "Daily heavy-equipment readiness check with pass/fail inspection items and direct out-of-service visibility.",
      tone: "slate",
      ctaLabel: "Start inspection",
      testId: "field-tile-equipment",
      Card: WorkflowCard,
    },
  ],
  trucking: [
    {
      to: "/shift",
      icon: Send,
      title: "Driver Shift Start",
      description: "Start the shift fast by selecting the driver and truck with no password or app handoff.",
      tone: "amber",
      ctaLabel: "Start shift",
      testId: "field-tile-shift-start",
      Card: WorkflowCard,
    },
    {
      to: "/fleet/dvir/new",
      icon: Truck,
      title: "Trucking · Daily DVIR",
      description: "Daily truck and trailer inspection with direct defect visibility for shop operations.",
      tone: "amber",
      ctaLabel: "Start DVIR",
      testId: "field-tile-dvir",
      Card: WorkflowCard,
    },
    {
      to: "/fleet/weekly-lead/new",
      icon: Truck,
      title: "Weekly · Lead Inspection",
      description: "Weekly high-signal review for recurring issues, operational hygiene, and key safety items.",
      tone: "amber",
      ctaLabel: "Start weekly lead",
      testId: "field-tile-weekly-lead",
      Card: WorkflowCard,
    },
    {
      to: "/fleet/weekly-emergency/new",
      icon: Truck,
      title: "Weekly · Emergency Equipment",
      description: "Verify emergency gear, dates, readiness, and presence before the truck leaves the yard.",
      tone: "amber",
      ctaLabel: "Start emergency check",
      testId: "field-tile-weekly-emergency",
      Card: WorkflowCard,
    },
  ],
  tools: [
    {
      to: "/field/calculators",
      icon: Calculator,
      title: "Material Calculators",
      description: "Estimate aggregate, asphalt, concrete, truck loads, yield, waste, and conversions without leaving the field.",
      tone: "blue",
      ctaLabel: "Open tools",
      testId: "field-tile-calculators",
      Card: InformationCard,
    },
  ],
};

/**
 * FieldSection — landing for the /field sub-hub. Daily operational logs
 * used by crews and operators at the start/end of every shift.
 */
export default function FieldSection() {
  const { t } = useT();

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Field"
      pageTitle={t("Field")}
      homeHref="/field"
      backHref="/"
      showBack
      showSearch={false}
      showNotifications={false}
      showPortalSwitcher={false}
      showSignOut={false}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        <InformationCard
          icon={HardHat}
          tone="amber"
          title={t("Field Operations")}
          description={t("Start the shift, log field work, confirm equipment readiness, and open jobsite tools from one governed crew-facing surface.")}
          eyebrow={t("Crew start point")}
          testId="field-section-summary"
          className="mb-8"
        />

        <div className="space-y-10 mb-12">
          <section data-testid="field-group-reporting">
            <SectionHeading
              index="01"
              title={t("Field Reporting")}
              subtitle={t("End-of-day operational memory for the jobsite.")}
              testId="field-group-heading-reporting"
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
              {FIELD_GROUPS.reporting.map(({ Card, title, description, ctaLabel, ...card }) => (
                <Card
                  key={card.testId}
                  title={t(title)}
                  description={t(description)}
                  ctaLabel={t(ctaLabel)}
                  {...card}
                />
              ))}
            </div>
          </section>

          <section data-testid="field-group-equipment">
            <SectionHeading
              index="02"
              title={t("Equipment Operations")}
              subtitle={t("Daily OSHA equipment readiness before production starts.")}
              testId="field-group-heading-equipment"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {FIELD_GROUPS.equipment.map(({ Card, title, description, ctaLabel, ...card }) => (
                <Card
                  key={card.testId}
                  title={t(title)}
                  description={t(description)}
                  ctaLabel={t(ctaLabel)}
                  {...card}
                />
              ))}
            </div>
          </section>

          <section data-testid="field-group-trucking">
            <SectionHeading
              index="03"
              title={t("Trucking Operations")}
              subtitle={t("Shift activation, daily readiness, and recurring truck checks.")}
              testId="field-group-heading-trucking"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {FIELD_GROUPS.trucking.map(({ Card, title, description, ctaLabel, ...card }) => (
                <Card
                  key={card.testId}
                  title={t(title)}
                  description={t(description)}
                  ctaLabel={t(ctaLabel)}
                  {...card}
                />
              ))}
            </div>
          </section>

          <section
            data-testid="field-group-tools"
            className="pt-6 border-t border-slate-200"
          >
            <SectionHeading
              index="04"
              title={t("Calculators & Tools")}
              subtitle={t("Supporting field calculators and quick utilities.")}
              testId="field-group-heading-tools"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {FIELD_GROUPS.tools.map(({ Card, title, description, ctaLabel, ...card }) => (
                <Card
                  key={card.testId}
                  title={t(title)}
                  description={t(description)}
                  ctaLabel={t(ctaLabel)}
                  {...card}
                />
              ))}
            </div>
          </section>
        </div>
      </div>
    </PortalShell>
  );
}
