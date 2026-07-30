export function buildWave3AdminHeaders(extra = {}) {
  if (typeof window === "undefined") return { ...extra };
  const adminToken =
    window.localStorage.getItem("masci.admin.token") ||
    window.sessionStorage.getItem("masci.admin.token") ||
    "";
  const directoryToken =
    window.localStorage.getItem("masci.directory.token") ||
    window.sessionStorage.getItem("masci.directory.token") ||
    window.__masciDirectoryTokenCache ||
    "";

  return {
    ...extra,
    ...(adminToken ? { "X-Admin-Token": adminToken } : {}),
    ...(directoryToken ? { "X-Directory-Token": directoryToken } : {}),
  };
}