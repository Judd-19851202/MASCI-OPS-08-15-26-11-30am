// src/components/team/RemoveReasonDialog.jsx
// TRACK 15.39A · Structured remove-assignment reason dialog.
//
// Replaces the legacy `window.prompt(...)` UX with a shadcn Dialog that:
//   * forces the operator to pick one of the 7 certified categories
//     (reassigned · staffing_adjustment · promotion · demotion ·
//      project_complete · left_company · other) — locked taxonomy from
//     the Track 15.39 backend cert.
//   * requires free-text when category === "other" (matches the
//     backend 400 guard so the user never sees a server bounce).
//   * surfaces the server `detail` inline on failure instead of
//     bubbling up as a generic toast.
//
// The parent is responsible for calling `removeTeamMember(...)` with
// `{ reason_category, reason_text }` and refreshing the roster after
// the promise resolves.

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

const CATEGORIES = [
  { key: "reassigned", label: "Reassigned" },
  { key: "staffing_adjustment", label: "Staffing Adjustment" },
  { key: "promotion", label: "Promotion" },
  { key: "demotion", label: "Demotion" },
  { key: "project_complete", label: "Project Complete" },
  { key: "left_company", label: "Left Company" },
  { key: "other", label: "Other" },
];

export function RemoveReasonDialog({
  open,
  onOpenChange,
  member, // { id, display_name, role_label }
  onConfirm, // (reason_category, reason_text) => Promise<void>
}) {
  const [category, setCategory] = useState("reassigned");
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Reset form whenever the dialog re-opens against a different member.
  useEffect(() => {
    if (open) {
      setCategory("reassigned");
      setText("");
      setError(null);
      setSubmitting(false);
    }
  }, [open, member?.id]);

  const otherRequiresText = category === "other" && !text.trim();

  async function handleSubmit() {
    if (otherRequiresText) return;
    setSubmitting(true);
    setError(null);
    try {
      await onConfirm(category, text.trim() || undefined);
      onOpenChange(false);
    } catch (e) {
      setError(e?.detail || e?.message || String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => (!submitting ? onOpenChange(v) : null)}>
      <DialogContent
        data-testid="remove-reason-dialog"
        className="max-w-md"
      >
        <DialogHeader>
          <DialogTitle>
            Remove {member?.display_name || member?.email || "team member"}
          </DialogTitle>
          <DialogDescription>
            {member?.role_label ? (
              <>Currently <strong>{member.role_label}</strong>. </>
            ) : null}
            Choose a reason — recorded in the audit log.
          </DialogDescription>
        </DialogHeader>

        <RadioGroup
          value={category}
          onValueChange={setCategory}
          className="space-y-2 py-1"
          data-testid="reason-category-group"
        >
          {CATEGORIES.map((c) => (
            <div key={c.key} className="flex items-center gap-2">
              <RadioGroupItem
                value={c.key}
                id={`reason-${c.key}`}
                data-testid={`reason-${c.key}`}
              />
              <Label
                htmlFor={`reason-${c.key}`}
                className="cursor-pointer text-sm"
              >
                {c.label}
              </Label>
            </div>
          ))}
        </RadioGroup>

        <div className="space-y-1">
          <Label className="text-xs uppercase tracking-wide text-slate-500">
            {category === "other" ? "Reason (required)" : "Notes (optional)"}
          </Label>
          <Textarea
            data-testid="reason-text"
            placeholder={
              category === "other"
                ? "Required — explain the reason"
                : "Optional notes"
            }
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
          />
        </div>

        {error && (
          <p
            data-testid="reason-error"
            className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1"
          >
            {error}
          </p>
        )}

        <DialogFooter className="gap-2">
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
            data-testid="reason-cancel"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting || otherRequiresText}
            data-testid="reason-submit"
          >
            {submitting ? "Removing…" : "Remove"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default RemoveReasonDialog;
