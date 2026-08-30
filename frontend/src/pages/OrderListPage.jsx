import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { listOrders } from "../services/orders";
import { formatPrice } from "../services/products";

export default function OrderListPage() {
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    listOrders().then(setOrders).catch((requestError) => setError(getErrorMessage(requestError))).finally(() => setIsLoading(false));
  }, []);
  return (
    <OrderLayout title="سفارش‌ها" backPath="/">
      {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {isLoading ? <p className="py-12 text-center text-slate-600">در حال دریافت سفارش‌ها…</p> : orders.length === 0 ? <div className="rounded-2xl bg-white py-12 text-center text-slate-600 ring-1 ring-slate-200">سفارشی ثبت نشده است.</div> : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {orders.map((order) => <button className="min-h-32 rounded-2xl bg-white p-5 text-right shadow-sm ring-1 ring-slate-200 hover:ring-teal-300" key={order.id} onClick={() => navigate("/orders/" + order.id)} type="button">
            <span className="block text-lg font-bold text-slate-900">{order.customer_name}</span>
            <span className="mt-2 block text-sm text-slate-500">{new Intl.DateTimeFormat("fa-IR").format(new Date(order.created_at))} · {order.status_display}</span>
            <span className="mt-4 block font-semibold text-teal-800">{formatPrice(order.total_amount)}</span>
          </button>)}
        </div>
      )}
    </OrderLayout>
  );
}
