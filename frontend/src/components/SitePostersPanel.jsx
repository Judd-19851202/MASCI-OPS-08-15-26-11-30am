import React from "react";
import { Link } from "react-router-dom";
import {
  Printer,
  ExternalLink,
  ClipboardCheck,
  Box,
  FileText,
  PrinterCheck,
  GraduationCap,
} from "lucide-react";
import { useT } from "@/lib/i18n";

/**
 * Site Posters Panel — Admin Hub section listing every printable handout
 * MASCI uses on jobsites. Each row gives the office staff a one-click
 * "Open" (preview) button + a "Print" button (?autoprint=1) so they can
 * batch-print before each quarterly safety refresh.
 *
 * The "Print All Posters" button at the bottom navigates to the combined
 * /admin/posters/print-all?autoprint=1 page, which stacks the 3 cards
 * with page-break-after so a single Cmd+P → 3 letter-size sheets.
 */
const POSTERS = (t) => [
  {
    id: "cheatsheet",
    title: t("Crew Cheat Sheet"),
    desc: t("Foreman handout. QR to the Hub + 4-step submit flow + stop-the-line rules."),
    where: t("Post inside every site trailer."),
    accent: "border-red-700 bg-red-700",
    Icon: ClipboardCheck,
    open: "/cheatsheet",
    print: "/cheatsheet?autoprint=1",
    testId: "poster-row-cheatsheet",
  },
  {
    id: "trench",
    title: t("Trench Box QR Poster"),
    desc: t("OSHA 1926 Subpart P. QR to live trench-shield specs + soil-type quick reference."),
    where: t("Post inside every excavation kit toolbox."),
    accent: "border-slate-800 bg-slate-800",
    Icon: Box,
    open: "/admin/trench-boxes/poster",
    print: "/admin/trench-boxes/poster?autoprint=1",
    testId: "poster-row-trench",
  },
  {
    id: "jha",
    title: t("Job Hazard Plans QR Poster"),
    desc: t("QR to Job Hazard Plans hub + job list + what-to-look-for cheat card."),
    where: t("Post inside every job trailer."),
    accent: "border-amber-600 bg-amber-600",
    Icon: FileText,
    open: "/admin/jha-plans/poster",
    print: "/admin/jha-plans/poster?autoprint=1",
    testId: "poster-row-jha",
  },
  // Training Scan-&-Go — 4 rows, one per track. Same row shape so the
  // UI doesn't need a second list.
  {
    id: "training-field",
    title: t("Training Scan-&-Go · Field Crew"),
    desc: t("3 QR codes (EN / ES / EN+ES) → the full Field Crew training packet. Bilingual poster."),
    where: t("Post inside every site trailer."),
    accent: "border-red-700 bg-red-700",
    Icon: GraduationCap,
    open: "/training/field/poster",
    print: "/training/field/poster?autoprint=1",
    testId: "poster-row-training-field",
  },
  {
    id: "training-shop",
    title: t("Training Scan-&-Go · Shop"),
    desc: t("3 QR codes (EN / ES / EN+ES) → the Shop / Mechanic training packet."),
    where: t("Post inside the shop office and parts room."),
    accent: "border-slate-800 bg-slate-800",
    Icon: GraduationCap,
    open: "/training/shop/poster",
    print: "/training/shop/poster?autoprint=1",
    testId: "poster-row-training-shop",
  },
  {
    id: "training-pm",
    title: t("Training Scan-&-Go · PM"),
    desc: t("3 QR codes (EN / ES / EN+ES) → the PM / Project Management training packet."),
    where: t("Post on the wall behind the PM's desk."),
    accent: "border-amber-600 bg-amber-600",
    Icon: GraduationCap,
    open: "/training/pm/poster",
    print: "/training/pm/poster?autoprint=1",
    testId: "poster-row-training-pm",
  },
  {
    id: "training-admin",
    title: t("Training Scan-&-Go · Admin"),
    desc: t("3 QR codes → the Admin / Owner training packet incl. backup, restore, and security."),
    where: t("Keep in the admin / owner's office binder."),
    accent: "border-red-700 bg-red-700",
    Icon: GraduationCap,
    open: "/training/admin/poster",
    print: "/training/admin/poster?autoprint=1",
    testId: "poster-row-training-admin",
  },
];

export default function SitePostersPanel() {
  const { t } = useT();
  const posters = POSTERS(t);

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-6 sm:p-7 mb-12"
      data-testid="site-posters-panel"
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
        <div>
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
            {t("Site Posters")}
          </span>
          <h2 className="font-display text-2xl font-black tracking-tight text-slate-900 mt-1">
            {t("Printable handouts for every job trailer")}
          </h2>
          <p className="text-slate-600 text-sm mt-1.5 max-w-2xl">
            {t(
              "QR-coded posters foremen scan from any phone. One sheet each. Print before every quarterly safety refresh."
            )}
          </p>
        </div>
        <Link
          to="/admin/posters/print-all?autoprint=1"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 h-11 px-4 rounded-md bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs border-b-2 border-red-900 transition-colors"
          data-testid="print-all-posters-btn"
        >
          <PrinterCheck className="w-4 h-4" />
          {t("Print All Posters")}
        </Link>
      </div>

      <ul className="divide-y-2 divide-slate-100 border border-slate-200 rounded-md overflow-hidden">
        {posters.map(({ id, title, desc, where, accent, Icon, open, print, testId }) => (
          <li
            key={id}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3 bg-white"
            data-testid={testId}
          >
            <div
              className={`inline-flex items-center justify-center w-12 h-12 rounded-md ${accent} text-white shrink-0`}
            >
              <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-display font-black text-slate-900 leading-tight">
                {title}
              </div>
              <div className="text-sm text-slate-600 mt-1 leading-snug">{desc}</div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1.5">
                {where}
              </div>
            </div>
            <div className="flex gap-2 shrink-0">
              <Link
                to={open}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 h-10 px-3 rounded border-2 border-slate-300 hover:border-red-700 hover:text-red-700 text-slate-700 font-mono text-[11px] uppercase tracking-[0.15em] font-bold transition-colors"
                data-testid={`${testId}-open`}
              >
                <ExternalLink className="w-3.5 h-3.5" /> {t("Preview")}
              </Link>
              <Link
                to={print}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 h-10 px-3 rounded bg-slate-900 hover:bg-red-700 text-white font-mono text-[11px] uppercase tracking-[0.15em] font-bold transition-colors"
                data-testid={`${testId}-print`}
              >
                <Printer className="w-3.5 h-3.5" /> {t("Print")}
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
