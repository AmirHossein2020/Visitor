import { useEffect, useMemo, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { getInvoice } from "../services/invoices";
import { addReturnItem, createReturn, updateReturn } from "../services/returns";
import { formatPrice } from "../services/products";

export default function ReturnCreatePage({ invoiceId }) {
  const [invoice, setInvoice] = useState(null);
  const [quantities, setQuantities] = useState({});
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { getInvoice(invoiceId).then(setInvoice).catch((requestError) => setError(getErrorMessage(requestError))); }, [invoiceId]);
  const selected = useMemo(() => invoice?.items.filter((item) => Number(quantities[item.id] || 0) > 0) || [], [invoice, quantities]);
  const total = selected.reduce((sum, item) => sum + Number(quantities[item.id]) * Number(item.unit_price), 0);
  const submit = async () => {
    setError("");
    if (!selected.length) return setError("حداقل یک محصول و مقدار مرجوعی را وارد کنید.");
    for (const item of selected) if (Number(quantities[item.id]) > Number(item.remaining_returnable_quantity)) return setError("مقدار مرجوعی بیشتر از مقدار باقی‌مانده است.");
    setSaving(true);
    try {
      const salesReturn = await createReturn({ invoice: invoiceId, notes });
      for (const item of selected) await addReturnItem(salesReturn.id, { invoice_item: item.id, quantity: quantities[item.id] });
      await updateReturn(salesReturn.id, { status: "confirmed" });
      navigate("/returns/" + salesReturn.id, { replace: true });
    } catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setSaving(false); }
  };
  return <OrderLayout title="ثبت مرجوعی" backPath={"/invoices/" + invoiceId}>
    {error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {!invoice ? <p className="py-12 text-center text-slate-600">در حال دریافت فاکتور…</p> : <div className="mx-auto max-w-4xl space-y-4">
      <section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><p className="text-sm text-slate-500">فاکتور {invoice.invoice_number}</p><h2 className="mt-1 text-xl font-bold">{invoice.buyer_name}</h2></section>
      {invoice.items.map((item) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={item.id}><div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.product_name}</h3><p className="text-sm text-slate-500">{item.brand || "بدون برند"} · {item.unit}</p></div><span className="font-semibold text-teal-800">{formatPrice(item.unit_price)}</span></div><div className="mt-3 grid grid-cols-3 gap-2 text-sm text-slate-600"><span>فروخته‌شده: {item.quantity}</span><span>مرجوع‌شده: {item.returned_quantity}</span><span>باقی‌مانده: {item.remaining_returnable_quantity}</span></div><label className="mt-3 block text-sm">مقدار مرجوعی<input className="mt-1 min-h-12 w-full rounded-xl border border-slate-300 px-3" min="0" max={item.remaining_returnable_quantity} step="0.001" type="number" value={quantities[item.id] || ""} onChange={(event) => setQuantities({ ...quantities, [item.id]: event.target.value })} /></label></article>)}
      <label className="block rounded-2xl bg-white p-4 text-sm ring-1 ring-slate-200">یادداشت (اختیاری)<textarea className="mt-2 min-h-24 w-full rounded-xl border border-slate-300 p-3" value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
      <div className="sticky bottom-3 rounded-2xl bg-white p-4 shadow-lg ring-1 ring-slate-200"><div className="mb-3 flex justify-between text-lg font-bold"><span>جمع مرجوعی</span><span>{formatPrice(total)}</span></div><button className="min-h-12 w-full rounded-xl bg-teal-700 font-semibold text-white disabled:opacity-60" disabled={saving} onClick={submit} type="button">{saving ? "در حال ثبت…" : "تأیید مرجوعی"}</button></div>
    </div>}
  </OrderLayout>;
}
