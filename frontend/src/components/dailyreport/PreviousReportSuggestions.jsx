// Phase 10D · Previous Report Suggestions — Path A.
//
// AUTO-APPLY on first job-select. No card. No buttons. Just a tiny
// "Yesterday's setup applied · Undo" toast for 6 seconds.
//
// Foreman opens the form, picks a job, the form fills itself. Done.
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";

async function _loadPrevious(projectNumber) {
  if (!projectNumber) return null;
  try {
    const r = await api.get("/daily-reports", { params: { project_number: projectNumber, limit: 5 } });
    const items = Array.isArray(r.data) ? r.data : (r.data?.items || []);
    items.sort((a, b) => String(b.report_date || "").localeCompare(String(a.report_date || "")));
    return items[0] || null;
  } catch { return null; }
}

// Pure hook: no UI. Auto-applies once per (projectNumber, mount) pair.
export default function usePreviousReportAutofill({ projectNumber, currentData, setData, enabled = true }) {
  const appliedFor = useRef(null);
  const [snapshot, setSnapshot] = useState(null);

  useEffect(() => {
    if (!enabled) return undefined;
    if (!projectNumber) return undefined;
    if (appliedFor.current === projectNumber) return undefined;
    let alive = true;

    _loadPrevious(projectNumber).then((prev) => {
      if (!alive || !prev) return;
      // Don't overwrite if the form already has crew + activity + equipment
      const hasContent =
        (currentData.masci_crews || []).length > 0 ||
        (currentData.equipment || []).length > 0 ||
        String(currentData.work_performed || "").trim().length > 20;
      if (hasContent) {
        appliedFor.current = projectNumber;
        return;
      }
      const before = {
        masci_crews: currentData.masci_crews,
        subcontractors: currentData.subcontractors,
        equipment: currentData.equipment,
        work_performed: currentData.work_performed,
        production: currentData.production,
      };
      const patch = {
        masci_crews: prev.masci_crews || [],
        subcontractors: prev.subcontractors || [],
        equipment: prev.equipment || [],
        work_performed: prev.work_performed || prev.activity_summary || "",
        production: prev.production || [],
      };
      const counts = [
        (patch.masci_crews || []).length && `${patch.masci_crews.length} crew`,
        (patch.equipment || []).length && `${patch.equipment.length} equipment`,
        String(patch.work_performed || "").trim().length && "activity",
      ].filter(Boolean).join(" · ");
      if (!counts) {
        appliedFor.current = projectNumber;
        return;
      }
      setSnapshot(before);
      setData((d) => ({ ...d, ...patch }));
      appliedFor.current = projectNumber;
      toast(`Yesterday's setup applied · ${counts}`, {
        duration: 6000,
        action: {
          label: "Undo",
          onClick: () => {
            setData((d) => ({ ...d, ...before }));
            setSnapshot(null);
            toast.dismiss();
          },
        },
        // Smaller, lower-friction
      });
    });

    return () => { alive = false; };
  }, [projectNumber, enabled]);  // eslint-disable-line react-hooks/exhaustive-deps

  return snapshot;
}
