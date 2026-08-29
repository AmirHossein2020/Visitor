import { useEffect, useState } from "react";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { getInventoryProduct } from "../services/inventory";

const quantity = (value) => new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 3, signDisplay: "exceptZero" }).format(Number(value));

export default function InventoryDetailPage({ productId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getInventoryProduct(productId).then(setData).catch((requestError) => setError(getErrorMessage(requestError))); }, [productId]);
  return <OrderLayout title="جزئیات موجودی" backPath="/inventory">{error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{data && <div className="mx-auto max-w-4xl space-y-4"><section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><h2 className="text-xl font-bold">{data.product.name}</h2><p className="mt-1 text-sm text-slate-500">{data.product.brand || "بدون برند"}</p><p className={"mt-5 text-3xl font-bold " + (Number(data.product.current_stock) < 0 ? "text-red-700" : "text-teal-800")}>{quantity(data.product.current_stock)} {data.product.unit_display}</p>{Number(data.product.current_stock) < 0 && <p className="mt-2 text-sm text-red-600">موجودی این محصول منفی است.</p>}</section><section className="space-y-3"><h3 className="font-bold">گردش‌های اخیر موجودی</h3>{data.movements.map((movement) => <article className="flex items-center justify-between rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={movement.id}><div><p className="font-semibold">{movement.movement_type_display}</p><p className="mt-1 text-sm text-slate-500">{movement.notes || "بدون توضیح"} · {new Intl.DateTimeFormat("fa-IR").format(new Date(movement.created_at))}</p></div><span className={"text-lg font-bold " + (Number(movement.quantity) < 0 ? "text-red-700" : "text-teal-800")}>{quantity(movement.quantity)} {data.product.unit_display}</span></article>)}{data.movements.length === 0 && <div className="rounded-2xl bg-white py-10 text-center text-slate-500 ring-1 ring-slate-200">گردش موجودی ثبت نشده است.</div>}</section></div>}</OrderLayout>;
}
