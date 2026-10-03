// The normal entry point is the device flow. Both non-device modes require an
// explicit URL so a backend or hardware error never turns into sample success.
export function resolveRuntime(query) {
  if (query.get("sample") === "1" || (query.get("demo") === "1" && query.get("controls") === "1")) return "sample";
  if (query.get("preview") === "1" || query.get("demo") === "1" || query.get("web") === "1") return "web";
  return "kiosk";
}
