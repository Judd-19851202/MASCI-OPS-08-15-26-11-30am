// CrewSetupRestorePrompt.jsx — iter437 · Phase 31.1 · calm restore card.
//
// 3-button prompt shown on Daily Report mount when a device-local
// setup snapshot exists. Doctrine-locked: NEVER silent auto-fill ·
// shared-device safe · operational language only.
//
// Buttons (exact spec verbatim):
//   - Use Setup
//   - Start Blank
//   - Clear Saved Setup
//
// Optional nickname (Phase 31.1 · Part 7): if the snapshot has one,
// it's surfaced as a chip. A tiny inline pencil lets the operator
// rename it on the spot — kept calm via an inline input, no modal.

import React, { useState } from "react";
import { ScrollText, RotateCcw, FileText, Trash2, Pencil, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";

function _relativeDay(ts, t) {
  if (!ts) return "";
  try {
    const days = Math.floor((Date.now() - ts) / (24 * 60 * 60 * 1000));
    if (days <= 0) return t("today");
    if (days === 1) return t("yesterday");
    return `${days} ${t("days ago")}`;
  } catch { return ""; }
}

export default function CrewSetupRestorePrompt({
  snapshot,
  onUseSetup,
  onStartBlank,
  onClear,
  onRename,
  testId = "crew-setup-restore-prompt",
}) {
  const { t } = useT();
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState(snapshot?.nickname || "");
  if (!snapshot) return null;

  const crewCount = (snapshot.masci_crews || []).length;
  const subCount = (snapshot.subcontractors || []).length;
  const eqCount = (snapshot.equipment || []).length;
  const project = snapshot.project_name || snapshot.project_number || "";

  return (
    <section
      data-testid={testId}
      className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 mb-4"
    >
      <div className="flex items-start gap-3">
        <ScrollText
          className="h-5 w-5 text-amber-700 mt-0.5 flex-shrink-0"
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-amber-900">
            {t("Use yesterday's crew and equipment setup from this device?")}
          </h3>
          <p className="text-xs text-amber-800 mt-1">
            {t("Saved setups stay only on this device.")}
            {" "}
            {t("Use this option only if this is your crew device or personal device.")}
          </p>

          {/* Setup chip · nickname + saved-when + counts */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {editingName ? (
              <div className="flex items-center gap-1">
                <Input
                  data-testid={`${testId}-nickname-input`}
                  autoFocus
                  value={draftName}
                  onChange={(e) => setDraftName(e.target.value.slice(0, 60))}
                  className="h-7 text-xs border-amber-300 w-44"
                  placeholder={t("e.g. Paving Crew A")}
                />
                <button
                  type="button"
                  data-testid={`${testId}-nickname-save`}
                  className="text-amber-800 hover:text-amber-900"
                  aria-label={t("Save name")}
                  onClick={() => {
                    onRename && onRename(draftName);
                    setEditingName(false);
                  }}
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                data-testid={`${testId}-nickname-edit`}
                onClick={() => setEditingName(true)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white border border-amber-300 text-amber-900 text-[11px] uppercase tracking-wider font-mono font-bold hover:bg-amber-100"
                title={t("Optional · name this setup")}
              >
                <Pencil className="h-3 w-3" />
                {snapshot.nickname || t("Name this setup")}
              </button>
            )}
            <span
              data-testid={`${testId}-saved-when`}
              className="text-[11px] uppercase tracking-wider font-mono text-amber-700"
            >
              {t("saved")} {_relativeDay(snapshot.savedAt, t)}
            </span>
          </div>

          {/* Setup summary line · calm read-only */}
          {(project || crewCount || subCount || eqCount) && (
            <p
              data-testid={`${testId}-summary`}
              className="text-xs text-amber-900 mt-2"
            >
              {project ? (
                <>
                  <span className="font-medium">{project}</span>
                  {" · "}
                </>
              ) : null}
              {crewCount > 0 && (
                <>{crewCount} {crewCount === 1 ? t("crew member") : t("crew members")}</>
              )}
              {crewCount > 0 && (subCount > 0 || eqCount > 0) && " · "}
              {subCount > 0 && (
                <>{subCount} {subCount === 1 ? t("subcontractor") : t("subcontractors")}</>
              )}
              {subCount > 0 && eqCount > 0 && " · "}
              {eqCount > 0 && (
                <>{eqCount} {eqCount === 1 ? t("equipment item") : t("equipment items")}</>
              )}
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mt-3">
        <Button
          type="button"
          onClick={onUseSetup}
          data-testid={`${testId}-use`}
          className="bg-amber-700 hover:bg-amber-800 text-white h-9 px-4"
        >
          <RotateCcw className="h-4 w-4 mr-1.5" aria-hidden="true" />
          {t("Use Setup")}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onStartBlank}
          data-testid={`${testId}-blank`}
          className="h-9 px-4 border-amber-300 text-amber-900 hover:bg-amber-100"
        >
          <FileText className="h-4 w-4 mr-1.5" aria-hidden="true" />
          {t("Start Blank")}
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={onClear}
          data-testid={`${testId}-clear`}
          className="h-9 px-3 text-amber-900 hover:bg-amber-100"
        >
          <Trash2 className="h-4 w-4 mr-1.5" aria-hidden="true" />
          {t("Clear Saved Setup")}
        </Button>
      </div>

      <p className="text-[11px] text-amber-800 mt-2">
        {t("You can edit crew and equipment after loading.")}
        {" "}
        {t("Starting blank will not erase previously submitted reports.")}
      </p>
    </section>
  );
}
