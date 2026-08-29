import { useCallback, useEffect, useState } from "react";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { formatPrice, listProducts } from "../services/products";
import { addPurchaseItem, getPurchase, removePurchaseItem, updatePurchase, updatePurchaseItem } from "../services/purchases";

export default function PurchaseDetailPage({ purchaseId }) {
  const [purchase, setPurchase] = useState(null);
  const [search, setSearch] = useState("");
  const [results, setResults] = useState([]);
  const [newPrices, setNewPrices] = useState({});
  const [error, setError] = useState("");
  const load = useCallback(() => getPurchase(purchaseId).then(setPurchase).catch((requestError) => setError(getErrorMessage(requestError))), [purchaseId]);
  useEffect(() => { load(); }, [load]);
  const changeLocal = (itemId, field, value) => setPurchase((current) => ({ ...current, items: current.items.map((item) => item.id === itemId ? { ...item, [field]: value } : item) }));
  const saveItem = async (item) => { try { await updatePurchaseItem(purchaseId, item.id, { quantity: item.quantity, unit_price: item.unit_price }); await load(); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  const removeItem = async (item) => { if (!window.confirm("این محصول از خرید حذف شود؟")) return; try { await removePurchaseItem(purchaseId, item.id); await load(); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  const searchProducts = async (event) => { event.preventDefault(); if (!search.trim()) return setResults([]); try { setResults(await listProducts(search.trim())); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  const add = async (product) => { const price = newPrices[product.id]; if (price === undefined || price === "" || Number(price) < 0) return setError("قیمت خرید را وارد کنید."); try { await addPurchaseItem(purchaseId, { product: product.id, quantity: "1", unit_price: price }); setResults([]); setSearch(""); setNewPrices({}); await load(); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  const setStatus = async (status) => { try { await updatePurchase(purchaseId, { status }); await load(); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  return <OrderLayout title="جزئیات خرید">
    {error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {!purchase ? <p className="py-12 text-center text-slate-600">در حال دریافت خرید…</p> : <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
      <section className="space-y-3"><div className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><p className="text-sm text-slate-500">مشتری یا تأمین‌کننده</p><h2 className="mt-1 text-xl font-bold">{purchase.customer_name}</h2><p className="mt-2 text-sm text-slate-500">تاریخ خرید: {new Intl.DateTimeFormat("fa-IR").format(new Date(purchase.purchase_date + "T00:00:00"))} · {purchase.status_display}</p></div>
        {purchase.items.map((item) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={item.id}><div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.product_name_snapshot}</h3><p className="text-sm text-slate-500">{item.brand_snapshot || "بدون برند"} · {item.unit_snapshot}</p></div><span className="font-semibold text-teal-800">{formatPrice(item.line_total)} تومان</span></div><div className="mt-3 grid grid-cols-2 gap-3"><label className="text-sm text-slate-600">مقدار<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0.001" step="0.001" type="number" value={item.quantity} onChange={(event) => changeLocal(item.id, "quantity", event.target.value)} /></label><label className="text-sm text-slate-600">قیمت خرید<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0" step="0.01" type="number" value={item.unit_price} onChange={(event) => changeLocal(item.id, "unit_price", event.target.value)} /></label></div><div className="mt-3 grid grid-cols-2 gap-2"><button className="min-h-11 rounded-xl border border-teal-700 font-semibold text-teal-800" onClick={() => saveItem(item)} type="button">ذخیره تغییر</button><button className="min-h-11 rounded-xl border border-red-200 font-semibold text-red-700" onClick={() => removeItem(item)} type="button">حذف محصول</button></div></article>)}
      </section>
      <aside className="space-y-4"><div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200"><form className="flex gap-2" onSubmit={searchProducts}><input className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 px-3" placeholder="افزودن محصول" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="min-h-12 rounded-xl bg-teal-700 px-3 font-semibold text-white" type="submit">جستجو</button></form>{results.map((product) => <div className="mt-2 rounded-xl border border-slate-200 p-3" key={product.id}><p className="font-semibold">{product.name} · {product.unit_display}</p><div className="mt-2 flex gap-2"><input aria-label="قیمت خرید" className="min-h-11 min-w-0 flex-1 rounded-xl border border-slate-300 px-3" min="0" placeholder="قیمت خرید" step="0.01" type="number" value={newPrices[product.id] || ""} onChange={(event) => setNewPrices((values) => ({ ...values, [product.id]: event.target.value }))} /><button className="min-h-11 rounded-xl bg-teal-700 px-3 font-semibold text-white" onClick={() => add(product)} type="button">افزودن</button></div></div>)}</div>
        {purchase.notes && <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200"><p className="text-sm text-slate-500">یادداشت</p><p className="mt-2 whitespace-pre-wrap">{purchase.notes}</p></div>}
        <div className="sticky bottom-3 rounded-2xl bg-white p-4 shadow-lg ring-1 ring-slate-200"><div className="mb-4 flex justify-between text-lg font-bold"><span>جمع خرید</span><span>{formatPrice(purchase.total_amount)} تومان</span></div><div className="grid grid-cols-2 gap-2"><button className="min-h-11 rounded-xl border border-slate-300 font-semibold" onClick={() => setStatus("draft")} type="button">پیش‌نویس</button><button className="min-h-11 rounded-xl bg-teal-700 font-semibold text-white" onClick={() => setStatus("confirmed")} type="button">تأیید خرید</button></div></div>
      </aside>
    </div>}
  </OrderLayout>;
}
