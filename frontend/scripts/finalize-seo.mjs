import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { publicPages } from "../src/content/publicPages.js";

function envFrom(path) {
  if (!existsSync(path)) return {};
  return Object.fromEntries(readFileSync(path, "utf8").split(/\r?\n/).filter(line => line && !line.startsWith("#") && line.includes("=")).map(line => {
    const index = line.indexOf("="); return [line.slice(0, index).trim(), line.slice(index + 1).trim().replace(/^['"]|['"]$/g, "")];
  }));
}
const env = { ...envFrom(".env"), ...envFrom(".env.production"), ...process.env };
const site = (env.VITE_SITE_URL || "http://localhost:5173").replace(/\/$/, "");
const escape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const replaceMeta = (html, page, path) => html
  .replace(/<title>.*?<\/title>/s, `<title>${escape(page.title)}</title>`)
  .replace(/<meta name="description" content=".*?"\s*\/>/s, `<meta name="description" content="${escape(page.description)}" />`)
  .replace(/<link rel="canonical" href=".*?"\s*\/>/s, `<link rel="canonical" href="${site}${path}" />`)
  .replace(/<meta property="og:url" content=".*?"\s*\/>/s, `<meta property="og:url" content="${site}${path}" />`)
  .replace(/<meta property="og:title" content=".*?"\s*\/>/s, `<meta property="og:title" content="${escape(page.title)}" />`)
  .replace(/<meta property="og:description" content=".*?"\s*\/>/s, `<meta property="og:description" content="${escape(page.description)}" />`);
const body = (page) => `<main dir="rtl"><header><strong>ویزیتورکار | VisitorKar</strong></header><article><p>${escape(page.eyebrow)}</p><h1>${escape(page.h1)}</h1><p>${escape(page.intro)}</p>${page.sections.map(([title, text]) => `<section><h2>${escape(title)}</h2><p>${escape(text)}</p></section>`).join("")}<p><a href="/pricing">مشاهده تعرفه‌ها و آزمایش رایگان</a></p></article></main>`;
const indexPath = "dist/index.html";
let base = readFileSync(indexPath, "utf8").replaceAll("%VITE_SITE_URL%", site);
if (env.VITE_GOOGLE_SITE_VERIFICATION) {
  base = base.replace("</head>", `<meta name="google-site-verification" content="${escape(env.VITE_GOOGLE_SITE_VERIFICATION)}" /></head>`);
}
const home = { title: "ویزیتورکار | نرم افزار ویزیتوری، ثبت سفارش و صدور فاکتور فروش", description: "ویزیتورکار نرم افزار موبایل‌محور مدیریت مشتری، محصول، سفارش فروش، فاکتور PDF، موجودی و گزارش برای ویزیتورها و فروشندگان است.", eyebrow: "نرم افزار مدیریت فروش میدانی", h1: "فروش میدانی، از ثبت مشتری تا فاکتور در یک مسیر ساده", intro: "ویزیتورکار برای ویزیتورها و فروشندگانی ساخته شده که می‌خواهند هنگام حضور نزد مشتری سریع سفارش ثبت کنند و سوابق فروش را منظم نگه دارند.", sections: [["ثبت سریع سفارش و فاکتور","مشتری و محصول را انتخاب کنید، مقدار را وارد کنید و از سفارش تأییدشده فاکتور فارسی PDF بسازید."],["مدیریت کامل عملیات فروش","محصولات، مشتریان، خرید، مرجوعی، موجودی، داشبورد و گزارش فروش در یک سامانه هماهنگ در دسترس‌اند."]] };
const pricing = { title: "تعرفه و آزمایش رایگان ویزیتورکار", description: "مشاهده پلن‌های ماهانه و سالانه و شروع آزمایش رایگان ۲۴ ساعته نرم افزار ویزیتوری ویزیتورکار.", eyebrow: "تعرفه شفاف", h1: "پلن مناسب کار فروش خود را انتخاب کنید", intro: "امکانات اصلی سامانه در پلن‌ها یکسان است و قیمت‌های جاری مستقیماً از تنظیمات ویزیتورکار نمایش داده می‌شوند.", sections: [["آزمایش رایگان یک‌روزه","کاربر واجد شرایط می‌تواند پیش از خرید، یک بار به مدت دقیق ۲۴ ساعت امکانات سامانه را بررسی کند."],["پرداخت و تمدید قابل پیگیری","درخواست اشتراک و رسید پرداخت در حساب ثبت می‌شود و پس از بررسی مدیر، دسترسی فعال خواهد شد."]] };
for (const [path, page] of Object.entries({ "/": home, "/pricing": pricing, ...publicPages })) {
  const schema = { "@context": "https://schema.org", "@graph": [
    { "@type": "WebSite", name: "ویزیتورکار", alternateName: "VisitorKar", url: `${site}/`, description: home.description },
    { "@type": "SoftwareApplication", name: "ویزیتورکار", alternateName: "VisitorKar", applicationCategory: "BusinessApplication", operatingSystem: "Web, Android, iOS", url: `${site}/`, description: home.description },
    ...(path === "/" ? [] : [{ "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "ویزیتورکار", item: `${site}/` }, { "@type": "ListItem", position: 2, name: page.h1, item: `${site}${path}` }] }]),
  ] };
  const rendered = replaceMeta(base, page, path).replace("</head>", `<script id="landing-schema" type="application/ld+json">${JSON.stringify(schema).replaceAll("<", "\\u003c")}</script></head>`).replace('<div id="root"></div>', `<div id="root">${body(page)}</div>`);
  if (path === "/") writeFileSync(indexPath, rendered);
  else { const directory = `dist${path}`; mkdirSync(directory, { recursive: true }); writeFileSync(`${directory}/index.html`, rendered); }
}
const notFound = base
  .replace(/<title>.*?<\/title>/s, "<title>صفحه پیدا نشد | ویزیتورکار</title>")
  .replace(/<meta name="robots" content=".*?"\s*\/>/s, '<meta name="robots" content="noindex, nofollow" />')
  .replace('<div id="root"></div>', '<div id="root"><main dir="rtl"><h1>صفحه پیدا نشد</h1><p>نشانی واردشده در ویزیتورکار وجود ندارد.</p><a href="/">بازگشت به صفحه اصلی</a></main></div>');
writeFileSync("dist/404.html", notFound);
for (const file of ["dist/robots.txt", "dist/sitemap.xml"]) writeFileSync(file, readFileSync(file, "utf8").replaceAll("__SITE_URL__", site));
