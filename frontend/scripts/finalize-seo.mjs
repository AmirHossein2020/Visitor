import { existsSync, readFileSync, writeFileSync } from "node:fs";

function envFrom(path) {
  if (!existsSync(path)) return {};
  return Object.fromEntries(readFileSync(path, "utf8").split(/\r?\n/).filter(line => line && !line.startsWith("#") && line.includes("=")).map(line => {
    const index = line.indexOf("="); return [line.slice(0, index).trim(), line.slice(index + 1).trim().replace(/^['"]|['"]$/g, "")];
  }));
}
const env = {...envFrom(".env"), ...envFrom(".env.production"), ...process.env};
const site = (env.VITE_SITE_URL || "http://localhost:5173").replace(/\/$/, "");
for (const file of ["dist/robots.txt", "dist/sitemap.xml"]) {
  writeFileSync(file, readFileSync(file, "utf8").replaceAll("__SITE_URL__", site));
}
