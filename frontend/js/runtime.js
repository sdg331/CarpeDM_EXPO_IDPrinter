// Browser experience uses the real backend. Fixtures require an explicit URL.
export function resolveRuntime(query) {
  if (query.get("sample") === "1" || (query.get("demo") === "1" && query.get("controls") === "1")) return "sample";
  return query.get("kiosk") === "1" ? "kiosk" : "web";
}
