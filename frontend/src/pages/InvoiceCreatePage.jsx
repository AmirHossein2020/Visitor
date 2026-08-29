import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { listCompanies } from "../services/companies";
import { issueInvoice } from "../services/invoices";
import { getOrder } from "../services/orders";
import { formatPrice } from "../services/products";

export default function InvoiceCreatePage({ orderId }) {
  const [order, setOrder] = useState(null);
  const [sellers, setSellers] = useState([]);
  const [form, setForm] = useState({ seller_profile: "", discount_amount: "0", tax_amount: "0", duties_amount: "0", notes: "" });
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  useEffect(() => { Promise.all([getOrder(orderId), listCompanies()]).then(([orderData, sellerData]) => { setOrder(orderData); setSellers(sellerData); }).catch((requestError) => setError(getErrorMessage(requestError))); }, [orderId]);
  const finalPreview = order ? Number(order.total_amount) - Number(form.discount_amount || 0) + Number(form.tax_amount || 0) + Number(form.duties_amount || 0) : 0;
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault(); setError("");
    if (!form.seller_profile) return setError("فروشنده را انتخاب کنید.");
    if ([form.discount_amount, form.tax_amount, form.duties_amount].some((value) => Number(value) < 0)) return setError("مبالغ نمی‌توانند منفی باشند.");
    if (finalPreview < 0) return setError("تخفیف نمی‌تواند مبلغ نهایی را منفی کند.");
    setIsSaving(true);
    try { const invoice = await issueInvoice({ sales_order: orderId, ...form }); navigate("/invoices/" + invoice.id, { replace: true }); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setIsSaving(false); }
  };
  return <OrderLayout title={order?.active_invoice ? "صدور فاکتور اصلاحی" : "صدور فاکتور"} backPath={"/orders/" + orderId}><div className="mx-auto max-w-3xl">
    {!order && !error && <p className="py-12 text-center text-slate-600">در حال آماده‌سازی فاکتور…</p>}
    {error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {order && sellers.length === 0 && <div className="rounded-2xl bg-amber-50 p-5 text-amber-800 ring-1 ring-amber-200"><p>برای صدور فاکتور ابتدا یک فروشنده ایجاد کنید.</p><button className="mt-4 min-h-11 rounded-xl bg-teal-700 px-4 font-semibold text-white" onClick={() => navigate("/companies/new")} type="button">ایجاد فروشنده</button></div>}
    {order && sellers.length > 0 && <form className="space-y-4" onSubmit={submit}>{order.active_invoice && <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800">نسخه جدید از وضعیت فعلی سفارش ساخته می‌شود و فاکتور قبلی بدون تغییر نگهداری خواهد شد.</p>}<section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><p className="text-sm text-slate-500">خریدار</p><h2 className="mt-1 text-xl font-bold">{order.customer_name}</h2><p className="mt-4 text-sm text-slate-500">اقلام سفارش: {order.items.length}</p><p className="mt-1 font-semibold text-teal-800">{formatPrice(order.total_amount)} تومان</p></section>
      <section className="space-y-4 rounded-2xl bg-white p-5 ring-1 ring-slate-200"><label className="block"><span className="mb-1.5 block text-sm font-medium">فروشنده / شرکت</span><select name="seller_profile" className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3" required value={form.seller_profile} onChange={update}><option value="">انتخاب فروشنده</option>{sellers.map((seller) => <option key={seller.id} value={seller.id}>{seller.name}</option>)}</select></label>
        <div className="grid gap-3 sm:grid-cols-3">{[["discount_amount", "تخفیف"], ["tax_amount", "مالیات"], ["duties_amount", "عوارض"]].map(([name, label]) => <label className="text-sm" key={name}>{label} (تومان)<input name={name} className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0" step="0.01" type="number" value={form[name]} onChange={update} /></label>)}</div>
        <label className="block text-sm">یادداشت (اختیاری)<textarea name="notes" className="mt-1 min-h-24 w-full rounded-xl border border-slate-300 p-3" value={form.notes} onChange={update} /></label></section>
      <div className="sticky bottom-3 rounded-2xl bg-white p-4 shadow-lg ring-1 ring-slate-200"><div className="mb-3 flex justify-between text-lg font-bold"><span>مبلغ نهایی</span><span>{formatPrice(finalPreview)} تومان</span></div><button className="min-h-12 w-full rounded-xl bg-teal-700 font-semibold text-white disabled:opacity-60" disabled={isSaving} type="submit">{isSaving ? "در حال صدور…" : "تأیید و صدور فاکتور"}</button></div>
    </form>}
  </div></OrderLayout>;
}
