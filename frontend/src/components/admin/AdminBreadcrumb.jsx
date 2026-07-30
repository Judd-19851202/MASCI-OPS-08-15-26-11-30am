import React from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export default function AdminBreadcrumb({ crumbs = [], testidPrefix = "admin-breadcrumb" }) {
  const trail = [{ label: "Admin OS", to: "/admin", icon: Home, root: true }, ...crumbs];

  return (
    <nav
      aria-label="Breadcrumb"
      data-testid={testidPrefix}
      data-admin-breadcrumb="true"
      className="mb-3 flex flex-wrap items-center gap-1.5 text-[11px] font-mono uppercase tracking-[0.16em] text-[color:var(--ink-soft)]"
    >
      {trail.map((crumb, index) => {
        const isLast = index === trail.length - 1;
        const Icon = crumb.icon;

        const content = (
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 transition-colors ${isLast ? "bg-[color:var(--paper-card)] text-[color:var(--ink-strong)] shadow-sm" : "hover:bg-white/70 hover:text-[color:var(--ink-strong)]"}`}>
            {Icon ? <Icon className="h-3 w-3" /> : null}
            {crumb.label}
          </span>
        );

        return (
          <React.Fragment key={`${crumb.label}-${index}`}>
            {index > 0 ? <ChevronRight className="h-3 w-3 shrink-0 text-[color:var(--ink-faint)]" aria-hidden="true" /> : null}
            {isLast || !crumb.to ? (
              <span data-testid={`${testidPrefix}-crumb-${index}`}>{content}</span>
            ) : (
              <Link to={crumb.to} data-testid={`${testidPrefix}-crumb-${index}`} className="rounded-full">
                {content}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}