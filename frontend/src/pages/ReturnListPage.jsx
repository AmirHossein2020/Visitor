import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { formatPrice } from "../services/products";
import { listReturns } from "../services/returns";

export default function ReturnListPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => { listReturns().then(setItems).catch((requestError) => setError(getErrorMessage(requestError))); }, []);
  return <OrderLayout title="مرجوعی‌ها" backPath="/">{error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{items.length === 0 ? <div className="rounded-2xl bg-white py-12 text-center text-slate-500 ring-1 ring-slate-200">مرجوعی ثبت نشده است.</div> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{items.map((item) => <button className="min-h-36 rounded-2xl bg-white p-5 text-right ring-1 ring-slate-200" key={item.id} onClick={() => navigate("/returns/" + item.id)} type="button"><span className="font-mono text-sm text-teal-700" dir="ltr">{item.invoice_number}</span><h2 className="mt-2 text-lg font-bold">{item.customer_name}</h2><p className="mt-2 text-sm text-slate-500">{new Intl.DateTimeFormat("fa-IR").format(new Date(item.created_at))} · {item.status_display}</p><p className="mt-3 font-semibold text-teal-800">{formatPrice(item.total_amount)}</p></button>)}</div>}</OrderLayout>;
}
