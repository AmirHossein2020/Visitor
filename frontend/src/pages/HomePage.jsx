import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";

export default function HomePage() {
  const { user, logout } = useAuth();
  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };
  return (
    <main className="flex min-h-dvh items-center justify-center bg-slate-50 p-4">
      <section className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-bold text-slate-900">سلام، {user.full_name}</h1>
        <p className="mt-3 leading-7 text-slate-600">ورود با موفقیت انجام شد.</p>
        <div className="mt-6 grid gap-3">
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/invoices")} type="button">فاکتورها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/companies")} type="button">فروشنده‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/purchases")} type="button">خریدها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/orders")} type="button">سفارش‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/customers")} type="button">مشتری‌ها</button>
          <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/products")} type="button">محصولات</button>
          <button className="min-h-12 w-full rounded-xl border border-slate-300 px-4 font-semibold text-slate-700 hover:bg-slate-50" onClick={handleLogout} type="button">خروج از حساب</button>
        </div>
      </section>
    </main>
  );
}
