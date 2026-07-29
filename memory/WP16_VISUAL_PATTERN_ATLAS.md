# WP16 Visual Pattern Atlas

Date: 2026-07-29

## Rule of use
This atlas is descriptive only. It compares observed pattern families in the restored baseline and does **not** select winners or propose redesign actions.

## Evidence set used
- `WP16-EVID-PUBLIC-HUB.jpeg` — `/` — Public hub / public shell
- `WP16-EVID-PUBLIC-DAILY-FORM.jpeg` — `/daily/submit` — Public form / daily report authoring
- `WP16-EVID-ADMIN-LOGIN.jpeg` — `/admin/login` — Admin login shell
- `WP16-EVID-ADMIN-HOME.jpeg` — `/admin` — Admin shell + domain nav
- `WP16-EVID-ADMIN-GOVERNANCE.jpeg` — `/admin/governance` — Admin KPI / dashboard shell variant
- `WP16-EVID-PM-LOGIN.jpeg` — `/pm/login` — PM login shell
- `WP16-EVID-PM-HOME.jpeg` — `/pm` — PM shell + project dashboard
- `WP16-EVID-HR-LOGIN.jpeg` — `/hr/login` — HR login shell
- `WP16-EVID-HR-HOME.jpeg` — `/hr` — HR overview with blocked data calls observed
- `WP16-EVID-HR-EMPLOYEES.jpeg` — `/hr/employees` — HR list / filter / table pattern with blocked data calls observed
- `WP16-EVID-SAFETY-LOGIN.jpeg` — `/safety-portal/login` — Safety login shell
- `WP16-EVID-SAFETY-HOME.jpeg` — `/safety-portal` — Safety shell + KPI table mix
- `WP16-EVID-DISPATCH-LOGIN.jpeg` — `/dispatch-portal/login` — Dispatch login shell
- `WP16-EVID-DISPATCH-HOME.jpeg` — `/dispatch-portal` — Transportation mission control / map shell
- `WP16-EVID-SHOP-LOGIN.jpeg` — `/shop/login` — Shop login shell
- `WP16-EVID-SHOP-HOME.jpeg` — `/shop` — Shop command center shell

## 1. Login shell family

- **Shared structure:** Admin, PM, HR, Safety, Dispatch, and Shop login routes all use a centered single-card sign-in composition with the same navy top rail and graph-paper background.
- **Accent divergence:** Portal accents diverge by route: red (Admin), amber (PM), purple (HR), cyan (Safety), orange (Dispatch/Shop).
- **Evidence:** `WP16-EVID-ADMIN-LOGIN.jpeg`, `WP16-EVID-PM-LOGIN.jpeg`, `WP16-EVID-HR-LOGIN.jpeg`, `WP16-EVID-SAFETY-LOGIN.jpeg`, `WP16-EVID-DISPATCH-LOGIN.jpeg`, `WP16-EVID-SHOP-LOGIN.jpeg`

## 2. Public shell family

- **Hub shell:** The public hub uses the same navy rail and graph-paper background but opens into a wide editorial landing page with large marketing-style cards.
- **Focused work shell:** The public daily report route collapses into a single-column task flow with dense form controls and a lighter work panel.
- **Evidence:** `WP16-EVID-PUBLIC-HUB.jpeg`, `WP16-EVID-PUBLIC-DAILY-FORM.jpeg`

## 3. Authenticated shell family

- **Admin shell:** Admin uses a left-side vertical command stack with domain groups and a top bar carrying search, notifications, portal switcher, language, identity, home, and sign-out.
- **PM / HR / Safety / Shop shell:** These portals keep the shared top bar but swap in role-specific left navigation stacks and page-title language. KPI, queue, and dashboard compositions differ by portal.
- **Dispatch / Transportation shell:** Dispatch shifts away from the boxed left rail into a wide top sub-navigation plus mission-control map surface.
- **Evidence:** `WP16-EVID-ADMIN-HOME.jpeg`, `WP16-EVID-ADMIN-GOVERNANCE.jpeg`, `WP16-EVID-PM-HOME.jpeg`, `WP16-EVID-HR-HOME.jpeg`, `WP16-EVID-SAFETY-HOME.jpeg`, `WP16-EVID-DISPATCH-HOME.jpeg`, `WP16-EVID-SHOP-HOME.jpeg`

