import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import MobileNav from "../components/MobileNav";

const sections = [["خانه","/app"],["مشتری‌ها","/customers"],["محصولات","/products"],["سفارش‌ها","/orders"],["فاکتورها","/invoices"],["خریدها","/purchases"],["موجودی","/inventory"],["گزارش‌ها","/reports"]];

export default function OrderLayout({ title, children, backPath = "/orders" }) {
  const { logout } = useAuth();
  const handleLogout = () => { logout(); navigate("/login", { replace: true }); };
  return (
    <div className="min-h-dvh bg-slate-50">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <button className="min-h-11 rounded-xl px-3 text-sm font-semibold text-teal-800 hover:bg-teal-50" onClick={() => navigate(backPath)} type="button">‹ بازگشت</button>
            <h1 className="text-lg font-bold text-slate-900">{title}</h1>
          </div>
          <button className="min-h-11 rounded-xl px-3 text-sm font-semibold text-slate-600 hover:bg-slate-100" onClick={handleLogout} type="button">خروج</button>
        </div>
        <nav className="mx-auto hidden max-w-6xl gap-1 overflow-x-auto px-6 pb-2 sm:flex" aria-label="بخش‌های کسب‌وکار">{sections.map(([label,href])=>{const active=window.location.pathname===href||window.location.pathname.startsWith(`${href}/`);return <button aria-current={active?"page":undefined} className={`min-h-10 whitespace-nowrap rounded-lg px-3 text-sm font-bold ${active?"bg-teal-700 text-white":"text-slate-600 hover:bg-slate-100"}`} key={href} onClick={()=>navigate(href)} type="button">{label}</button>})}</nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-5 pb-24 sm:px-6 sm:py-8">{children}</main>
      <MobileNav />
    </div>
  );
}
