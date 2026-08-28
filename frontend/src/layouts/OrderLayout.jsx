import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";

export default function OrderLayout({ title, children, backPath = "/orders" }) {
  const { logout } = useAuth();
  const handleLogout = () => { logout(); navigate("/login", { replace: true }); };
  return (
    <div className="min-h-dvh bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex min-h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <button className="min-h-11 rounded-xl px-3 text-sm font-semibold text-slate-600 hover:bg-slate-100" onClick={() => navigate(backPath)} type="button">بازگشت</button>
            <h1 className="text-lg font-bold text-slate-900">{title}</h1>
          </div>
          <button className="min-h-11 rounded-xl px-3 text-sm font-semibold text-slate-600 hover:bg-slate-100" onClick={handleLogout} type="button">خروج</button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-5 sm:px-6 sm:py-8">{children}</main>
    </div>
  );
}