## 4. Header and search pattern family

- **Shared top bar:** Search remains centered/high-visibility across authenticated portals, while identity and action slots sit on the right edge.
- **Portal naming:** Portal subtitle language varies: “Admin Operating System”, “Project Management Center”, “What requires your attention today?”, “Shop Command Center”, and “Transportation Operations”.
- **Observed divergence:** Some shells rely on breadcrumb-style page labels, while others rely on a large page title plus module subtitle.

## 5. Navigation pattern family

- **Left stacked nav:** Admin, PM, HR, Safety, and Shop all use stacked vertical modules, but each groups content differently and uses different sectional labels and accent separators.
- **Top subnav workspace:** Dispatch/Transportation uses a horizontal workspace subnav with categories such as Operations, People, Compliance, and Operations Intelligence.
- **Evidence:** `WP16-EVID-ADMIN-HOME.jpeg`, `WP16-EVID-PM-HOME.jpeg`, `WP16-EVID-HR-HOME.jpeg`, `WP16-EVID-SAFETY-HOME.jpeg`, `WP16-EVID-SHOP-HOME.jpeg`, `WP16-EVID-DISPATCH-HOME.jpeg`

## 6. Dashboard and KPI pattern family

- **Admin governance:** Admin governance uses large report-style cards, status chips, and governance metadata blocks.
- **PM / HR / Safety / Shop:** PM, HR, Safety, and Shop dashboards mix KPI cards with queue or record sections beneath them, but sizing and density vary by portal.
- **Dispatch:** Dispatch foregrounds a live map before deeper queue/detail content, making it visually distinct from the left-rail dashboard portals.
- **Evidence:** `WP16-EVID-ADMIN-GOVERNANCE.jpeg`, `WP16-EVID-PM-HOME.jpeg`, `WP16-EVID-HR-HOME.jpeg`, `WP16-EVID-SAFETY-HOME.jpeg`, `WP16-EVID-SHOP-HOME.jpeg`, `WP16-EVID-DISPATCH-HOME.jpeg`

## 7. Table / list / queue pattern family

- **HR employee list:** The exercised HR Employees route shows quick-view chips, filter bars, reset/print/export actions, and a large empty/results area underneath.
- **Safety dashboard table:** The exercised Safety home route shows a row-based project attention table embedded directly under KPI cards.
- **Dispatch workspace:** Dispatch home emphasizes map-first situational awareness rather than list-first records.
- **Evidence:** `WP16-EVID-HR-EMPLOYEES.jpeg`, `WP16-EVID-SAFETY-HOME.jpeg`, `WP16-EVID-DISPATCH-HOME.jpeg`

## 8. Form pattern family

- **Daily report form:** The exercised daily report flow uses numbered steps, dense field groupings, inline badges, utility chips, and helper text inside a narrow work column.
- **Login forms:** Login forms use larger inputs and a short linear sign-in path, visually distinct from the production work forms.
- **Evidence:** `WP16-EVID-PUBLIC-DAILY-FORM.jpeg`, plus all login evidence files

## 9. Color and accent family

- **Shared base:** Navy chrome + graph-paper background appears repeatedly across public and authenticated surfaces.
- **Portal accents:** Red, amber, purple, cyan, orange, green, and slate accents coexist. Accent usage is portal-linked rather than globally uniform.
- **Visual hits from source inventory:** `bg-slate-900`=241, `transparent`=48, `shadow-lg`=28, `backdrop-blur`=17

## 10. Overlay / drawer / modal family

- **Source inventory only:** Overlay families were inventoried from source in this pass rather than exhaustively opened one by one.
- **Current counts:** Dialogs=64, AlertDialogs=1, Sheets=27, Drawers=11, Popovers=9, Tabs=23
- **Key files:** `NotificationBell.jsx`, `PmShell.jsx`, `HrPageShell.jsx`, `SafetyShell.jsx`, `AdminIntegrationCenter.jsx`, `Tasks.jsx`, `TrenchSafetyOpsCenter.jsx`