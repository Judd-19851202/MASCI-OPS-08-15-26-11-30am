// TRACK 25A · Universal Admin OS Breadcrumb.
//
// One coherent breadcrumb component used by every Admin OS surface so
// the operator ALWAYS knows exactly where they are, one click from
// home, one click from the parent domain.
//
// Convention:
//   Admin OS › Domain › Feature [› Details]
//
// Usage:
//   <AdminBreadcrumb crumbs={[
//     { label: "Storage & Recovery", to: "/admin/storage-recovery" },
//     { label: "Backups" },
//   ]} />
//
// The first crumb ("Admin OS") is prepended automatically and always
// links to /admin. The last crumb is rendered as inactive (current).
import React from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export default function AdminBreadcrumb({ crumbs = [], testidPrefix = "admin-breadcrumb" }) {
  const trail = [
    { label: "Admin OS", to: "/admin", icon: Home, root: true },
    ...crumbs,
  ];
  return (
    <nav
      aria-label="Breadcrumb"
      data-testid={testidPrefix}
      data-admin-breadcrumb="true"
      className="mb-3 flex flex-wrap items-center gap-1.5 text-[11px] font-mono uppercase tracking-[0.14em] text-zinc-500"
    >
      {trail.map((c, i) => {
        const isLast = i === trail.length - 1;
        const Icon = c.icon;
        const content = (
          <span className={`inline-flex items-center gap-1 rounded-sm border px-2 py-1 ${isLast ? "border-orange-500 bg-orange-50 text-zinc-950 font-semibold" : "border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-700"}`}>
            {Icon ? <Icon className="w-3 h-3" /> : null}
            {c.label}
          </span>
        );
        return (
          <React.Fragment key={`${c.label}-${i}`}>
            {i > 0 ? (
              <ChevronRight className="w-3 h-3 text-zinc-400 shrink-0" aria-hidden="true" />
            ) : null}
            {isLast || !c.to ? (
              <span data-testid={`${testidPrefix}-crumb-${i}`}>{content}</span>
            ) : (
              <Link
                to={c.to}
                data-testid={`${testidPrefix}-crumb-${i}`}
                className="hover:underline"
              >
                {content}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
