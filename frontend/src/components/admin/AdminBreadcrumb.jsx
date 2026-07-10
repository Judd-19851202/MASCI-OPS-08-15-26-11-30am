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
      className="flex items-center gap-1 text-[11px] font-mono uppercase tracking-widest text-slate-500 mb-3"
    >
      {trail.map((c, i) => {
        const isLast = i === trail.length - 1;
        const Icon = c.icon;
        const content = (
          <span className={`inline-flex items-center gap-1 ${isLast ? "text-slate-900 font-semibold" : "hover:text-slate-800"}`}>
            {Icon ? <Icon className="w-3 h-3" /> : null}
            {c.label}
          </span>
        );
        return (
          <React.Fragment key={`${c.label}-${i}`}>
            {i > 0 ? (
              <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" aria-hidden="true" />
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
