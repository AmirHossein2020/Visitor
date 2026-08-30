import { navigate } from "../hooks/useRoute";

const links = [
  ["خانه", "/app", "⌂"],
  ["مشتری‌ها", "/customers", "◉"],
  ["سفارش‌ها", "/orders", "▤"],
  ["محصولات", "/products", "◇"],
];

export default function MobileNav() {
  const path = window.location.pathname;
  return <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur sm:hidden" aria-label="ناوبری اصلی"><div className="mx-auto grid max-w-md grid-cols-4">{links.map(([label, href, icon]) => { const active = path.startsWith(href); return <button className={"flex min-h-16 flex-col items-center justify-center gap-1 text-xs font-semibold " + (active ? "text-teal-700" : "text-slate-500")} key={href} onClick={() => navigate(href)} type="button"><span className="text-xl leading-none" aria-hidden="true">{icon}</span><span>{label}</span></button>; })}</div></nav>;
}
