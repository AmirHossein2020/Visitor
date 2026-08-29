import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { formatPrice } from "../services/products";
import { listPurchases } from "../services/purchases";

export default function PurchaseListPage() {
  const [purchases, setPurchases] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => { listPurchases().then(setPurchases).catch((requestError) => setError(getErrorMessage(requestError))).finally(() => setIsLoading(false)); }, []);
  return <OrderLayout title="خریدها" backPath="/">
    {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {isLoading ? <p className="py-12 text-center text-slate-600">در حال دریافت خریدها…</p> : purchases.length === 0 ? <div className="rounded-2xl bg-white py-12 text-center text-slate-600 ring-1 ring-slate-200">خریدی ثبت نشده است.</div> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{purchases.map((purchase) => <button className="min-h-32 rounded-2xl bg-white p-5 text-right shadow-sm ring-1 ring-slate-200 hover:ring-teal-300" key={purchase.id} onClick={() => navigate("/purchases/" + purchase.id)} type="button"><span className="block text-lg font-bold">{purchase.customer_name}</span><span className="mt-2 block text-sm text-slate-500">{new Intl.DateTimeFormat("fa-IR").format(new Date(purchase.purchase_date + "T00:00:00"))} · {purchase.status_display}</span><span className="mt-4 block font-semibold text-teal-800">{formatPrice(purchase.total_amount)} تومان</span></button>)}</div>}
  </OrderLayout>;
}
