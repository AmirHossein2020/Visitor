import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import { getDashboard } from "../services/reports";
import { formatPrice } from "../services/products";
import MobileNav from "../components/MobileNav";

export default function HomePage() {
  const { user, logout } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getDashboard().then(setDashboard).catch(() => setError("دریافت اطلاعات داشبورد ممکن نشد.")); }, []);
  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };
  return (
    <main className="min-h-dvh bg-slate-50 p-4 sm:p-6">
      <div className="mx-auto max-w-6xl"><header className="mb-5"><h1 className="text-2xl font-bold text-slate-900">سلام، {user.full_name}</h1><p className="mt-1 text-slate-600">نمای کلی فعالیت کسب‌وکار شما</p></header>
        {error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {dashboard && <><section className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[["فروش امروز", dashboard.today.sales_total], ["فروش این ماه", dashboard.current_month.sales_total], ["خرید این ماه", dashboard.current_month.purchase_total], ["مرجوعی این ماه", dashboard.current_month.return_total], ["فروش خالص", dashboard.current_month.net_sales]].map(([label, value]) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={label}><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-lg font-bold text-teal-800">{formatPrice(value)}</p></article>)}<button className="rounded-2xl bg-white p-4 text-right ring-1 ring-slate-200" onClick={() => navigate("/orders")} type="button"><p className="text-sm text-slate-500">سفارش‌های این ماه</p><p className="mt-2 text-2xl font-bold">{new Intl.NumberFormat("fa-IR").format(dashboard.current_month.orders_count)}</p></button><button className="rounded-2xl bg-white p-4 text-right ring-1 ring-slate-200" onClick={() => navigate("/inventory")} type="button"><p className="text-sm text-slate-500">موجودی منفی</p><p className={"mt-2 text-2xl font-bold " + (dashboard.inventory.negative_stock_count ? "text-red-700" : "text-teal-800")}>{new Intl.NumberFormat("fa-IR").format(dashboard.inventory.negative_stock_count)}</p></button></section></>}
        <section className="mt-6 rounded-2xl bg-white p-5 ring-1 ring-slate-200"><h2 className="text-lg font-bold">دسترسی سریع</h2><div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/reports")} type="button">گزارش‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/inventory")} type="button">موجودی</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/invoices")} type="button">فاکتورها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/returns")} type="button">مرجوعی‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/companies")} type="button">فروشنده‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/purchases")} type="button">خریدها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/orders")} type="button">سفارش‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/customers")} type="button">مشتری‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/products")} type="button">محصولات</button>
          <button className="min-h-12 w-full rounded-xl border border-slate-300 px-4 font-semibold text-slate-700 hover:bg-slate-50" onClick={handleLogout} type="button">خروج از حساب</button>
        </div></section>
      </div>
      <MobileNav />
    </main>
  );
}
