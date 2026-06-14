// MASCI Platform · ModalFooter — Track 14.0-FIXALL · Batch 2
//
// Shared primitive for modal action rows.
//
// Pattern (per BUTTONS_DICT.md §1):
//   • Destructive action (Delete · Remove · Discard) on the LEFT — visually
//     separated so it never sits next to the primary submit.
//   • Cancel / Close (ghost) in the middle-right cluster.
//   • Primary action (Submit · Save · Add · Generate PDF · Verify · etc.) on the
//     FAR right.
//
// Usage:
//   <ModalFooter>
//     <ModalFooter.Destructive>...</ModalFooter.Destructive>   (optional, left)
//     <ModalFooter.Cancel>Cancel</ModalFooter.Cancel>          (optional)
//     <ModalFooter.Primary>Save</ModalFooter.Primary>          (required-ish)
//   </ModalFooter>
//
// `sticky` opt-in for tall scrollable forms; default = inline. Always renders
// the same structure so Spanish-translation pass (14.0-S1) only changes the
// string children, never the layout.

import { Button } from "@/components/ui/button";

export function ModalFooter({
  children,
  sticky = false,
  className = "",
  destructive = null,
  testid = "modal-footer",
}) {
  // Discover whether children include a slot tagged for the destructive corner.
  // Simpler API: caller can either pass `destructive` prop OR include a
  // <ModalFooter.Destructive> child. We honour both for ergonomics.
  return (
    <div
      data-testid={testid}
      className={[
        "flex items-center gap-2",
        sticky
          ? "sticky bottom-0 bg-white border-t border-slate-200 px-5 py-3 z-10"
          : "pt-3",
        className,
      ].join(" ")}
    >
      {destructive ? (
        <div className="mr-auto">{destructive}</div>
      ) : (
        <div className="mr-auto" />
      )}
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}

ModalFooter.Cancel = function ModalFooterCancel({
  onClick,
  disabled = false,
  children = "Cancel",
  testid = "modal-cancel-btn",
  ...rest
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      onClick={onClick}
      disabled={disabled}
      data-testid={testid}
      {...rest}
    >
      {children}
    </Button>
  );
};

ModalFooter.Primary = function ModalFooterPrimary({
  type = "submit",
  onClick,
  disabled = false,
  children,
  testid = "modal-primary-btn",
  className = "",
  ...rest
}) {
  return (
    <Button
      type={type}
      onClick={onClick}
      disabled={disabled}
      data-testid={testid}
      className={["bg-red-700 hover:bg-red-800 text-white", className].join(" ")}
      {...rest}
    >
      {children}
    </Button>
  );
};

ModalFooter.Secondary = function ModalFooterSecondary({
  type = "button",
  onClick,
  disabled = false,
  children,
  testid = "modal-secondary-btn",
  ...rest
}) {
  return (
    <Button
      type={type}
      variant="outline"
      onClick={onClick}
      disabled={disabled}
      data-testid={testid}
      {...rest}
    >
      {children}
    </Button>
  );
};

ModalFooter.Destructive = function ModalFooterDestructive({
  onClick,
  disabled = false,
  children,
  testid = "modal-destructive-btn",
  ...rest
}) {
  return (
    <Button
      type="button"
      variant="destructive"
      onClick={onClick}
      disabled={disabled}
      data-testid={testid}
      {...rest}
    >
      {children}
    </Button>
  );
};

export default ModalFooter;
