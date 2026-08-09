// src/components/team/MyAssignedProjectsWidget.jsx
// Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2B
//
// Lightweight read-only widget that lists the projects on which the
// current user is rostered. Powered by `/api/users/me/projects` (Phase 1).
// Mountable on any portal (FL, Asset Care, Dispatch, Shop) — the
// endpoint resolves the actor by the portal token they present.

import React, { useEffect, useState } from "react";
import { fetchMyProjects } from "@/lib/teamRosterApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Briefcase } from "lucide-react";
import { useT } from "@/lib/i18n";
import { sanitizeOperatorError, sanitizeOperatorProjectNumber } from "@/lib/operatorLanguage";

const ROLE_LABEL = {
  pm: "PM", co_pm: "Co-PM", assistant_pm: "Assistant PM",
  superintendent: "Superintendent", foreman: "Foreman",
  safety_lead: "Safety Lead", project_engineer: "Project Engineer",
  asset_admin: "Asset Admin", locate_coordinator: "Locate Coordinator",
  dispatcher_contact: "Dispatcher Contact", shop_contact: "Shop Contact",
  executive_oversight: "Executive Oversight",
  read_only_stakeholder: "Read-only Stakeholder",
};

export default function MyAssignedProjectsWidget({ title = "My assigned jobs" }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    fetchMyProjects()
      .then((d) => setItems(d.items || []))
      .catch((e) => setErr(sanitizeOperatorError(e.message, t("Project roster unavailable right now."))))
      .finally(() => setLoading(false));
  }, []);

  // Group by project_number → list of role chips.
  const byProject = items.reduce((acc, it) => {
    const k = it.project_number;
    if (!acc[k]) acc[k] = [];
    acc[k].push(it.assignment_role);
    return acc;
  }, {});
  const projects = Object.entries(byProject).sort();

  return (
    <Card className="min-w-0" data-testid="my-assigned-projects-widget">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex min-w-0 flex-wrap items-start gap-2">
          <Briefcase className="h-4 w-4 shrink-0" />
          <span className="min-w-0 flex-1 break-words">{title}</span>
          <Badge variant="outline" className="text-xs shrink-0">
            {projects.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && <p className="text-sm text-slate-500">{t("Loading…")}</p>}
        {err && <p className="text-sm text-red-700">{err}</p>}
        {!loading && !err && projects.length === 0 && (
          <p className="text-sm text-slate-500 italic">
            {t("You aren't currently assigned to any active jobs.")}
          </p>
        )}
        {!loading && projects.length > 0 && (
          <ul className="divide-y divide-slate-100">
            {projects.map(([pn, roles]) => (
              <li key={pn} className="py-2 flex items-center justify-between" data-testid={`mp-row-${pn}`}>
                <span className="font-mono text-sm text-slate-800">{sanitizeOperatorProjectNumber(pn, t("Project number unavailable"))}</span>
                <span className="flex gap-1 flex-wrap justify-end">
                  {[...new Set(roles)].map((r) => (
                    <Badge key={r} variant="secondary" className="text-[10px]">
                      {t(ROLE_LABEL[r] || r)}
                    </Badge>
                  ))}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
