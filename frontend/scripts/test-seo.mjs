import { existsSync, readFileSync } from "node:fs";

const paths = ["", "pricing", "software-visitori", "sales-order-management", "sales-invoice", "field-sales", "inventory-sales", "customer-management", "privacy", "terms", "contact"];
const titles = new Set();
for (const path of paths) {
  const file = path ? `dist/${path}/index.html` : "dist/index.html";
  if (!existsSync(file)) throw new Error(`Missing prerendered route: ${file}`);
  const html = readFileSync(file, "utf8");
  const title = html.match(/<title>(.*?)<\/title>/s)?.[1];
  if (!title || titles.has(title)) throw new Error(`Missing or duplicate title: ${path || "/"}`);
  if (!html.includes('name="description"') || !html.includes('rel="canonical"') || !html.includes("<h1>")) throw new Error(`Incomplete SEO contract: ${path || "/"}`);
  if (html.includes("noindex")) throw new Error(`Public route is noindex: ${path || "/"}`);
  JSON.parse(html.match(/<script id="landing-schema" type="application\/ld\+json">(.*?)<\/script>/s)?.[1] || "");
  titles.add(title);
}
const sitemap = readFileSync("dist/sitemap.xml", "utf8");
const notFound = readFileSync("dist/404.html", "utf8");
if (!/noindex, nofollow/.test(notFound)) throw new Error("404 page must be noindex");
const robots = readFileSync("dist/robots.txt", "utf8");
if (sitemap.includes("__SITE_URL__") || sitemap.includes("/login") || sitemap.includes("/register")) throw new Error("Invalid sitemap policy");
if (!robots.includes("Disallow: /support/") || !robots.includes("Sitemap: https://")) throw new Error("Invalid robots policy");
console.log(`SEO validation passed for ${paths.length} public routes; titles are unique.`);
