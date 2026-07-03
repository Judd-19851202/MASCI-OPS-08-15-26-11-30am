# TRACK 19.29 · PERSONA DAY-IN-THE-LIFE REPORT

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Anchor:** `TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md`

Walk-through of every real MASCI user role, from public entry (or login) through daily-work completion. Each persona is scored against the Six Pillars.

---

## 1 · Field Laborer
- **Entry:** Public QR / `/daily/submit` · `/incidents/report` · `/near-miss` (no login).
- **Workflow:** Fill Daily Report → attach photo → submit → sees Thank-You (`/thank-you`). Also scans QR at asset for TrenchSafetyQrLanding (`/trench-safety/assets/:assetId`).
- **PDFs / emails:** Daily Report PDF auto-emails to PM + Safety upon submit (dry-run available). Photo attachment routed.
- **Field-first checks:** ✅ Mobile-first layout · ✅ EN/ES toggle in header · ✅ Autosave (`useFormAutosave`) prevents data loss on interrupted submit · ✅ No keyboard overlay traps.
- **Score:** 9/9/9/9/9/9. **Verdict:** 🟢 GO.

## 2 · Equipment Operator
- **Entry:** Public `/equipment/submit` or scan QR on asset.
- **Workflow:** Fill Pre-Op → mark defect if any → submit. If defect → cascade to Shop.
- **PDFs / emails:** Pre-Op PDF emails Shop + FLL. Defect → Shop `/shop/equipment` queue.
- **Verdict:** 🟢 GO.

## 3 · Foreman
- **Entry:** `/field-leadership/portal/dashboard` (auth) or public field entry.
- **Workflow:** Daily Report roll-up · Toolbox Talk (`/meetings/submit`) · Trench Safety plan (`/jha`) · crew attendance · photos.
- **PDFs / emails:** Toolbox Talk PDF (attendance sheet) auto-emails PM + Safety.
- **Field-first checks:** ✅ TrenchAssetPicker fixed in 19.26 · ✅ Mobile-first · ✅ Draft restore.
- **Verdict:** 🟢 GO.

## 4 · Superintendent
- **Entry:** `/field-leadership` (gated, MASCIGC password) or `/leadership`.
- **Workflow:** FL Records (`/leadership/records`) · Field Leadership forms (`/leadership/:kind/new`) · cross-project visibility · Field Leadership PDF exports.
- **Verdict:** 🟢 GO.

## 5 · Project Manager
- **Entry:** `/pm/login` → `/pm` → `PmHubV2` (sidebar V2).
- **Workflow:** Job dashboards · daily-report roll-ups · Ops Actions queue · Employee 360 access · POS · project health · staffing.
- **PDFs / emails:** Weekly digest (dry-run available at `/admin/digest-config`) · Job PnL PDF · Daily Report PDFs · Incident Executive PDF for cross-portal reads.
- **Verdict:** 🟢 GO.

## 6 · Safety Manager
- **Entry:** `/safety-portal/login` → `SafetyHubV2` (sidebar V2).
- **Workflow:** Incident Report → Case Workspace (`/safety/cases/:caseId`) → Investigation → Evidence → Executive PDF (`/safety/cases/:caseId/reports/:reportType`) → Closeout. JHA plans. Toolbox archive. Near-miss review. Executive Intelligence Center.
- **PDFs / emails:** Incident Executive PDF · Case reports · Meetings PDF · JHA PDF. All emails through `fsi_send_email` with audit ledger.
- **Verdict:** 🟢 GO.

## 7 · HR
- **Entry:** `/hr/login` → `/hr` → `HrHubV2` (sidebar V2).
- **Workflow:** Employee 360 (`/hr/employees/:empId/profile`) · Historical Records Intake (`/hr/historical-records/intake` · `/queue` · `/batches`) · Compliance Brief PDF · Doc expirations · Employee records queue · Employee package PDFs (6 variants from Track 19.22).
- **PDFs / emails:** HR Compliance Brief PDF · Employee 360 PDF · 6 employee-package PDFs (Historical · Compliance · Discipline · PPE · Training · Full Discovery).
- **Verdict:** 🟢 GO.

## 8 · Shop / Mechanic
- **Entry:** `/shop/login` → `/shop` → `ShopHubV2`.
- **Workflow:** Pre-Op review · DVIR defects · Fleet visibility (`/shop/fleet`) · Fuel/Lube (`/shop/fuel-lube`) · Service Truck Reconciliation · Recovery Map · Asset Care & Readiness.
- **Track 19.28 delta:** Non-asset-admin shop users no longer see the "Asset Administrator · Historical Records" section 09 (visibility polish). Asset Admins retain full access.
- **PDFs / emails:** DVIR PDF · Pre-Op PDF · Service Truck Rec PDF.
- **Verdict:** 🟢 GO.

