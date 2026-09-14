// Local, dependency-free frontend preview. Production is served by FastAPI.
import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number(process.env.PORT || 4173);
const mime = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
};
http
  .createServer(async (req, res) => {
    try {
      const url = new URL(req.url, "http://localhost");
      const pathname = decodeURIComponent(url.pathname);
      if (pathname.startsWith("/api/")) {
        res.writeHead(503, { "Content-Type": "application/json" });
        return res.end(
          JSON.stringify({ ok: false, error: "BACKEND_UNAVAILABLE" }),
        );
      }
      const base =
        pathname === "/" || pathname === "/kiosk.html"
          ? path.join(root, "frontend")
          : pathname.startsWith("/static/")
            ? path.join(root, "frontend")
            : pathname.startsWith("/assets/")
              ? path.join(root, "assets")
              : null;
      if (!base) {
        res.writeHead(404);
        return res.end("Not found");
      }
      const relative =
        pathname === "/" || pathname === "/kiosk.html"
          ? "kiosk.html"
          : pathname.replace(/^\/(static|assets)\//, "");
      const file = path.resolve(base, relative);
      if (!file.startsWith(base + path.sep) || !(await stat(file)).isFile()) {
        res.writeHead(404);
        return res.end("Not found");
      }
      res.writeHead(200, {
        "Content-Type": mime[path.extname(file)] || "application/octet-stream",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      });
      res.end(await readFile(file));
    } catch {
      res.writeHead(404);
      res.end("Not found");
    }
  })
  .listen(port, "127.0.0.1", () => {
    console.log(`Frontend demo: http://localhost:${port}/?demo=1`);
    console.log(`Live UI (requires FastAPI): http://localhost:${port}/`);
  });
