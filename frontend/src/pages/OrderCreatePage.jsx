import { useEffect, useMemo, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { getCustomer } from "../services/customers";
import { addOrderItem, createOrder } from "../services/orders";
import { formatPrice, listProducts } from "../services/products";

export default function OrderCreatePage({ customerId }) {
  const [customer, setCustomer] = useState(null);
  const [items, setItems] = useState([]);
  const [notes, setNotes] = useState("");
  const [search, setSearch] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  useEffect(() => { getCustomer(customerId).then(setCustomer).catch((requestError) => setError(getErrorMessage(requestError))); }, [customerId]);

  const total = useMemo(() => items.reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0), [items]);
  const updateItem = (id, field, value) => setItems((current) => current.map((item) => item.product.id === id ? { ...item, [field]: value } : item));
  const addProduct = (product) => {
    setItems((current) => {
      const existing = current.find((item) => item.product.id === product.id);
      if (existing) return current.map((item) => item.product.id === product.id ? { ...item, quantity: String(Number(item.quantity) + 1) } : item);
      return [...current, { product, quantity: "1", unit_price: product.default_price }];
    });
  };
  const searchProducts = async (event) => {
    event.preventDefault(); setError("");
    if (!search.trim()) return setResults([]);
    try { setResults(await listProducts(search.trim())); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  const save = async (status) => {
    setError("");
    if (!items.length) return setError("حداقل یک محصول به سفارش اضافه کنید.");
    if (items.some((item) => Number(item.quantity) <= 0 || Number(item.unit_price) < 0)) return setError("مقدار و قیمت محصولات را بررسی کنید.");
    setIsSaving(true);
    try {
      const order = await createOrder({ customer: customerId, notes, status });
      for (const item of items) await addOrderItem(order.id, { product: item.product.id, quantity: item.quantity, unit_price: item.unit_price });
      navigate("/orders/" + order.id, { replace: true });
    } catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setIsSaving(false); }
  };
  return (
    <OrderLayout title="ثبت سفارش" backPath={"/customers/" + customerId}>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.7fr)]">
        <section>
          <div className="mb-4 rounded-2xl bg-white p-4 ring-1 ring-slate-200"><p className="text-sm text-slate-500">مشتری</p><h2 className="mt-1 text-xl font-bold">{customer?.name || "در حال دریافت…"}</h2></div>
          <form className="flex gap-2" onSubmit={searchProducts}><input className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" placeholder="جستجوی نام یا برند محصول" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="min-h-12 rounded-xl bg-teal-700 px-5 font-semibold text-white" type="submit">جستجو</button></form>
          {results.length > 0 && <div className="mt-3 grid gap-2 sm:grid-cols-2">{results.map((product) => <button className="min-h-16 rounded-xl bg-white px-4 text-right ring-1 ring-slate-200 hover:ring-teal-400" key={product.id} onClick={() => addProduct(product)} type="button"><span className="block font-semibold">{product.name}</span><span className="text-sm text-slate-500">{product.brand || "بدون برند"} · {formatPrice(product.default_price)}</span></button>)}</div>}
        </section>
        <section className="space-y-3">
          {items.length === 0 ? <div className="rounded-2xl bg-white py-10 text-center text-slate-500 ring-1 ring-slate-200">هنوز محصولی اضافه نشده است.</div> : items.map((item) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={item.product.id}>
            <div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.product.name}</h3><p className="text-sm text-slate-500">{item.product.unit_display}</p></div><button className="min-h-11 px-2 text-sm font-semibold text-red-700" onClick={() => setItems((current) => current.filter((entry) => entry.product.id !== item.product.id))} type="button">حذف</button></div>
            <div className="mt-3 grid grid-cols-2 gap-3"><label className="text-sm text-slate-600">مقدار<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0.001" step="0.001" type="number" value={item.quantity} onChange={(event) => updateItem(item.product.id, "quantity", event.target.value)} /></label><label className="text-sm text-slate-600">قیمت واحد<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0" step="0.01" type="number" value={item.unit_price} onChange={(event) => updateItem(item.product.id, "unit_price", event.target.value)} /></label></div>
            <p className="mt-3 text-left font-semibold text-teal-800">{formatPrice(Number(item.quantity || 0) * Number(item.unit_price || 0))}</p>
          </article>)}
          <label className="block rounded-2xl bg-white p-4 ring-1 ring-slate-200"><span className="text-sm text-slate-600">یادداشت (اختیاری)</span><textarea className="mt-2 min-h-20 w-full rounded-xl border border-slate-300 p-3" value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
          {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <div className="sticky bottom-3 rounded-2xl bg-white p-4 shadow-lg ring-1 ring-slate-200"><div className="mb-3 flex justify-between text-lg font-bold"><span>جمع سفارش</span><span>{formatPrice(total)}</span></div><div className="grid grid-cols-2 gap-2"><button className="min-h-12 rounded-xl border border-teal-700 font-semibold text-teal-800 disabled:opacity-60" disabled={isSaving} onClick={() => save("draft")} type="button">ذخیره پیش‌نویس</button><button className="min-h-12 rounded-xl bg-teal-700 font-semibold text-white disabled:opacity-60" disabled={isSaving} onClick={() => save("confirmed")} type="button">{isSaving ? "در حال ذخیره…" : "تأیید سفارش"}</button></div></div>
        </section>
      </div>
    </OrderLayout>
  );
}
