import { tStr, useT } from "@/lib/i18n";

export const GOVERNED_ACTION_LABELS = {
  back: "Back",
  home: "Home",
  dashboard: "Dashboard",
  profile: "Profile",
  search: "Search",
  loading: "Loading",
  save: "Save",
  edit: "Edit",
  delete: "Delete",
  cancel: "Cancel",
  submit: "Submit",
  export: "Export",
  print: "Print",
  email: "Email",
  download: "Download",
  upload: "Upload",
  filter: "Filter",
  clear: "Clear",
  apply: "Apply",
  retry: "Retry",
  refresh: "Refresh",
  close: "Close",
  next: "Next",
  previous: "Previous",
  view: "View",
  open: "Open",
  return: "Return",
  archive: "Archive",
  restore: "Restore",
};

export function governedActionLabel(key, translate = tStr) {
  return translate(GOVERNED_ACTION_LABELS[key] || key);
}

export function useGovernedActions() {
  const { t } = useT();
  return {
    tAction: (key) => governedActionLabel(key, t),
  };
}
