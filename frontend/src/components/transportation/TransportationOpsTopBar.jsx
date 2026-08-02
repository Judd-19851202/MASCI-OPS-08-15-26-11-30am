/**
 * TRACK 18.00 · Phase E · Transportation Operations Portal Transformation
 *
 * The unified top bar that re-frames the dispatcher's entry experience.
 * Mounted at the top of `/dispatch-portal` (DispatchHub) so a dispatcher
 * logging in sees TRANSPORTATION OPERATIONS — not "Dispatch app".
 *
 * Doctrine:
 *   - Additive. NEVER mounts inside the dispatch board, map, command
 *     center, or driver pages. It is a header strip, not a router.
 *   - Reuses every existing route. Dispatch is one workspace inside
 *     the grouped nav — not a separate product.
 *   - `/` keyboard shortcut opens search (Phase C).
 *   - No backend changes. No new auth. No collection drift.
 */
import React from "react";
import { Link } from "react-router-dom";
import { Search, ChevronDown, Menu, X } from "lucide-react";
import { isAdmin } from "@/lib/adminAuth";
import { useT } from "@/lib/i18n";

const NAV_GROUPS = [
  {
    id: "ops",
    label: "Operations",
    items: [
      { label: "Mission Control", href: "/transportation-operations" },
      { label: "Dispatch", href: "/dispatch-portal" },
      { label: "Live Operations", href: "/transportation-operations/live-operations" },
      { label: "Fleet", href: "/transportation-operations/trucks" },
    ],
  },
  {
    id: "people",
    label: "People",
    items: [
      { label: "Drivers", href: "/transportation-operations/drivers" },
      { label: "Carriers", href: "/transportation-operations/carriers" },
    ],
  },
  {
    id: "compliance",
    label: "Compliance",
    items: [
      { label: "Compliance", href: "/transportation-operations/compliance" },
      { label: "Orientation", href: "/transportation-operations/orientation" },
    ],
  },
  {
    id: "intel",
    label: "Operations Intelligence",
    items: [
      { label: "Intelligence", href: "/transportation-operations/intelligence" },
      { label: "Cleanup", href: "/transportation-operations/intelligence/cleanup" },
      { label: "Automation", href: "/transportation-operations/intelligence/automation" },
    ],
  },
  {
    // TRACK 18.00 Phase F · Admin-only group. Hidden from non-admin
    // portal sessions so dispatch users never see a clickable dead end.
    id: "admin",
    label: "Administration",
    adminOnly: true,
    items: [
      { label: "Reports", href: "/transportation-operations/reports" },
      { label: "Audit", href: "/transportation-operations/audit" },
    ],
  },
];

function visibleNavGroups() {
  const admin = isAdmin();
  return NAV_GROUPS.filter((g) => !g.adminOnly || admin);
}

function NavMenu({ group, onItemClick }) {
  const { t } = useT();
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef(null);

  React.useEffect(() => {
    function handle(e) {
      if (!ref.current) return;
      if (!ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        data-testid={`txops-topbar-group-${group.id}`}
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1 text-[11px] uppercase tracking-wider font-semibold text-slate-300 hover:text-white px-2 py-1.5 rounded transition-colors"
      >
        {t(group.label)}
        <ChevronDown
          className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open ? (
        <div
          data-testid={`txops-topbar-menu-${group.id}`}
          className="absolute left-0 top-full mt-1 w-56 rounded-md border border-slate-700 bg-slate-900 shadow-xl z-50 overflow-hidden"
        >
          {group.items.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              data-testid={`txops-topbar-item-${group.id}-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
              onClick={() => { setOpen(false); onItemClick && onItemClick(item); }}
              className="block px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 hover:text-white"
            >
              {t(item.label)}
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Open the universal Transportation search. If a Phase C search input
 * is already on-page (`[data-testid="tx-search-input"]`), focus it
 * directly. Otherwise navigate to Mission Control where the search
 * rail lives. The `/` key fires when focus is not in an input.
 */
export function useTxOpsSlashShortcut() {
  React.useEffect(() => {
    function onKey(e) {
      if (e.key !== "/") return;
      const tag = (document.activeElement && document.activeElement.tagName) || "";
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
      if (document.activeElement && document.activeElement.isContentEditable) return;
      const existing = document.querySelector('[data-testid="txops-search-input"]');
      if (existing && typeof existing.focus === "function") {
        e.preventDefault();
        existing.focus();
        return;
      }
      e.preventDefault();
      window.location.assign("/transportation-operations");
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
}

export default function TransportationOpsTopBar() {
  const { t } = useT();
  useTxOpsSlashShortcut();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const groups = visibleNavGroups();
  return (
    <div
      data-testid="txops-portal-topbar"
      className="w-full bg-slate-950 border-b border-slate-800 text-slate-100"
    >
      <div className="flex flex-wrap items-center gap-3 px-4 py-2.5">
        <Link
          to="/transportation-operations"
          data-testid="txops-portal-topbar-brand"
          className="flex items-center gap-2"
        >
          <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
          <span className="text-[11px] uppercase tracking-[0.18em] font-semibold text-white">
            {t("Transportation Operations")}
          </span>
        </Link>

        <nav
          data-testid="txops-portal-topbar-nav"
          className="hidden md:flex items-center gap-1 ml-2"
        >
          {groups.map((g) => (
            <NavMenu key={g.id} group={g} />
          ))}
        </nav>

        <button
          type="button"
          data-testid="txops-portal-topbar-mobile-toggle"
          aria-label="Toggle navigation"
          onClick={() => setMobileOpen((v) => !v)}
          className="md:hidden ml-1 inline-flex items-center justify-center rounded p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
        >
          {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>

        <div className="ml-auto flex items-center gap-2">
          <Link
            to="/transportation-operations"
            data-testid="txops-portal-topbar-search"
            className="inline-flex items-center gap-1.5 rounded bg-slate-800 hover:bg-slate-700 px-2.5 py-1.5 text-[11px] text-slate-200 transition-colors"
            title={t("Open Transportation search ( / )")}
          >
            <Search className="h-3 w-3" />
            <span>{t("Search")}</span>
            <kbd className="ml-1 hidden lg:inline rounded border border-slate-600 px-1 text-[9px] font-mono text-slate-300">
              /
            </kbd>
          </Link>
          <Link
            to="/transportation-operations"
            data-testid="txops-portal-topbar-mission-control"
            className="hidden sm:inline-flex items-center gap-1 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 px-2.5 py-1.5 text-[11px] font-semibold transition-colors"
          >
            {t("Mission Control →")}
          </Link>
        </div>
      </div>

      {mobileOpen ? (
        <nav
          data-testid="txops-portal-topbar-mobile-nav"
          className="md:hidden border-t border-slate-800 bg-slate-900 px-4 py-2 space-y-2"
        >
          {groups.map((g) => (
            <div key={g.id}>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
                {t(g.label)}
              </div>
              <div className="flex flex-col gap-1">
                {g.items.map((item) => (
                  <Link
                    key={item.href}
                    to={item.href}
                    data-testid={`txops-topbar-mobile-item-${g.id}-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
                    onClick={() => setMobileOpen(false)}
                    className="text-xs text-slate-200 hover:text-white px-2 py-1.5 rounded hover:bg-slate-800"
                  >
                    {t(item.label)}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </nav>
      ) : null}
    </div>
  );
}
