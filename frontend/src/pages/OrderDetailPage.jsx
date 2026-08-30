import { useCallback, useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { addOrderItem, getOrder, removeOrderItem, updateOrder, updateOrderItem } from "../services/orders";
import { formatPrice, listProducts } from "../services/products";

export default function OrderDetailPage({ orderId }) {
  const [order, setOrder] = useState(null);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState([]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [isActing, setIsActing] = useState(false);
  const load = useCallback(() => getOrder(orderId).then((data) => { setOrder(data); setNotes(data.notes || ""); }).catch((requestError) => setError(getErrorMessage(requestError))), [orderId]);
  useEffect(() => { load(); }, [load]);
  const changeLocal = (itemId, field, value) => setOrder((current) => ({ ...current, items: current.items.map((item) => item.id === itemId ? { ...item, [field]: value } : item) }));
  const saveItem = async (item) => {
    try { await updateOrderItem(orderId, item.id, { quantity: item.quantity, unit_price: item.unit_price }); await load(); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  const removeItem = async (item) => {
    if (!window.confirm("این محصول از سفارش حذف شود؟")) return;
    try { await removeOrderItem(orderId, item.id); await load(); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  const searchProducts = async (event) => {
    event.preventDefault();
    if (!search.trim()) return setResults([]);
    try { setResults(await listProducts(search.trim())); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  const add = async (product) => {
    try { await addOrderItem(orderId, { product: product.id, quantity: "1", unit_price: product.default_price }); setResults([]); setSearch(""); await load(); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  const setStatus = async (status) => {
    if (isActing) return;
    setIsActing(true);
    try { await updateOrder(orderId, { status }); await load(); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setIsActing(false); }
  };
  const saveNotes = async () => {
    try { await updateOrder(orderId, { notes }); await load(); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  return (
    <OrderLayout title="جزئیات سفارش">
      {error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {!order ? <p className="py-12 text-center text-slate-600">در حال دریافت سفارش…</p> : <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section className="space-y-3">
          <div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><p className="text-sm text-slate-500">مشتری</p><h2 className="mt-1 text-xl font-bold">{order.customer_name}</h2><p className="mt-2 text-sm text-slate-500">وضعیت: {order.status_display}</p>{order.status === "confirmed" && (!order.active_invoice || order.invoice_needs_revision) && <button className="mt-4 min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white" onClick={() => navigate("/orders/" + order.id + "/invoice/new")} type="button">{order.active_invoice ? "صدور فاکتور اصلاحی" : "صدور فاکتور"}</button>}{order.active_invoice && !order.invoice_needs_revision && <button className="mt-4 min-h-12 w-full rounded-xl border border-teal-700 px-4 font-semibold text-teal-800" onClick={() => navigate("/invoices/" + order.active_invoice.id)} type="button">مشاهده فاکتور فعلی</button>}{order.active_invoice && order.invoice_needs_revision && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">سفارش پس از صدور فاکتور تغییر کرده و نیازمند فاکتور اصلاحی است.</p>}</div>
          {order.items.map((item) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={item.id}>
            <div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.product_name_snapshot}</h3><p className="text-sm text-slate-500">{item.brand_snapshot || "بدون برند"} · {item.unit_snapshot}</p></div><span className="font-semibold text-teal-800">{formatPrice(item.line_total)}</span></div>
            <div className="mt-3 grid grid-cols-2 gap-3"><label className="text-sm text-slate-600">مقدار<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0.001" step="0.001" type="number" value={item.quantity} onChange={(event) => changeLocal(item.id, "quantity", event.target.value)} /></label><label className="text-sm text-slate-600">قیمت واحد<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0" step="0.01" type="number" value={item.unit_price} onChange={(event) => changeLocal(item.id, "unit_price", event.target.value)} /></label></div>
            <div className="mt-3 grid grid-cols-2 gap-2"><button className="min-h-11 rounded-xl border border-teal-700 font-semibold text-teal-800" onClick={() => saveItem(item)} type="button">ذخیره تغییر</button><button className="min-h-11 rounded-xl border border-red-200 font-semibold text-red-700" onClick={() => removeItem(item)} type="button">حذف محصول</button></div>
          </article>)}
          {order.items.length === 0 && <div className="rounded-2xl bg-white py-10 text-center text-slate-500 ring-1 ring-slate-200">محصولی در سفارش نیست.</div>}
        </section>
        <aside className="space-y-4">
          <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200"><form className="flex gap-2" onSubmit={searchProducts}><input className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 px-3" placeholder="افزودن محصول" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="min-h-12 rounded-xl bg-teal-700 px-3 font-semibold text-white" type="submit">جستجو</button></form>{results.map((product) => <button className="mt-2 min-h-12 w-full rounded-xl border border-slate-200 px-3 text-right" key={product.id} onClick={() => add(product)} type="button">{product.name} · {formatPrice(product.default_price)}</button>)}</div>
          <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200"><label className="text-sm text-slate-600">یادداشت سفارش<textarea className="mt-2 min-h-24 w-full rounded-xl border border-slate-300 p-3" value={notes} onChange={(event) => setNotes(event.target.value)} /></label><button className="mt-2 min-h-11 w-full rounded-xl border border-teal-700 font-semibold text-teal-800" onClick={saveNotes} type="button">ذخیره یادداشت</button></div>
          <div className="sticky bottom-20 rounded-2xl bg-white p-4 shadow-lg ring-1 ring-slate-200 sm:bottom-3"><div className="mb-4 flex justify-between text-lg font-bold"><span>جمع سفارش</span><span>{formatPrice(order.total_amount)}</span></div><div className="grid grid-cols-2 gap-2"><button className="min-h-12 rounded-xl border border-slate-300 font-semibold disabled:opacity-60" disabled={isActing} onClick={() => setStatus("draft")} type="button">پیش‌نویس</button><button className="min-h-12 rounded-xl bg-teal-700 font-semibold text-white disabled:opacity-60" disabled={isActing} onClick={() => setStatus("confirmed")} type="button">{isActing ? "در حال ثبت…" : "تأیید سفارش"}</button></div></div>
        </aside>
      </div>}
    </OrderLayout>
  );
}
