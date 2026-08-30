import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { formatPrice } from "../services/products";
import { cancelReturn, getReturn } from "../services/returns";

export default function ReturnDetailPage({ returnId }) {
  const [item, setItem] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getReturn(returnId).then(setItem).catch((requestError) => setError(getErrorMessage(requestError))); }, [returnId]);
  const cancel = async () => { if (!window.confirm("این مرجوعی لغو شود؟")) return; try { await cancelReturn(returnId); setItem(await getReturn(returnId)); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  return <OrderLayout title="جزئیات مرجوعی" backPath="/returns">{error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{item && <div className="mx-auto max-w-4xl space-y-4"><section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><button className="font-mono text-sm text-teal-700" dir="ltr" onClick={() => navigate("/invoices/" + item.invoice)} type="button">{item.invoice_number}</button><h2 className="mt-2 text-xl font-bold">{item.customer_name}</h2><p className="mt-2 text-sm text-slate-500">وضعیت: {item.status_display}</p></section>{item.items.map((row) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={row.id}><div className="flex justify-between"><div><h3 className="font-bold">{row.product_name_snapshot}</h3><p className="text-sm text-slate-500">{row.brand_snapshot || "بدون برند"} · {row.unit_snapshot}</p></div><span className="font-semibold text-teal-800">{formatPrice(row.line_total)}</span></div><p className="mt-3 text-sm text-slate-600">مقدار: {row.quantity} · قیمت واحد: {formatPrice(row.unit_price)}</p></article>)}<section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><div className="flex justify-between text-lg font-bold"><span>جمع مرجوعی</span><span>{formatPrice(item.total_amount)}</span></div>{item.notes && <p className="mt-4 whitespace-pre-wrap text-sm text-slate-600">{item.notes}</p>}</section>{item.status !== "cancelled" && <button className="min-h-12 w-full rounded-xl border border-red-200 font-semibold text-red-700" onClick={cancel} type="button">لغو مرجوعی</button>}</div>}</OrderLayout>;
}
