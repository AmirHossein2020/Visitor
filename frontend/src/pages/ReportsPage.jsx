import { useEffect, useState } from "react";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { formatPrice } from "../services/products";
import { getCustomerReport, getProductReport, getSummaryReport } from "../services/reports";

const now = new Date();
const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
const monthStart = today.slice(0, 8) + "01";

export default function ReportsPage() {
  const [range, setRange] = useState({ from: monthStart, to: today });
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const load = async (event) => {
    event?.preventDefault(); setError(""); setLoading(true);
    try { const [summary, products, customers] = await Promise.all([getSummaryReport(range.from, range.to), getProductReport(range.from, range.to), getCustomerReport(range.from, range.to)]); setData({ summary, products, customers }); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  return <OrderLayout title="گزارش‌ها" backPath="/"><form className="mb-5 grid gap-3 rounded-2xl bg-white p-4 ring-1 ring-slate-200 sm:grid-cols-[1fr_1fr_auto]" onSubmit={load}><label className="text-sm">از تاریخ<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" type="date" value={range.from} onChange={(event) => setRange({ ...range, from: event.target.value })} /></label><label className="text-sm">تا تاریخ<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" type="date" value={range.to} onChange={(event) => setRange({ ...range, to: event.target.value })} /></label><button className="min-h-12 self-end rounded-xl bg-teal-700 px-6 font-semibold text-white disabled:opacity-60" disabled={loading} type="submit">{loading ? "در حال دریافت…" : "نمایش گزارش"}</button></form>{error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{data && <div className="space-y-6"><section className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[["فروش", data.summary.sales_total], ["خرید", data.summary.purchase_total], ["مرجوعی", data.summary.return_total], ["فروش خالص", data.summary.net_sales]].map(([label, value]) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={label}><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-lg font-bold text-teal-800">{formatPrice(value)} تومان</p></article>)}</section><section><h2 className="mb-3 text-lg font-bold">محصولات پرفروش</h2><div className="grid gap-3 sm:grid-cols-2">{data.products.map((item, index) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={`${item.product_name}-${item.brand}-${index}`}><div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.product_name}</h3><p className="text-sm text-slate-500">{item.brand || "بدون برند"}</p></div><span className="font-semibold">{new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 3 }).format(Number(item.quantity_sold))} {item.unit}</span></div><p className="mt-3 text-sm text-teal-800">{formatPrice(item.total_sales)} تومان</p></article>)}</div>{data.products.length === 0 && <p className="rounded-2xl bg-white p-6 text-center text-slate-500 ring-1 ring-slate-200">فروشی در این بازه نیست.</p>}</section><section><h2 className="mb-3 text-lg font-bold">فروش مشتری‌ها</h2><div className="grid gap-3 sm:grid-cols-2">{data.customers.map((item) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={`${item.sales_order__customer_id}-${item.buyer_name}`}><h3 className="font-bold">{item.buyer_name}</h3>{item.buyer_company_name && <p className="text-sm text-slate-500">{item.buyer_company_name}</p>}<div className="mt-3 flex justify-between text-sm"><span>{new Intl.NumberFormat("fa-IR").format(item.invoice_count)} فاکتور</span><span className="font-semibold text-teal-800">{formatPrice(item.total_sales)} تومان</span></div></article>)}</div>{data.customers.length === 0 && <p className="rounded-2xl bg-white p-6 text-center text-slate-500 ring-1 ring-slate-200">فروشی برای مشتری‌ها ثبت نشده است.</p>}</section></div>}</OrderLayout>;
}
