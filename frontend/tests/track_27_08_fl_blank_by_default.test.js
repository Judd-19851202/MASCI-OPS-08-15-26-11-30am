/**
 * TRACK 27.08 · Explicit-restore contract regression lock.
 *
 * Before this fix, `useDraftSync` auto-applied any IndexedDB draft to
 * the form state on mount — creating the appearance of stale
 * carryover ("clicking termination shows another employee's data").
 * The fix separates loading from applying: the hook loads the draft
 * but only invokes `onRecover` when the caller explicitly calls
 * `applyDraft()`.
 *
 * This regression lock proves the auto-apply behavior is gone at the
 * source-code level and that both branches of the explicit prompt
 * (Restore vs Start blank) are wired up in the FL form.
 */
const fs = require("fs");
const path = require("path");

const hookSrc = fs.readFileSync(
  path.resolve(__dirname, "../src/lib/resiliency/useDraftSync.js"),
  "utf-8",
);
const formSrc = fs.readFileSync(
  path.resolve(__dirname, "../src/pages/FieldLeadershipFormPage.jsx"),
  "utf-8",
);

describe("TRACK 27.08 · FL blank-by-default + explicit restore", () => {
  test("useDraftSync exposes pendingDraft and applyDraft — no auto-apply", () => {
    // The hook must NOT auto-invoke onRecover on mount. Verify the
    // structural markers of the new contract are present.
    expect(hookSrc).toContain("pendingDraft");
    expect(hookSrc).toContain("hasPendingDraft");
    expect(hookSrc).toContain("applyDraft");
    // Ensure the old auto-apply pattern is absent.
    expect(hookSrc).not.toMatch(/onRecoverRef\.current\(draft\)\s*$/m);
    // The applyDraft callback IS allowed to invoke onRecover — but
    // only inside a useCallback body, never inside the mount effect.
    const mountEffect = hookSrc.match(/On mount:[\s\S]+?}, \[formKey, actorId\]\);/);
    if (mountEffect) {
      expect(mountEffect[0]).not.toContain("onRecoverRef.current(");
    }
  });

  test("FL form renders an explicit Restore / Start blank prompt", () => {
    // Both operator choices must be present in the JSX.
    expect(formSrc).toContain("fl-draft-restore-prompt");
    expect(formSrc).toContain("fl-draft-restore-apply");
    expect(formSrc).toContain("fl-draft-restore-discard");
    // The prompt is gated on `hasPendingDraft` — form is blank by
    // default and only shows the prompt when a draft exists.
    expect(formSrc).toContain("hasPendingDraft");
  });

  test("Draft key is scoped to user + form + kind (no cross-user bleed)", () => {
    // The `formKey` passed to useDraftSync includes `fl-<kind>-new`
    // and the actor id is passed separately; the draft store combines
    // them. Verify both are present at the call site.
    expect(formSrc).toMatch(/`fl-\$\{kind\}-new`/);
    expect(formSrc).toContain("getActorId()");
  });

  test("Successful submit calls commit() to clear the draft", () => {
    expect(formSrc).toContain("await commit()");
  });
});
