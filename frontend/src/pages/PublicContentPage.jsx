import { useEffect } from "react";
import { navigate } from "../hooks/useRoute";
import { publicPages } from "../content/publicPages";

const site = (import.meta.env.VITE_SITE_URL || window.location.origin).replace(/\/$/, "");
const setMeta = (selector, attribute, value) => { let node = document.head.querySelector(selector); if (!node) { node = document.createElement(attribute === "href" ? "link" : "meta"); if (attribute === "href") node.rel = "canonical"; document.head.appendChild(node); } node.setAttribute(attribute, value); };

export default function PublicContentPage({ path }) {
  const page = publicPages[path];
  useEffect(() => { document.title = page.title; setMeta('meta[name="description"]', "content", page.description); setMeta('meta[property="og:title"]', "content", page.title); setMeta('meta[property="og:description"]', "content", page.description); setMeta('meta[property="og:url"]', "content", site + path); setMeta('link[rel="canonical"]', "href", site + path); }, [page, path]);
  return <main className="public-article"><nav><button onClick={() => navigate("/")}><b>ویزیتورکار</b><span>صفحه اصلی</span></button><button onClick={() => navigate("/pricing")}>تعرفه‌ها و آزمایش رایگان</button></nav><article><p>{page.eyebrow}</p><h1>{page.h1}</h1><div className="public-article-intro">{page.intro}</div>{page.sections.map(([title, body]) => <section key={title}><h2>{title}</h2><p>{body}</p></section>)}<aside><h2>آماده‌اید مسیر فروش را ساده‌تر کنید؟</h2><p>امکانات و پلن‌ها را ببینید یا با آزمایش رایگان یک‌روزه محیط واقعی سامانه را بررسی کنید.</p><button onClick={() => navigate("/pricing")}>مشاهده تعرفه‌ها</button></aside></article><footer><button onClick={() => navigate("/privacy")}>حریم خصوصی</button><button onClick={() => navigate("/terms")}>شرایط استفاده</button><button onClick={() => navigate("/contact")}>پشتیبانی</button></footer></main>;
}
