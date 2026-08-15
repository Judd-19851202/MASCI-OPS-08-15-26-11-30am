/**
 * Shared browse-first-on-touch behavior for every cmdk-in-Radix-Popover
 * picker (Job, Unit, Topic, Employee, Team roster, …).
 *
 * Problem: Radix `Popover.Content` auto-focuses its first focusable child on
 * open. For a cmdk picker that is the `CommandInput`, so opening the picker
 * on a phone immediately pops the iOS keyboard OVER the results list. The
 * list is then pushed behind the keyboard and feels unscrollable, forcing the
 * operator to type — the exact platform-wide selector complaint.
 *
 * Fix: on coarse-pointer (touch) devices, prevent the open-time auto-focus so
 * the full list is browsable/finger-scrollable first. Tapping the search field
 * still focuses it and opens the keyboard for the search-acceleration path.
 * Desktop (fine pointer) keeps auto-focus so keyboard-first users are
 * unaffected.
 *
 * Pass as: <PopoverContent onOpenAutoFocus={preventAutoFocusOnTouch} />
 */
export function isCoarsePointer() {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(pointer: coarse)").matches
  );
}

export function preventAutoFocusOnTouch(event) {
  if (isCoarsePointer()) {
    event.preventDefault();
  }
}
