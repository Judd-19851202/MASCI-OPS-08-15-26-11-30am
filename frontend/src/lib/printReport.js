// Print helper that works inside the Emergent preview iframe AND on the
// standalone deployed site.
//
// Background: Emergent's preview URL hosts the app in an iframe under
// .preview.emergentagent.com. When code in that iframe calls window.print(),
// it triggers the iframe's print — which has no UI, so nothing visible
// happens. The native print dialog only fires from the *top-level* browser
// window. On the deployed standalone domain (safety.mascigc.com) we ARE
// the top-level window, so plain window.print() works.
//
// This helper handles both:
//   1. If we're already top-level → window.print() directly.
//   2. If we're inside an iframe   → open the same URL with ?autoprint=1
//      in a fresh top-level tab. The destination page detects the flag
//      and calls window.print() once it has rendered, giving the user the
//      real OS print dialog with a "Save as PDF" option.

const isTopLevel = () => {
  try {
    return window.top === window.self;
  } catch {
    // Cross-origin parent (Emergent preview) → top access throws → iframe
    return false;
  }
};

export function printReport() {
  if (isTopLevel()) {
    // Standalone — print directly
    window.print();
    return;
  }

  // Inside iframe — open a top-level copy of this exact page with ?autoprint=1
  const url = new URL(window.location.href);
  url.searchParams.set("autoprint", "1");
  const win = window.open(url.toString(), "_blank", "noopener,noreferrer");
  if (!win) {
    // Pop-up blocked — fall back to navigating in this iframe and then
    // letting the user hit Cmd/Ctrl+P. Better than silent failure.
    alert(
      "Pop-ups appear to be blocked. Please allow pop-ups for this site, or press Ctrl+P (Cmd+P on Mac) to print."
    );
  }
}

/**
 * Call from any view page mount. If the URL contains ?autoprint=1 we wait
 * for the next paint cycle, fire window.print(), then strip the flag from
 * the URL so reloading the tab doesn't re-print on every refresh.
 */
export function maybeAutoPrint() {
  try {
    const u = new URL(window.location.href);
    if (u.searchParams.get("autoprint") !== "1") return;
    // Two RAFs ≈ "after layout settled"
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        window.print();
        // Clean up the URL so reload won't re-fire
        u.searchParams.delete("autoprint");
        window.history.replaceState({}, "", u.toString());
      })
    );
  } catch {
    /* noop */
  }
}
