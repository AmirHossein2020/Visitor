import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import { formatPrice } from "../services/products";
import { createSubscriptionOrder, listPlans } from "../services/subscriptions";
import { getErrorMessage } from "../services/api";

export default function PricingPage() {
  const { user } = useAuth(); const [plans,setPlans]=useState([]); const [message,setMessage]=useState(""); const [loading,setLoading]=useState(true);
  const load=()=>{setLoading(true);setMessage("");listPlans().then(setPlans).catch(e=>setMessage(getErrorMessage(e))).finally(()=>setLoading(false))};
  useEffect(load,[]);
  const select=async(id)=>{if(!user)return navigate("/register");try{const order=await createSubscriptionOrder(id);navigate(`/account/subscription/orders/${order.id}/payment`);}catch(e){setMessage(e.data?.detail||"ثبت درخواست ممکن نشد.")}};
  return <main className="min-h-dvh bg-slate-50 p-4 sm:p-8"><div className="mx-auto max-w-5xl"><button className="min-h-11 font-bold text-emerald-800" onClick={()=>navigate("/")}>بازگشت به خانه</button><header className="py-10 text-center"><h1 className="text-4xl font-black">تعرفه‌های اشتراک</h1><p className="mt-3 text-slate-600">قیمت‌ها از سامانه دریافت می‌شوند و همه مبالغ به ریال هستند.</p></header>{message&&<p className="mb-5 rounded-2xl bg-emerald-50 p-4 text-center font-bold text-emerald-800">{message}</p>}{loading&&<p className="rounded-2xl bg-white p-6 text-center text-slate-500">در حال دریافت تعرفه‌ها…</p>}{!loading&&message&&plans.length===0&&<button className="mx-auto mb-5 block min-h-12 rounded-xl border border-slate-300 bg-white px-6 font-bold" onClick={load}>تلاش مجدد</button>}<div className="grid gap-5 md:grid-cols-2">{plans.map(p=><article className={`rounded-3xl bg-white p-7 ring-1 ${p.is_featured?"ring-2 ring-emerald-600":"ring-slate-200"}`} key={p.id}><h2 className="text-2xl font-black">{p.name}</h2><p className="mt-2 min-h-12 text-slate-600">{p.description}</p><p className="mt-7 text-3xl font-black text-emerald-800">{formatPrice(p.price)}</p><p className="mt-2 text-sm text-slate-500">اعتبار {p.duration_days} روزه</p><button className="mt-7 min-h-13 w-full rounded-xl bg-emerald-800 font-bold text-white" onClick={()=>select(p.id)}>درخواست خرید اشتراک</button></article>)}</div>{user&&<button className="mx-auto mt-8 block min-h-12 font-bold text-emerald-800" onClick={()=>navigate("/account/subscription")}>مشاهده وضعیت اشتراک من</button>}</div></main>;
}
