import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { listInventory } from "../services/inventory";

const quantity = (value) => new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 3 }).format(Number(value));

export default function InventoryListPage() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const load = (value = "") => listInventory(value).then(setItems).catch((requestError) => setError(getErrorMessage(requestError)));
  useEffect(() => { load(); }, []);
  const submit = (event) => { event.preventDefault(); load(search.trim()); };
  return <OrderLayout title="موجودی" backPath="/"><form className="mb-5 flex gap-2" onSubmit={submit}><input className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 px-4" placeholder="جستجوی نام یا برند محصول" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="min-h-12 rounded-xl bg-teal-700 px-5 font-semibold text-white" type="submit">جستجو</button></form>{error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{items.map((item) => { const negative = Number(item.current_stock) < 0; return <button className="min-h-36 rounded-2xl bg-white p-5 text-right ring-1 ring-slate-200" key={item.id} onClick={() => navigate("/inventory/" + item.id)} type="button"><h2 className="text-lg font-bold">{item.name}</h2><p className="mt-1 text-sm text-slate-500">{item.brand || "بدون برند"}</p><p className={"mt-5 text-xl font-bold " + (negative ? "text-red-700" : "text-teal-800")}>{quantity(item.current_stock)} {item.unit_display}</p>{negative && <span className="mt-2 block text-sm text-red-600">موجودی منفی</span>}</button>; })}</div>{items.length === 0 && !error && <div className="rounded-2xl bg-white py-12 text-center text-slate-500 ring-1 ring-slate-200">محصولی یافت نشد.</div>}</OrderLayout>;
}