## 9 · Fleet
- **Entry:** `/shop/fleet` (accessed via shop portal) or admin `/admin/equipment`.
- **Workflow:** Per-unit DVIR + defect state · RTS verification queue · Weekly Lead/Emergency Equipment forms.
- **Verdict:** 🟢 GO. Sidebar V2 for Fleet is P3-2 backlog (uses tile-grid HubV2 today — fully functional).

## 10 · Dispatch
- **Entry:** `/dispatch-portal/login` → `/dispatch-portal` → `DispatchHubV2` (sidebar V2).
- **Workflow:** Command summary · Asset transfers · Holds · Utilization · Shift QR (`/admin/dls/shift-qr`) · Debrief flows · Motive integration data · Fleet OOS visibility.
- **Verdict:** 🟢 GO.

## 11 · Transportation
- **Entry:** `/transportation-operations/*` (dispatch-safe TX gate).
- **Workflow:** External Carrier invites (`/transport-invite/:token`) · Certificate Verify · Driver academy / orientation · Fleet + driver-carrier canonical models.
- **Verdict:** 🟢 GO. Sidebar V2 for Transportation is P3-2 backlog (currently uses AdminTransportation shell).

## 12 · Executive
- **Entry:** `/admin/executive-overview` · `/safety/executive-intelligence` · `/leadership/hub_v2`.
- **Workflow:** Executive read-only surfaces · cross-portal KPIs · Executive Incident PDFs · Ops attention queues.
- **Verdict:** 🟢 GO.

## 13 · Administrator
- **Entry:** `/admin/login` → `/admin` → `AdminHubV2` (Track 19.28 · now canonical) → Sidebar V2 (6 domains).
- **Rollback:** `/admin/hub_v1` retains the classic tile-grid for admins who prefer the flat 32-section list.
- **Workflow:** Every admin section — People · Jobs · Equipment · Email · Training · Compliance · Governance · System · Database · Audit Log · Deploy Recovery/Readiness · Integrations · Analytics · Command Center · Project Identity Governance · Operational Records · Operational Inventory · Operational Language · Promo Assets · Recovery · Deploy Recovery · Guidance Coverage.
- **Verdict:** 🟢 GO. All routes reachable via sidebar V2 (parity closed in Track 19.28).

## 14 · Public / Unauthenticated
- **Entry:** `/` (Hub landing) · `/safety` · `/field` · `/qaqc` · `/daily/submit` · `/incidents/report` · `/near-miss` · `/meetings/submit` · `/equipment/submit` · `/inspections/submit` (redirect to `/safety/inspections/new` or `/safety-portal/login`) · `/jha` · `/trench-safety` · `/trench-safety/tabulated-data` · `/trench-safety/report` · `/trench-safety/references` · `/cheatsheet` · `/guidance` · `/transport-invite/:token` · `/transport-verify/:cnum` · `/field/calculators` · `/fleet/dvir/submit`.
- **Workflow:** Submit-and-thank-you (`/thank-you`). Print-friendly cheat sheets. QR-driven scan-and-go.
- **Restricted-state UI:** Restricted portal tiles on `/` show "Sign in to continue" — no 401/403 leakage.
- **Verdict:** 🟢 GO.

---

## Cross-persona guarantees
- ✅ Every persona has a working login path OR public entry.
- ✅ Every authenticated persona lands on a real hub (not a placeholder).
- ✅ Every persona's primary workflow has a submit path that produces a real record.
- ✅ Every persona has bilingual support (EN + ES) via `useT()` hook.
- ✅ Every persona has empty/loading/error states via the design-system primitives (`EmptyState`, `PortalShell`, `StatusChip`, `Card`).
- ✅ Every submit path autosaves via `useFormAutosave` where applicable.
- ✅ Every persona's PDFs are professional-quality (ReportLab-generated · no raw DB dumps · no missing fields per PDF audit).
- ✅ No dead ends. No duplicate paths (Cheat Sheet consolidated · Admin V2 canonical · Hub V2s canonical for HR/Safety/PM/Shop/Dispatch).

## Roadmap items surfaced but non-blocking
- P3-1 · Sidebar V2 for Shop portal (currently HubV2 tile-grid).
- P3-2 · Sidebar V2 for Transportation / Fleet.
- P3-3 · TrenchAssetPicker enter-key auto-select.
- P3-4 · TrenchAssetPicker recently-used shortcut.
- P3-5 · HR Bulk Intake "Continue previous session".
- P3-8 · HR Compliance At Risk widget.
- P3-9 · HR Recent intake activity feed.
- P3-10 · HR onboarding "New here?" callout.

None of these prevent pilot rollout.
